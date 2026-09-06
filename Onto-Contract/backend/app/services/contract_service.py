from __future__ import annotations

from datetime import datetime

from ..db import get_db, write_audit_log


STATUS_ACTIVE = "生效"
STATUS_INVOICED = "已开票"
STATUS_PARTIAL_INVOICED = "部分开票"
STATUS_NOT_INVOICED = "未开票"
STATUS_RECEIVED = "已收款"
STATUS_PARTIAL_RECEIVED = "部分收款"
STATUS_NOT_RECEIVED = "未收款"


def create_contract(payload: dict, actor: str | None = None):
    db = get_db()

    contract_no = (payload.get("contractNo") or "").strip()
    contract_name = (payload.get("contractName") or "").strip()
    payment_terms = payload.get("paymentTerms") or []

    if not contract_no or not contract_name:
        raise ValueError("合同编号和合同名称不能为空")
    if not payment_terms:
        raise ValueError("付款条款至少需要一条记录")

    ratio_sum = round(sum(float(item["ratio"]) for item in payment_terms), 4)
    if ratio_sum != 1.0:
        raise ValueError("付款比例合计必须等于 1")

    existing = db.execute("SELECT id FROM contracts WHERE contract_no = ?", (contract_no,)).fetchone()
    if existing:
        raise ValueError("合同编号已存在")

    cursor = db.execute(
        """
        INSERT INTO contracts (
            contract_no, contract_name, status, product_id, customer_id, dept_id, owner_id,
            sign_date, total_amount, purchase_amount, tax_rate,
            invoiced_amount_total, received_amount_total, invoice_status, receipt_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
        """,
        (
            contract_no,
            contract_name,
            STATUS_ACTIVE,
            int(payload["productId"]),
            int(payload["customerId"]),
            int(payload["deptId"]),
            int(payload["ownerId"]),
            payload["signDate"],
            float(payload["totalAmount"]),
            float(payload["purchaseAmount"]),
            float(payload["taxRate"]),
            STATUS_NOT_INVOICED,
            STATUS_NOT_RECEIVED,
        ),
    )
    contract_id = cursor.lastrowid

    seen_stage_no: set[str] = set()
    for term in payment_terms:
        stage_no = (term.get("stageNo") or "").strip()
        stage_name = (term.get("stageName") or "").strip()
        if not stage_no or not stage_name:
            raise ValueError("付款阶段编号和名称不能为空")
        if stage_no in seen_stage_no:
            raise ValueError("付款阶段编号不可重复")
        seen_stage_no.add(stage_no)
        db.execute(
            """
            INSERT INTO contract_payment_terms (contract_id, stage_no, stage_name, ratio)
            VALUES (?, ?, ?, ?)
            """,
            (contract_id, stage_no, stage_name, float(term["ratio"])),
        )

    db.commit()
    write_audit_log("BEHAVIOR_EXECUTE", "Contract_Create", actor, {"contractId": contract_id})
    return get_contract_detail(contract_id)


def create_invoice(payload: dict, actor: str | None = None):
    db = get_db()
    contract_id = int(payload["contractId"])
    contract = db.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    if not contract:
        raise ValueError("对应合同不存在")
    if contract["status"] != STATUS_ACTIVE:
        raise ValueError("只有生效合同才允许开票")

    amount = float(payload["amount"])
    if amount <= 0:
        raise ValueError("开票金额必须大于 0")

    remaining = float(contract["total_amount"]) - float(contract["invoiced_amount_total"])
    if amount > remaining:
        raise ValueError("开票金额超过合同剩余可开票金额")

    mappings = payload.get("stageMappings") or []
    if not mappings:
        raise ValueError("至少选择一个付款阶段")

    valid_stage_no = {
        row["stage_no"]
        for row in db.execute(
            "SELECT stage_no FROM contract_payment_terms WHERE contract_id = ?",
            (contract_id,),
        ).fetchall()
    }

    for mapping in mappings:
        if mapping["stageNo"] not in valid_stage_no:
            raise ValueError("开票阶段不属于当前合同付款条款")

    invoice_no = (payload.get("invoiceNo") or "").strip()
    if not invoice_no:
        raise ValueError("发票编号不能为空")
    existing = db.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,)).fetchone()
    if existing:
        raise ValueError("发票编号已存在")

    cursor = db.execute(
        """
        INSERT INTO invoices (
            invoice_no, contract_id, amount, tax_rate, invoice_date, status, is_received
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (invoice_no, contract_id, amount, float(payload["taxRate"]), payload["invoiceDate"], STATUS_INVOICED),
    )
    invoice_id = cursor.lastrowid

    for mapping in mappings:
        db.execute(
            """
            INSERT INTO invoice_term_mappings (invoice_id, stage_no, stage_name)
            VALUES (?, ?, ?)
            """,
            (invoice_id, mapping["stageNo"], mapping.get("stageName") or ""),
        )

    _update_contract_invoice_summary(contract_id, amount)
    db.commit()
    write_audit_log("BEHAVIOR_EXECUTE", "Invoice_Create", actor, {"invoiceId": invoice_id})
    return get_invoice_detail(invoice_id)


def receive_payment(invoice_id: int, received_date: str | None = None, actor: str | None = None):
    db = get_db()
    invoice = db.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not invoice:
        raise ValueError("发票记录不存在")
    if invoice["status"] != STATUS_INVOICED or int(invoice["is_received"]) == 1:
        raise ValueError("只有未收款的已开票记录才能确认收款")

    effective_received_date = received_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        """
        UPDATE invoices
        SET is_received = 1, status = ?, received_date = ?
        WHERE id = ?
        """,
        (STATUS_RECEIVED, effective_received_date, invoice_id),
    )
    _update_contract_receipt_summary(invoice["contract_id"], invoice["amount"])
    db.commit()
    write_audit_log("BEHAVIOR_EXECUTE", "Payment_Receive", actor, {"invoiceId": invoice_id})
    return get_invoice_detail(invoice_id)


def query_contracts(filters: dict | None = None):
    db = get_db()
    filters = filters or {}
    sql = """
    SELECT c.id,
           c.contract_no AS contractNo,
           c.contract_name AS contractName,
           c.status,
           c.sign_date AS signDate,
           c.total_amount AS totalAmount,
           c.purchase_amount AS purchaseAmount,
           c.tax_rate AS taxRate,
           c.invoiced_amount_total AS invoicedAmountTotal,
           c.received_amount_total AS receivedAmountTotal,
           c.invoice_status AS invoiceStatus,
           c.receipt_status AS receiptStatus,
           p.product_name AS productName,
           p.product_type AS productType,
           cu.customer_name AS customerName,
           d.dept_name AS deptName,
           e.employee_name AS ownerName
    FROM contracts c
    JOIN products p ON p.id = c.product_id
    JOIN customers cu ON cu.id = c.customer_id
    JOIN departments d ON d.id = c.dept_id
    JOIN employees e ON e.id = c.owner_id
    WHERE 1 = 1
    """
    params: list = []

    if filters.get("contractNo"):
        sql += " AND c.contract_no LIKE ?"
        params.append(f"%{str(filters['contractNo']).strip()}%")
    if filters.get("contractName"):
        sql += " AND c.contract_name LIKE ?"
        params.append(f"%{str(filters['contractName']).strip()}%")
    if filters.get("productType"):
        sql += " AND p.product_type LIKE ?"
        params.append(f"%{str(filters['productType']).strip()}%")
    if filters.get("deptId"):
        sql += " AND c.dept_id = ?"
        params.append(int(filters["deptId"]))
    if filters.get("signDateStart"):
        sql += " AND c.sign_date >= ?"
        params.append(filters["signDateStart"])
    if filters.get("signDateEnd"):
        sql += " AND c.sign_date <= ?"
        params.append(filters["signDateEnd"])

    sql += " ORDER BY c.sign_date DESC, c.id DESC"
    return db.execute(sql, params).fetchall()


def get_contract_detail(contract_id: int):
    db = get_db()
    contract = db.execute(
        """
        SELECT c.id,
               c.contract_no AS contractNo,
               c.contract_name AS contractName,
               c.status,
               c.sign_date AS signDate,
               c.total_amount AS totalAmount,
               c.purchase_amount AS purchaseAmount,
               c.tax_rate AS taxRate,
               c.invoiced_amount_total AS invoicedAmountTotal,
               c.received_amount_total AS receivedAmountTotal,
               c.invoice_status AS invoiceStatus,
               c.receipt_status AS receiptStatus,
               c.product_id AS productId,
               c.customer_id AS customerId,
               c.dept_id AS deptId,
               c.owner_id AS ownerId,
               p.product_no AS productNo,
               p.product_name AS productName,
               p.product_type AS productType,
               cu.customer_no AS customerNo,
               cu.customer_name AS customerName,
               cu.customer_type AS customerType,
               d.dept_no AS deptNo,
               d.dept_name AS deptName,
               e.employee_no AS ownerNo,
               e.employee_name AS ownerName
        FROM contracts c
        JOIN products p ON p.id = c.product_id
        JOIN customers cu ON cu.id = c.customer_id
        JOIN departments d ON d.id = c.dept_id
        JOIN employees e ON e.id = c.owner_id
        WHERE c.id = ?
        """,
        (contract_id,),
    ).fetchone()
    if not contract:
        return None

    payment_terms = db.execute(
        """
        SELECT stage_no AS stageNo, stage_name AS stageName, ratio
        FROM contract_payment_terms
        WHERE contract_id = ?
        ORDER BY id
        """,
        (contract_id,),
    ).fetchall()
    invoices = db.execute(
        """
        SELECT i.id,
               i.invoice_no AS invoiceNo,
               i.amount,
               i.tax_rate AS taxRate,
               i.invoice_date AS invoiceDate,
               i.status,
               i.is_received AS isReceived,
               i.received_date AS receivedDate
        FROM invoices i
        WHERE i.contract_id = ?
        ORDER BY i.invoice_date DESC, i.id DESC
        """,
        (contract_id,),
    ).fetchall()

    for invoice in invoices:
        invoice["stageMappings"] = db.execute(
            """
            SELECT stage_no AS stageNo, stage_name AS stageName
            FROM invoice_term_mappings
            WHERE invoice_id = ?
            ORDER BY id
            """,
            (invoice["id"],),
        ).fetchall()

    contract["paymentTerms"] = payment_terms
    contract["invoices"] = invoices
    return contract


def get_invoice_detail(invoice_id: int):
    db = get_db()
    invoice = db.execute(
        """
        SELECT i.id,
               i.invoice_no AS invoiceNo,
               i.contract_id AS contractId,
               c.contract_no AS contractNo,
               c.contract_name AS contractName,
               cu.customer_name AS customerName,
               i.amount,
               i.tax_rate AS taxRate,
               i.invoice_date AS invoiceDate,
               i.status,
               i.is_received AS isReceived,
               i.received_date AS receivedDate
        FROM invoices i
        JOIN contracts c ON c.id = i.contract_id
        JOIN customers cu ON cu.id = c.customer_id
        WHERE i.id = ?
        """,
        (invoice_id,),
    ).fetchone()
    if not invoice:
        return None
    invoice["stageMappings"] = get_invoice_stage_mappings(invoice_id)
    return invoice


def get_invoice_stage_mappings(invoice_id: int):
    db = get_db()
    return db.execute(
        """
        SELECT stage_no AS stageNo, stage_name AS stageName
        FROM invoice_term_mappings
        WHERE invoice_id = ?
        ORDER BY id
        """,
        (invoice_id,),
    ).fetchall()


def query_open_invoices(filters: dict | None = None):
    db = get_db()
    filters = filters or {}
    sql = """
    SELECT i.id,
           i.invoice_no AS invoiceNo,
           i.contract_id AS contractId,
           c.contract_no AS contractNo,
           c.contract_name AS contractName,
           cu.customer_name AS customerName,
           i.amount,
           i.tax_rate AS taxRate,
           i.invoice_date AS invoiceDate,
           i.status,
           i.is_received AS isReceived,
           i.received_date AS receivedDate
    FROM invoices i
    JOIN contracts c ON c.id = i.contract_id
    JOIN customers cu ON cu.id = c.customer_id
    WHERE i.status = ? AND i.is_received = 0
    """
    params: list = [STATUS_INVOICED]
    if filters.get("contractNo"):
        sql += " AND c.contract_no LIKE ?"
        params.append(f"%{str(filters['contractNo']).strip()}%")
    if filters.get("contractName"):
        sql += " AND c.contract_name LIKE ?"
        params.append(f"%{str(filters['contractName']).strip()}%")
    if filters.get("invoiceNo"):
        sql += " AND i.invoice_no LIKE ?"
        params.append(f"%{str(filters['invoiceNo']).strip()}%")
    if filters.get("customerName"):
        sql += " AND cu.customer_name LIKE ?"
        params.append(f"%{str(filters['customerName']).strip()}%")

    sql += " ORDER BY i.invoice_date DESC"
    return db.execute(sql, params).fetchall()


def _update_contract_invoice_summary(contract_id: int, amount: float):
    db = get_db()
    contract = db.execute(
        "SELECT total_amount, invoiced_amount_total FROM contracts WHERE id = ?",
        (contract_id,),
    ).fetchone()
    new_total = float(contract["invoiced_amount_total"]) + float(amount)
    status = STATUS_INVOICED if new_total >= float(contract["total_amount"]) else STATUS_PARTIAL_INVOICED
    db.execute(
        """
        UPDATE contracts
        SET invoiced_amount_total = ?, invoice_status = ?
        WHERE id = ?
        """,
        (new_total, status, contract_id),
    )


def _update_contract_receipt_summary(contract_id: int, amount: float):
    db = get_db()
    contract = db.execute(
        "SELECT total_amount, received_amount_total FROM contracts WHERE id = ?",
        (contract_id,),
    ).fetchone()
    new_total = float(contract["received_amount_total"]) + float(amount)
    status = STATUS_RECEIVED if new_total >= float(contract["total_amount"]) else STATUS_PARTIAL_RECEIVED
    db.execute(
        """
        UPDATE contracts
        SET received_amount_total = ?, receipt_status = ?
        WHERE id = ?
        """,
        (new_total, status, contract_id),
    )

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def dict_factory(cursor, row):
    return {column[0]: row[idx] for idx, column in enumerate(cursor.description)}


def get_db():
    if "db" not in g:
        settings = current_app.config["APP_SETTINGS"]
        db_path = Path(settings["database"]["sqlite_path"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            db_path,
            timeout=settings["database"]["timeout_seconds"],
            check_same_thread=False,
        )
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app_database(app):
    with app.app_context():
        db = get_db()
        _create_schema(db)
        _seed_reference_data(db)
        _seed_default_admin(db)
        db.commit()


def _create_schema(db):
    schema = """
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_no TEXT UNIQUE NOT NULL,
        dept_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_no TEXT UNIQUE NOT NULL,
        employee_name TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(id)
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_no TEXT UNIQUE NOT NULL,
        product_type TEXT NOT NULL,
        product_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_no TEXT UNIQUE NOT NULL,
        customer_type TEXT NOT NULL,
        customer_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_no TEXT UNIQUE NOT NULL,
        contract_name TEXT NOT NULL,
        status TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        dept_id INTEGER NOT NULL,
        owner_id INTEGER NOT NULL,
        sign_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        purchase_amount REAL NOT NULL,
        tax_rate REAL NOT NULL,
        invoiced_amount_total REAL NOT NULL DEFAULT 0,
        received_amount_total REAL NOT NULL DEFAULT 0,
        invoice_status TEXT NOT NULL DEFAULT '未开票',
        receipt_status TEXT NOT NULL DEFAULT '未收款',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (dept_id) REFERENCES departments(id),
        FOREIGN KEY (owner_id) REFERENCES employees(id)
    );

    CREATE TABLE IF NOT EXISTS contract_payment_terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id INTEGER NOT NULL,
        stage_no TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        ratio REAL NOT NULL,
        FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
        UNIQUE(contract_id, stage_no)
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        contract_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        tax_rate REAL NOT NULL,
        invoice_date TEXT NOT NULL,
        status TEXT NOT NULL,
        is_received INTEGER NOT NULL DEFAULT 0,
        received_date TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_id) REFERENCES contracts(id)
    );

    CREATE TABLE IF NOT EXISTS invoice_term_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        stage_no TEXT NOT NULL,
        stage_name TEXT,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        UNIQUE(invoice_id, stage_no)
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        message_type TEXT NOT NULL DEFAULT 'text',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        action_target TEXT NOT NULL,
        actor TEXT,
        detail_json TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    db.executescript(schema)


def _seed_reference_data(db):
    if db.execute("SELECT COUNT(*) AS count FROM departments").fetchone()["count"] > 0:
        return

    departments = [
        ("D001", "销售一部"),
        ("D002", "销售二部"),
        ("D003", "财务部"),
    ]
    db.executemany("INSERT INTO departments (dept_no, dept_name) VALUES (?, ?)", departments)

    dept_map = {row["dept_no"]: row["id"] for row in db.execute("SELECT id, dept_no FROM departments").fetchall()}

    employees = [
        ("E001", "张敏", dept_map["D001"]),
        ("E002", "李强", dept_map["D002"]),
        ("E003", "王玲", dept_map["D003"]),
    ]
    db.executemany(
        "INSERT INTO employees (employee_no, employee_name, dept_id) VALUES (?, ?, ?)",
        employees,
    )

    products = [
        ("P001", "软件平台", "合同智能分析平台"),
        ("P002", "集成服务", "合同集成交付服务"),
        ("P003", "运维服务", "合同运维支持服务"),
    ]
    db.executemany(
        "INSERT INTO products (product_no, product_type, product_name) VALUES (?, ?, ?)",
        products,
    )

    customers = [
        ("C001", "国企", "华东能源集团"),
        ("C002", "民营", "星河制造有限公司"),
        ("C003", "上市公司", "远景数字科技"),
    ]
    db.executemany(
        "INSERT INTO customers (customer_no, customer_type, customer_name) VALUES (?, ?, ?)",
        customers,
    )

    if db.execute("SELECT COUNT(*) AS count FROM contracts").fetchone()["count"] == 0:
        product_map = {row["product_no"]: row["id"] for row in db.execute("SELECT id, product_no FROM products").fetchall()}
        customer_map = {row["customer_no"]: row["id"] for row in db.execute("SELECT id, customer_no FROM customers").fetchall()}
        employee_map = {row["employee_no"]: row["id"] for row in db.execute("SELECT id, employee_no FROM employees").fetchall()}

        db.execute(
            """
            INSERT INTO contracts (
                contract_no, contract_name, status, product_id, customer_id,
                dept_id, owner_id, sign_date, total_amount, purchase_amount,
                tax_rate, invoiced_amount_total, received_amount_total,
                invoice_status, receipt_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "HT2026040001",
                "华东能源集团合同智能平台建设",
                "生效",
                product_map["P001"],
                customer_map["C001"],
                dept_map["D001"],
                employee_map["E001"],
                "2026-03-15",
                480000,
                160000,
                0.13,
                180000,
                80000,
                "部分开票",
                "部分收款",
            ),
        )
        contract_id = db.execute(
            "SELECT id FROM contracts WHERE contract_no = ?",
            ("HT2026040001",),
        ).fetchone()["id"]

        db.executemany(
            """
            INSERT INTO contract_payment_terms (contract_id, stage_no, stage_name, ratio)
            VALUES (?, ?, ?, ?)
            """,
            [
                (contract_id, "S1", "预付款", 0.3),
                (contract_id, "S2", "里程碑验收款", 0.4),
                (contract_id, "S3", "尾款", 0.3),
            ],
        )

        db.execute(
            """
            INSERT INTO invoices (
                invoice_no, contract_id, amount, tax_rate, invoice_date, status, is_received, received_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "FP2026040001",
                contract_id,
                180000,
                0.13,
                "2026-03-20 10:00:00",
                "已收款",
                1,
                "2026-03-28 15:30:00",
            ),
        )
        invoice_id = db.execute(
            "SELECT id FROM invoices WHERE invoice_no = ?",
            ("FP2026040001",),
        ).fetchone()["id"]
        db.executemany(
            """
            INSERT INTO invoice_term_mappings (invoice_id, stage_no, stage_name)
            VALUES (?, ?, ?)
            """,
            [(invoice_id, "S1", "预付款")],
        )


def _seed_default_admin(db):
    if db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"] > 0:
        return
    settings = current_app.config["APP_SETTINGS"]
    db.execute(
        """
        INSERT INTO users (username, password_hash, display_name, is_active)
        VALUES (?, ?, ?, 1)
        """,
        (
            settings["auth"]["default_admin_username"],
            generate_password_hash(settings["auth"]["default_admin_password"]),
            "系统管理员",
        ),
    )


def write_audit_log(action_type: str, action_target: str, actor: str | None, detail: dict | None):
    db = get_db()
    db.execute(
        """
        INSERT INTO audit_logs (action_type, action_target, actor, detail_json)
        VALUES (?, ?, ?, ?)
        """,
        (action_type, action_target, actor, json.dumps(detail or {}, ensure_ascii=False)),
    )
    db.commit()

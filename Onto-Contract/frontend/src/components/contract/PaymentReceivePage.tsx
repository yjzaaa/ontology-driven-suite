import React, { useEffect, useMemo, useState } from 'react';
import { BadgeDollarSign, Search } from 'lucide-react';
import { queryOpenInvoices, receivePayment } from '../../api/client';
import type { InvoiceRecord } from '../../types';

const PaymentReceivePage: React.FC = () => {
  const [filters, setFilters] = useState({
    contractNo: '',
    contractName: '',
    invoiceNo: '',
    customerName: '',
  });
  const [rows, setRows] = useState<InvoiceRecord[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceRecord | null>(null);
  const [receivedDate, setReceivedDate] = useState(new Date().toISOString().slice(0, 16));
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadRows = async (nextFilters = filters) => {
    setLoading(true);
    try {
      const result = await queryOpenInvoices(nextFilters);
      setRows(result);
      if (selectedInvoice) {
        const updated = result.find((item) => item.id === selectedInvoice.id) ?? null;
        setSelectedInvoice(updated);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRows();
  }, []);

  const selectedSummary = useMemo(() => {
    if (!selectedInvoice) {
      return null;
    }
    return [
      ['发票编号', selectedInvoice.invoiceNo],
      ['合同编号', selectedInvoice.contractNo ?? '-'],
      ['合同名称', selectedInvoice.contractName ?? '-'],
      ['客户名称', selectedInvoice.customerName ?? '-'],
      ['开票金额', Number(selectedInvoice.amount).toLocaleString()],
      ['开票日期', selectedInvoice.invoiceDate],
      ['当前状态', selectedInvoice.status],
    ];
  }, [selectedInvoice]);

  const handleConfirm = async () => {
    if (!selectedInvoice) {
      return;
    }
    setSubmitting(true);
    setErrorMessage('');
    setSuccessMessage('');
    try {
      const result = await receivePayment({ invoiceId: selectedInvoice.id, receivedDate });
      setSuccessMessage(`收款确认成功：${result.invoiceNo}`);
      await loadRows();
      setSelectedInvoice(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '收款确认失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-shell compact-shell">
      <div className="page-stack">
        <section className="panel panel-flat">
          <div className="section-bar">
            <h3>待收款发票检索</h3>
            <button type="button" className="mini-btn" onClick={() => void loadRows()}>
              <Search size={14} />
              查询
            </button>
          </div>
          <div className="form-grid adaptive-form">
            <label className="form-field">
              <span>合同编号</span>
              <input value={filters.contractNo} onChange={(event) => setFilters((prev) => ({ ...prev, contractNo: event.target.value }))} />
            </label>
            <label className="form-field">
              <span>合同名称</span>
              <input value={filters.contractName} onChange={(event) => setFilters((prev) => ({ ...prev, contractName: event.target.value }))} />
            </label>
            <label className="form-field">
              <span>发票编号</span>
              <input value={filters.invoiceNo} onChange={(event) => setFilters((prev) => ({ ...prev, invoiceNo: event.target.value }))} />
            </label>
            <label className="form-field">
              <span>客户名称</span>
              <input value={filters.customerName} onChange={(event) => setFilters((prev) => ({ ...prev, customerName: event.target.value }))} />
            </label>
          </div>
          <div className="action-row action-row--right action-row--spaced">
            <button type="button" className="btn btn-primary btn-compact" onClick={() => void loadRows()}>
              查询待收款发票
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-compact"
              onClick={() => {
                const clean = { contractNo: '', contractName: '', invoiceNo: '', customerName: '' };
                setFilters(clean);
                void loadRows(clean);
              }}
            >
              重置条件
            </button>
          </div>
        </section>

        <section className="panel panel-flat">
          <div className="section-bar">
            <h3>待收款发票列表</h3>
            <span>{loading ? '加载中...' : `共 ${rows.length} 条`}</span>
          </div>
          <div className="table-wrap flat-table">
            <table className="data-table selectable">
              <thead>
                <tr>
                  <th>发票编号</th>
                  <th>合同编号</th>
                  <th>合同名称</th>
                  <th>客户</th>
                  <th>金额</th>
                  <th>开票日期</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={row.id}
                    className={selectedInvoice?.id === row.id ? 'selected' : ''}
                    onClick={() => setSelectedInvoice(row)}
                  >
                    <td>{row.invoiceNo}</td>
                    <td>{row.contractNo}</td>
                    <td>{row.contractName}</td>
                    <td>{row.customerName}</td>
                    <td>{Number(row.amount).toLocaleString()}</td>
                    <td>{row.invoiceDate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel panel-flat">
          <div className="section-bar">
            <h3>收款确认</h3>
            <span>{selectedInvoice ? '已选择待收款发票' : '请先从上方列表选择一条发票'}</span>
          </div>
          {selectedSummary ? (
            <div className="detail-grid">
              {selectedSummary.map(([label, value]) => (
                <div className="detail-list__item" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-block">请选择待收款发票后，再确认收款。</div>
          )}

          <div className="form-grid adaptive-form">
            <label className="form-field form-field--wide">
              <span>收款日期</span>
              <input type="datetime-local" value={receivedDate} onChange={(event) => setReceivedDate(event.target.value)} />
            </label>
          </div>

          {errorMessage ? <div className="alert error">{errorMessage}</div> : null}
          {successMessage ? <div className="alert success">{successMessage}</div> : null}

          <div className="action-row action-row--right action-row--spaced">
            <button type="button" className="btn btn-primary btn-compact" onClick={() => void handleConfirm()} disabled={!selectedInvoice || submitting}>
              <BadgeDollarSign size={16} />
              {submitting ? '确认中...' : '确认收款'}
            </button>
            <button type="button" className="btn btn-secondary btn-compact" onClick={() => setSelectedInvoice(null)}>
              清空选择
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};

export default PaymentReceivePage;

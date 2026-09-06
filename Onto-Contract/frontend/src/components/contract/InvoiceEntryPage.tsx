import React, { useEffect, useMemo, useState } from 'react';
import { BadgeCheck, ListChecks } from 'lucide-react';
import { createInvoice, getContractDetail, queryContracts } from '../../api/client';
import type { ContractDetail, ContractSummary, InvoiceRecord } from '../../types';

interface InvoiceEntryPageProps {
  onOpenPage: (pageId: string) => void;
}

const InvoiceEntryPage: React.FC<InvoiceEntryPageProps> = ({ onOpenPage }) => {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [selectedContractId, setSelectedContractId] = useState('');
  const [contractDetail, setContractDetail] = useState<ContractDetail | null>(null);
  const [invoiceNo, setInvoiceNo] = useState('');
  const [amount, setAmount] = useState('');
  const [taxRate, setTaxRate] = useState('0.13');
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().slice(0, 16));
  const [selectedStages, setSelectedStages] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvoiceRecord | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const loadContracts = async () => {
      const rows = await queryContracts({});
      setContracts(rows);
    };
    void loadContracts();
  }, []);

  useEffect(() => {
    const loadDetail = async () => {
      if (!selectedContractId) {
        setContractDetail(null);
        setSelectedStages([]);
        return;
      }
      setLoading(true);
      try {
        const detail = await getContractDetail(Number(selectedContractId));
        setContractDetail(detail);
        setTaxRate(String(detail.taxRate));
        setSelectedStages(detail.paymentTerms.length > 0 ? [detail.paymentTerms[0].stageNo] : []);
      } finally {
        setLoading(false);
      }
    };
    void loadDetail();
  }, [selectedContractId]);

  const remainingInvoiceAmount = useMemo(() => {
    if (!contractDetail) {
      return 0;
    }
    return Number(contractDetail.totalAmount) - Number(contractDetail.invoicedAmountTotal);
  }, [contractDetail]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedContractId || !contractDetail) {
      return;
    }

    setSaving(true);
    setErrorMessage('');
    setResult(null);
    try {
      const invoice = await createInvoice({
        invoiceNo,
        contractId: Number(selectedContractId),
        amount: Number(amount),
        taxRate: Number(taxRate),
        invoiceDate,
        stageMappings: contractDetail.paymentTerms
          .filter((item) => selectedStages.includes(item.stageNo))
          .map((item) => ({ stageNo: item.stageNo, stageName: item.stageName })),
      });
      setResult(invoice);
      onOpenPage('PaymentReceivePage');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '开票录入失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell compact-shell">
      <form className="page-stack" onSubmit={handleSubmit}>
        <section className="panel panel-flat">
          <div className="section-bar">
            <h3>开票录入</h3>
            <span>{loading ? '合同上下文加载中...' : contractDetail ? '已带出合同上下文' : '请选择合同'}</span>
          </div>

          <div className="form-grid adaptive-form">
            <label className="form-field">
              <span>选择合同</span>
              <select value={selectedContractId} onChange={(event) => setSelectedContractId(event.target.value)} required>
                <option value="">请选择合同</option>
                {contracts.map((contract) => (
                  <option key={contract.id} value={String(contract.id)}>
                    {contract.contractNo} / {contract.contractName}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>发票编号</span>
              <input value={invoiceNo} onChange={(event) => setInvoiceNo(event.target.value)} required />
            </label>
            <label className="form-field">
              <span>开票金额</span>
              <input type="number" min="0" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required />
            </label>
            <label className="form-field">
              <span>税率</span>
              <input type="number" min="0" step="0.01" value={taxRate} onChange={(event) => setTaxRate(event.target.value)} required />
            </label>
            <label className="form-field form-field--wide">
              <span>开票日期</span>
              <input type="datetime-local" value={invoiceDate} onChange={(event) => setInvoiceDate(event.target.value)} required />
            </label>
          </div>

          {contractDetail ? (
            <div className="readonly-context">
              <div className="readonly-context__title">合同上下文</div>
              <div className="form-grid adaptive-form readonly-grid">
                <label className="form-field">
                  <span>合同编号</span>
                  <input value={contractDetail.contractNo} readOnly />
                </label>
                <label className="form-field">
                  <span>合同名称</span>
                  <input value={contractDetail.contractName} readOnly />
                </label>
                <label className="form-field">
                  <span>客户名称</span>
                  <input value={contractDetail.customerName} readOnly />
                </label>
                <label className="form-field">
                  <span>销售部门</span>
                  <input value={contractDetail.deptName} readOnly />
                </label>
                <label className="form-field">
                  <span>合同总金额</span>
                  <input value={Number(contractDetail.totalAmount).toLocaleString()} readOnly />
                </label>
                <label className="form-field">
                  <span>累计开票金额</span>
                  <input value={Number(contractDetail.invoicedAmountTotal).toLocaleString()} readOnly />
                </label>
                <label className="form-field">
                  <span>剩余可开票金额</span>
                  <input value={remainingInvoiceAmount.toLocaleString()} readOnly />
                </label>
                <label className="form-field">
                  <span>当前开票状态</span>
                  <input value={contractDetail.invoiceStatus} readOnly />
                </label>
              </div>
            </div>
          ) : (
            <div className="empty-block">选择合同后将自动带出不可编辑的合同上下文信息。</div>
          )}

          <div className="subsection-block">
            <div className="section-bar section-bar--compact">
              <h3>关联付款阶段</h3>
              <button
                type="button"
                className="mini-btn"
                onClick={() => setSelectedStages(contractDetail?.paymentTerms.map((item) => item.stageNo) ?? [])}
                disabled={!contractDetail}
              >
                <ListChecks size={14} />
                全选
              </button>
            </div>
            {contractDetail ? (
              <div className="stage-chip-group">
                {contractDetail.paymentTerms.map((term) => {
                  const checked = selectedStages.includes(term.stageNo);
                  return (
                    <label key={term.stageNo} className={`stage-chip ${checked ? 'checked' : ''}`}>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          setSelectedStages((prev) =>
                            event.target.checked ? [...prev, term.stageNo] : prev.filter((item) => item !== term.stageNo),
                          );
                        }}
                      />
                      <span>{term.stageNo}</span>
                      <strong>{term.stageName}</strong>
                      <em>{(Number(term.ratio) * 100).toFixed(0)}%</em>
                    </label>
                  );
                })}
              </div>
            ) : (
              <div className="empty-block">尚未选择合同。</div>
            )}
          </div>

          {errorMessage ? <div className="alert error">{errorMessage}</div> : null}
          {result ? <div className="alert success">已创建发票 {result.invoiceNo}，金额 {Number(result.amount).toLocaleString()}。</div> : null}

          <div className="action-row action-row--right">
            <button type="submit" className="btn btn-primary btn-compact" disabled={saving || !contractDetail}>
              {saving ? '提交中...' : '保存开票'}
            </button>
            <button type="button" className="btn btn-secondary btn-compact" onClick={() => onOpenPage('PaymentReceivePage')}>
              转到收款录入
            </button>
            {result ? (
              <div className="inline-success">
                <BadgeCheck size={16} />
                状态：{result.status}
              </div>
            ) : null}
          </div>
        </section>
      </form>
    </div>
  );
};

export default InvoiceEntryPage;

import React, { useMemo, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { createContract, queryContracts } from '../../api/client';
import type { ContractDetail, PaymentTerm, ReferenceData } from '../../types';

interface ContractEntryPageProps {
  referenceData: ReferenceData;
  onOpenPage: (pageId: string) => void;
}

interface ContractFormState {
  contractNo: string;
  contractName: string;
  productId: string;
  customerId: string;
  deptId: string;
  ownerId: string;
  signDate: string;
  totalAmount: string;
  purchaseAmount: string;
  taxRate: string;
}

const createEmptyTerm = (index: number): PaymentTerm => ({
  stageNo: `S${index + 1}`,
  stageName: '',
  ratio: 0,
});

const defaultFormState = (): ContractFormState => ({
  contractNo: '',
  contractName: '',
  productId: '',
  customerId: '',
  deptId: '',
  ownerId: '',
  signDate: new Date().toISOString().slice(0, 10),
  totalAmount: '',
  purchaseAmount: '',
  taxRate: '0.13',
});

const defaultTerms = (): PaymentTerm[] => [
  { stageNo: 'S1', stageName: '预付款', ratio: 0.3 },
  { stageNo: 'S2', stageName: '验收款', ratio: 0.4 },
  { stageNo: 'S3', stageName: '尾款', ratio: 0.3 },
];

const ContractEntryPage: React.FC<ContractEntryPageProps> = ({ referenceData, onOpenPage }) => {
  const [form, setForm] = useState<ContractFormState>(defaultFormState);
  const [paymentTerms, setPaymentTerms] = useState<PaymentTerm[]>(defaultTerms);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successDetail, setSuccessDetail] = useState<ContractDetail | null>(null);
  const [isGeneratingNo, setIsGeneratingNo] = useState(false);

  const ownerOptions = useMemo(() => {
    if (!form.deptId) {
      return referenceData.employees;
    }
    return referenceData.employees.filter((item) => String(item.deptId) === form.deptId);
  }, [form.deptId, referenceData.employees]);

  const ratioTotal = useMemo(() => paymentTerms.reduce((sum, item) => sum + Number(item.ratio || 0), 0), [paymentTerms]);

  React.useEffect(() => {
    let cancelled = false;

    const generateContractNo = async () => {
      const signDate = form.signDate || new Date().toISOString().slice(0, 10);
      const [year, month] = signDate.split('-');
      if (!year || !month) {
        return;
      }

      const prefix = `HT${year}${month}`;
      setIsGeneratingNo(true);
      try {
        const rows = await queryContracts({ contractNo: prefix });
        const serials = rows
          .map((item) => item.contractNo)
          .filter((contractNo) => contractNo.startsWith(prefix))
          .map((contractNo) => Number(contractNo.slice(-4)))
          .filter((value) => Number.isFinite(value));
        const nextSerial = `${(serials.length ? Math.max(...serials) : 0) + 1}`.padStart(4, '0');
        if (!cancelled) {
          setForm((prev) => ({ ...prev, contractNo: `${prefix}${nextSerial}` }));
        }
      } finally {
        if (!cancelled) {
          setIsGeneratingNo(false);
        }
      }
    };

    void generateContractNo();
    return () => {
      cancelled = true;
    };
  }, [form.signDate]);

  const handleFormChange = (field: keyof ContractFormState, value: string) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
      ...(field === 'deptId' ? { ownerId: '' } : {}),
    }));
  };

  const handleTermChange = (index: number, field: keyof PaymentTerm, value: string) => {
    setPaymentTerms((prev) =>
      prev.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: field === 'ratio' ? Number(value) : value,
            }
          : item,
      ),
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setErrorMessage('');
    setSuccessDetail(null);

    try {
      const detail = await createContract({
        ...form,
        productId: Number(form.productId),
        customerId: Number(form.customerId),
        deptId: Number(form.deptId),
        ownerId: Number(form.ownerId),
        totalAmount: Number(form.totalAmount),
        purchaseAmount: Number(form.purchaseAmount),
        taxRate: Number(form.taxRate),
        paymentTerms,
      });
      setSuccessDetail(detail);
      onOpenPage('ContractSearchPage');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '合同录入失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-shell compact-shell">
      <form className="page-stack" onSubmit={handleSubmit}>
        <section className="panel panel-flat">
          <div className="section-bar">
            <h3>合同主信息</h3>
          </div>
          <div className="form-grid adaptive-form">
            <label className="form-field">
              <span>合同编号</span>
              <input value={isGeneratingNo ? '生成中...' : form.contractNo} readOnly required />
            </label>
            <label className="form-field">
              <span>合同名称</span>
              <input value={form.contractName} onChange={(event) => handleFormChange('contractName', event.target.value)} required />
            </label>
            <label className="form-field">
              <span>产品</span>
              <select value={form.productId} onChange={(event) => handleFormChange('productId', event.target.value)} required>
                <option value="">请选择产品</option>
                {referenceData.products.map((item) => (
                  <option key={item.id} value={String(item.id)}>
                    {String(item.productName)}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>客户</span>
              <select value={form.customerId} onChange={(event) => handleFormChange('customerId', event.target.value)} required>
                <option value="">请选择客户</option>
                {referenceData.customers.map((item) => (
                  <option key={item.id} value={String(item.id)}>
                    {String(item.customerName)}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>销售部门</span>
              <select value={form.deptId} onChange={(event) => handleFormChange('deptId', event.target.value)} required>
                <option value="">请选择部门</option>
                {referenceData.departments.map((item) => (
                  <option key={item.id} value={String(item.id)}>
                    {String(item.deptName)}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>销售人员</span>
              <select value={form.ownerId} onChange={(event) => handleFormChange('ownerId', event.target.value)} required>
                <option value="">请选择人员</option>
                {ownerOptions.map((item) => (
                  <option key={item.id} value={String(item.id)}>
                    {String(item.employeeName)}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>签订日期</span>
              <input type="date" value={form.signDate} onChange={(event) => handleFormChange('signDate', event.target.value)} required />
            </label>
            <label className="form-field">
              <span>合同总金额</span>
              <input type="number" min="0" step="0.01" value={form.totalAmount} onChange={(event) => handleFormChange('totalAmount', event.target.value)} required />
            </label>
            <label className="form-field">
              <span>采购金额</span>
              <input type="number" min="0" step="0.01" value={form.purchaseAmount} onChange={(event) => handleFormChange('purchaseAmount', event.target.value)} required />
            </label>
            <label className="form-field">
              <span>税率</span>
              <select value={form.taxRate} onChange={(event) => handleFormChange('taxRate', event.target.value)} required>
                <option value="0.01">1%</option>
                <option value="0.03">3%</option>
                <option value="0.06">6%</option>
                <option value="0.13">13%</option>
              </select>
            </label>
          </div>
        </section>

        <section className="panel panel-flat">
          <div className="section-bar">
            <h3>付款条款明细</h3>
            <div className="inline-meta">
              <span>比例合计 {(ratioTotal * 100).toFixed(0)}%</span>
              <button type="button" className="mini-btn" onClick={() => setPaymentTerms((prev) => [...prev, createEmptyTerm(prev.length)])}>
                <Plus size={14} />
                新增行
              </button>
            </div>
          </div>
          <div className="table-wrap flat-table">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '120px' }}>阶段编号</th>
                  <th>阶段名称</th>
                  <th style={{ width: '140px' }}>比例</th>
                  <th style={{ width: '160px' }}>付款金额</th>
                  <th style={{ width: '80px' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {paymentTerms.map((term, index) => (
                  <tr key={`${term.stageNo}-${index}`}>
                    <td>
                      <input value={term.stageNo} onChange={(event) => handleTermChange(index, 'stageNo', event.target.value)} />
                    </td>
                    <td>
                      <input value={term.stageName} onChange={(event) => handleTermChange(index, 'stageName', event.target.value)} />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={term.ratio}
                        onChange={(event) => handleTermChange(index, 'ratio', event.target.value)}
                      />
                    </td>
                    <td>{((Number(form.totalAmount || 0) || 0) * Number(term.ratio || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td>
                      <button
                        type="button"
                        className="icon-btn danger"
                        onClick={() => setPaymentTerms((prev) => prev.filter((_, itemIndex) => itemIndex !== index))}
                        disabled={paymentTerms.length === 1}
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel panel-flat panel-actions">
          {errorMessage ? <div className="alert error">{errorMessage}</div> : null}
          {successDetail ? <div className="alert success">合同已创建：{successDetail.contractNo} / {successDetail.contractName}</div> : null}
          <div className="action-row action-row--right">
            <button type="submit" className="btn btn-primary btn-compact" disabled={saving || isGeneratingNo}>
              {saving ? '保存中...' : '保存合同'}
            </button>
            <button type="button" className="btn btn-secondary btn-compact" onClick={() => onOpenPage('ContractSearchPage')}>
              打开合同查询
            </button>
          </div>
        </section>
      </form>
    </div>
  );
};

export default ContractEntryPage;

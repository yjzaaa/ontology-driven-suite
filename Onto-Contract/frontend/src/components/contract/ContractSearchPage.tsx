import React, { useEffect, useState } from 'react';
import { Eye, Search } from 'lucide-react';
import { getContractDetail, queryContracts } from '../../api/client';
import type { ContractDetail, ContractSummary, ReferenceData } from '../../types';

interface ContractSearchPageProps {
  referenceData: ReferenceData;
}

const defaultFilters = {
  contractNo: '',
  contractName: '',
  productType: '',
  deptId: '',
  signDateStart: '',
  signDateEnd: '',
};

const ContractSearchPage: React.FC<ContractSearchPageProps> = ({ referenceData }) => {
  const [filters, setFilters] = useState(defaultFilters);
  const [rows, setRows] = useState<ContractSummary[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<ContractDetail | null>(null);
  const [loading, setLoading] = useState(false);

  const loadRows = async (nextFilters = filters) => {
    setLoading(true);
    try {
      const result = await queryContracts({
        ...nextFilters,
        deptId: nextFilters.deptId ? Number(nextFilters.deptId) : undefined,
      });
      setRows(result);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRows();
  }, []);

  const openDetail = async (contractId: number) => {
    const detail = await getContractDetail(contractId);
    setSelectedDetail(detail);
  };

  return (
    <div className="page-shell compact-shell">
      <section className="panel panel-flat">
        <div className="section-bar">
          <h3>查询条件</h3>
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
            <span>产品类型</span>
            <input value={filters.productType} onChange={(event) => setFilters((prev) => ({ ...prev, productType: event.target.value }))} />
          </label>
          <label className="form-field">
            <span>销售部门</span>
            <select value={filters.deptId} onChange={(event) => setFilters((prev) => ({ ...prev, deptId: event.target.value }))}>
              <option value="">全部部门</option>
              {referenceData.departments.map((item) => (
                <option key={item.id} value={String(item.id)}>
                  {String(item.deptName)}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>签订开始日期</span>
            <input type="date" value={filters.signDateStart} onChange={(event) => setFilters((prev) => ({ ...prev, signDateStart: event.target.value }))} />
          </label>
          <label className="form-field">
            <span>签订结束日期</span>
            <input type="date" value={filters.signDateEnd} onChange={(event) => setFilters((prev) => ({ ...prev, signDateEnd: event.target.value }))} />
          </label>
        </div>
        <div className="action-row action-row--right action-row--spaced">
          <button type="button" className="btn btn-primary btn-compact" onClick={() => void loadRows()}>
            <Search size={14} />
            查询合同
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-compact"
            onClick={() => {
              setFilters(defaultFilters);
              void loadRows(defaultFilters);
            }}
          >
            重置条件
          </button>
        </div>
      </section>

      <section className="panel panel-flat">
        <div className="section-bar">
          <h3>合同列表</h3>
          <span>{loading ? '加载中...' : `共 ${rows.length} 条`}</span>
        </div>
        <div className="table-wrap flat-table">
          <table className="data-table selectable">
            <thead>
              <tr>
                <th>合同编号</th>
                <th>合同名称</th>
                <th>客户</th>
                <th>产品</th>
                <th>部门</th>
                <th>签订日期</th>
                <th>合同总金额</th>
                <th>累计开票</th>
                <th>累计收款</th>
                <th>开票状态</th>
                <th>收款状态</th>
                <th>销售人员</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} onClick={() => void openDetail(row.id)}>
                  <td>{row.contractNo}</td>
                  <td>{row.contractName}</td>
                  <td>{row.customerName}</td>
                  <td>{row.productName}</td>
                  <td>{row.deptName}</td>
                  <td>{row.signDate}</td>
                  <td>{Number(row.totalAmount).toLocaleString()}</td>
                  <td>{Number(row.invoicedAmountTotal).toLocaleString()}</td>
                  <td>{Number(row.receivedAmountTotal).toLocaleString()}</td>
                  <td>{row.invoiceStatus}</td>
                  <td>{row.receiptStatus}</td>
                  <td>{row.ownerName}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel panel-flat">
        <div className="section-bar">
          <h3>合同详情</h3>
          <span>{selectedDetail ? <><Eye size={14} /> 已选择合同</> : '点击上方合同查看详情'}</span>
        </div>
        {selectedDetail ? (
          <div className="detail-stack">
            <div className="detail-grid">
              <div className="detail-list__item">
                <span>合同编号</span>
                <strong>{selectedDetail.contractNo}</strong>
              </div>
              <div className="detail-list__item">
                <span>合同名称</span>
                <strong>{selectedDetail.contractName}</strong>
              </div>
              <div className="detail-list__item">
                <span>客户</span>
                <strong>{selectedDetail.customerName}</strong>
              </div>
              <div className="detail-list__item">
                <span>产品</span>
                <strong>{selectedDetail.productName}</strong>
              </div>
              <div className="detail-list__item">
                <span>合同金额</span>
                <strong>{Number(selectedDetail.totalAmount).toLocaleString()}</strong>
              </div>
              <div className="detail-list__item">
                <span>采购金额</span>
                <strong>{Number(selectedDetail.purchaseAmount).toLocaleString()}</strong>
              </div>
              <div className="detail-list__item">
                <span>累计开票</span>
                <strong>{Number(selectedDetail.invoicedAmountTotal).toLocaleString()}</strong>
              </div>
              <div className="detail-list__item">
                <span>累计收款</span>
                <strong>{Number(selectedDetail.receivedAmountTotal).toLocaleString()}</strong>
              </div>
            </div>

            <div className="subsection-stack">
              <div className="subsection-block">
                <div className="subsection-title">付款条款</div>
                <div className="table-wrap flat-table compact">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>阶段编号</th>
                        <th>阶段名称</th>
                        <th>比例</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedDetail.paymentTerms.map((item) => (
                        <tr key={item.stageNo}>
                          <td>{item.stageNo}</td>
                          <td>{item.stageName}</td>
                          <td>{(Number(item.ratio) * 100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="subsection-block">
                <div className="subsection-title">开票记录</div>
                <div className="table-wrap flat-table compact">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>发票编号</th>
                        <th>金额</th>
                        <th>状态</th>
                        <th>日期</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedDetail.invoices.map((item) => (
                        <tr key={item.id}>
                          <td>{item.invoiceNo}</td>
                          <td>{Number(item.amount).toLocaleString()}</td>
                          <td>{item.status}</td>
                          <td>{item.invoiceDate}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-block">尚未选择合同。</div>
        )}
      </section>
    </div>
  );
};

export default ContractSearchPage;

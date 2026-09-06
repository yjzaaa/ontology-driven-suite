import React from 'react';
import { X } from 'lucide-react';
import type { PageRegistryItem, ReferenceData, TabItem } from '../../types';
import ContractEntryPage from '../contract/ContractEntryPage';
import ContractSearchPage from '../contract/ContractSearchPage';
import InvoiceEntryPage from '../contract/InvoiceEntryPage';
import PaymentReceivePage from '../contract/PaymentReceivePage';

interface MainAreaProps {
  tabs: TabItem[];
  activeTabId: string;
  setActiveTabId: (tabId: string) => void;
  closeTab: (tabId: string) => void;
  pageMap: Record<string, PageRegistryItem>;
  referenceData: ReferenceData | null;
  onOpenPage: (pageId: string) => void;
}

const MainArea: React.FC<MainAreaProps> = ({
  tabs,
  activeTabId,
  setActiveTabId,
  closeTab,
  pageMap,
  referenceData,
  onOpenPage,
}) => {
  const renderPage = (pageId: string) => {
    if (!referenceData) {
      return <div className="page-loading">页面元数据加载中...</div>;
    }

    switch (pageId) {
      case 'ContractEntryPage':
        return <ContractEntryPage referenceData={referenceData} onOpenPage={onOpenPage} />;
      case 'InvoiceEntryPage':
        return <InvoiceEntryPage onOpenPage={onOpenPage} />;
      case 'PaymentReceivePage':
        return <PaymentReceivePage />;
      case 'ContractSearchPage':
        return <ContractSearchPage referenceData={referenceData} />;
      default:
        return <div className="page-loading">未识别页面 {pageId}</div>;
    }
  };

  return (
    <div className="main-area">
      <div className="tab-bar">
        {tabs.map((tab) => {
          const page = pageMap[tab.pageId];
          const active = tab.id === activeTabId;
          return (
            <button
              type="button"
              key={tab.id}
              className={`tab-pill ${active ? 'active' : ''}`}
              onClick={() => setActiveTabId(tab.id)}
            >
              <span>{page?.title ?? tab.title}</span>
              <span
                className="tab-pill__close"
                onClick={(event) => {
                  event.stopPropagation();
                  closeTab(tab.id);
                }}
              >
                <X size={12} />
              </span>
            </button>
          );
        })}
      </div>

      <div className="main-content">
        {tabs.length === 0 ? <div className="page-loading">当前没有打开的页面。</div> : null}
        {tabs.map((tab) => (
          <section key={tab.id} style={{ display: tab.id === activeTabId ? 'block' : 'none', height: '100%' }}>
            {renderPage(tab.pageId)}
          </section>
        ))}
      </div>
    </div>
  );
};

export default MainArea;

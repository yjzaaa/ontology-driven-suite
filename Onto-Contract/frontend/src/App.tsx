import React, { useEffect, useMemo, useState } from 'react';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import MainArea from './components/Layout/MainArea';
import AIChat from './components/Layout/AIChat';
import Login from './components/Layout/Login';
import { useResizable } from './hooks/useResizable';
import { getCurrentUser, getNavigation, getPages, getReferenceData, logout } from './api/client';
import type { NavigationNode, PageRegistryItem, ReferenceData, TabItem, UserProfile } from './types';

const DEFAULT_PAGE_ID = 'ContractSearchPage';

const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [navigation, setNavigation] = useState<NavigationNode[]>([]);
  const [pageMap, setPageMap] = useState<Record<string, PageRegistryItem>>({});
  const [referenceData, setReferenceData] = useState<ReferenceData | null>(null);
  const [tabs, setTabs] = useState<TabItem[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>('');
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [isChatVisible, setIsChatVisible] = useState(true);

  const { width: sidebarWidth, startResizing: startResizingSidebar } = useResizable(250, 180, 420, 'left');
  const { width: chatWidth, startResizing: startResizingChat } = useResizable(420, 320, 760, 'right');

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const current = await getCurrentUser();
        setUser(current);
      } catch {
        setUser(null);
      } finally {
        setIsBootstrapping(false);
      }
    };
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!user) {
      return;
    }
    const loadMeta = async () => {
      const [nav, pages, refs] = await Promise.all([getNavigation(), getPages(), getReferenceData()]);
      const map = pages.reduce<Record<string, PageRegistryItem>>((acc, page) => {
        acc[page.pageId] = page;
        return acc;
      }, {});
      setNavigation(nav);
      setPageMap(map);
      setReferenceData(refs);
      const defaultPage = map[DEFAULT_PAGE_ID];
      if (defaultPage) {
        const initialTab: TabItem = {
          id: `tab-${DEFAULT_PAGE_ID}`,
          pageId: defaultPage.pageId,
          title: defaultPage.title,
        };
        setTabs([initialTab]);
        setActiveTabId(initialTab.id);
      }
    };
    void loadMeta();
  }, [user]);

  const openPage = (pageId: string) => {
    const page = pageMap[pageId];
    if (!page) {
      return;
    }
    const existing = tabs.find((tab) => tab.pageId === pageId);
    if (existing) {
      setActiveTabId(existing.id);
      return;
    }
    const tab: TabItem = {
      id: `tab-${pageId}-${Date.now()}`,
      pageId,
      title: page.title,
    };
    setTabs((prev) => [...prev, tab]);
    setActiveTabId(tab.id);
  };

  const closeTab = (tabId: string) => {
    setTabs((prev) => {
      const nextTabs = prev.filter((tab) => tab.id !== tabId);
      if (activeTabId === tabId) {
        setActiveTabId(nextTabs.length > 0 ? nextTabs[nextTabs.length - 1].id : '');
      }
      return nextTabs;
    });
  };

  const activePageId = useMemo(() => tabs.find((tab) => tab.id === activeTabId)?.pageId, [activeTabId, tabs]);

  const handleLogout = async () => {
    await logout();
    setUser(null);
    setNavigation([]);
    setPageMap({});
    setReferenceData(null);
    setTabs([]);
    setActiveTabId('');
  };

  if (isBootstrapping) {
    return <div className="app-loading">系统初始化中...</div>;
  }

  if (!user) {
    return <Login onLoginSuccess={setUser} />;
  }

  return (
    <div className="app-shell">
      <Header
        appTitle="AI原生合同管理系统"
        displayName={user.displayName}
        toggleSidebar={() => setIsSidebarVisible((prev) => !prev)}
        toggleChat={() => setIsChatVisible((prev) => !prev)}
        onLogout={handleLogout}
      />

      <div className="app-workspace">
        {isSidebarVisible ? (
          <div className="left-pane" style={{ width: sidebarWidth, minWidth: sidebarWidth }}>
            <Sidebar navigation={navigation} onOpenPage={openPage} activePageId={activePageId} />
            <div className="pane-resizer right" onMouseDown={startResizingSidebar} />
          </div>
        ) : null}

        <div className="center-pane">
          <MainArea
            tabs={tabs}
            activeTabId={activeTabId}
            setActiveTabId={setActiveTabId}
            closeTab={closeTab}
            pageMap={pageMap}
            referenceData={referenceData}
            onOpenPage={openPage}
          />
        </div>

        {isChatVisible ? (
          <div className="right-pane" style={{ width: chatWidth, minWidth: chatWidth }}>
            <div className="pane-resizer left" onMouseDown={startResizingChat} />
            <AIChat onOpenPage={openPage} />
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default App;

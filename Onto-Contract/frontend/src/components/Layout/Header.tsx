import React from 'react';
import { LogOut, PanelLeftClose, PanelRightClose, ScrollText, UserCircle } from 'lucide-react';

interface HeaderProps {
  appTitle: string;
  displayName: string;
  toggleSidebar: () => void;
  toggleChat: () => void;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({
  appTitle,
  displayName,
  toggleSidebar,
  toggleChat,
  onLogout,
}) => {
  return (
    <header className="app-header">
      <div className="app-header__left">
        <button type="button" className="ghost-icon-btn" onClick={toggleSidebar} title="切换导航">
          <PanelLeftClose size={18} />
        </button>
        <div className="app-logo-mark">
          <ScrollText size={18} />
        </div>
        <div className="app-title-group">
          <div className="app-title">{appTitle}</div>
          <div className="app-subtitle">Ontology Registry + Hybrid UI + AI Copilot</div>
        </div>
      </div>

      <div className="app-header__right">
        <div className="app-user-chip">
          <UserCircle size={16} />
          <span>{displayName}</span>
        </div>
        <button type="button" className="ghost-icon-btn" onClick={toggleChat} title="切换 AI 助手">
          <PanelRightClose size={18} />
        </button>
        <button type="button" className="ghost-text-btn" onClick={onLogout}>
          <LogOut size={14} />
          退出
        </button>
      </div>
    </header>
  );
};

export default Header;

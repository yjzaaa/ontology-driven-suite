import React, { useEffect, useMemo, useState } from 'react';
import {
  BadgeDollarSign,
  ChevronDown,
  ChevronRight,
  FilePlus2,
  FileSearch,
  FileText,
  Receipt,
  Search,
} from 'lucide-react';
import type { NavigationNode } from '../../types';

interface SidebarProps {
  navigation: NavigationNode[];
  onOpenPage: (pageId: string) => void;
  activePageId?: string;
}

const iconMap: Record<string, React.ReactNode> = {
  FileText: <FileText size={18} />,
  FilePlus2: <FilePlus2 size={16} />,
  ReceiptText: <Receipt size={16} />,
  BadgeDollarSign: <BadgeDollarSign size={16} />,
  Search: <Search size={16} />,
  FileSearch: <FileSearch size={16} />,
};

const Sidebar: React.FC<SidebarProps> = ({ navigation, onOpenPage, activePageId }) => {
  const defaultExpanded = useMemo(
    () => navigation.filter((item) => item.children?.length).map((item) => item.id),
    [navigation],
  );
  const [expandedIds, setExpandedIds] = useState<string[]>(defaultExpanded);

  useEffect(() => {
    setExpandedIds(defaultExpanded);
  }, [defaultExpanded]);

  const toggleGroup = (groupId: string) => {
    setExpandedIds((prev) => (prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId]));
  };

  const renderNode = (node: NavigationNode, level = 0) => {
    const hasChildren = Boolean(node.children?.length);
    const isExpanded = expandedIds.includes(node.id);
    const isActive = node.payload === activePageId;
    const icon = iconMap[node.icon ?? 'FileText'] ?? <FileText size={16} />;

    return (
      <div key={node.id} className="sidebar-node">
        <button
          type="button"
          className={`sidebar-node__button ${isActive ? 'active' : ''}`}
          style={{ paddingLeft: `${16 + level * 18}px` }}
          onClick={() => {
            if (hasChildren) {
              toggleGroup(node.id);
            } else if (node.payload) {
              onOpenPage(node.payload);
            }
          }}
        >
          <span className="sidebar-node__icon">{icon}</span>
          <span className="sidebar-node__label">{node.label}</span>
          {hasChildren ? (
            <span className="sidebar-node__chevron">
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </span>
          ) : null}
        </button>

        {hasChildren && isExpanded ? (
          <div className="sidebar-node__children">{node.children?.map((child) => renderNode(child, level + 1))}</div>
        ) : null}
      </div>
    );
  };

  return <aside className="app-sidebar">{navigation.map((item) => renderNode(item))}</aside>;
};

export default Sidebar;

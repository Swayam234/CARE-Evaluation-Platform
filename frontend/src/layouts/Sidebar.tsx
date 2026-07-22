import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, PlusCircle, History, BarChart3,
  GitCompare, Settings, ChevronLeft, ChevronRight,
  Zap, Shield, Brain, DollarSign, Star,
} from 'lucide-react';
import { clsx } from 'clsx';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  badge?: string;
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
  { to: '/evaluate', icon: <PlusCircle size={20} />, label: 'New Evaluation' },
  { to: '/history', icon: <History size={20} />, label: 'History' },
  { to: '/comparison', icon: <GitCompare size={20} />, label: 'Comparison' },
  { to: '/analytics', icon: <BarChart3 size={20} />, label: 'Analytics' },
  { to: '/settings', icon: <Settings size={20} />, label: 'Settings' },
];

const CARE_LETTERS = [
  { letter: 'C', icon: <Brain size={14} />, color: 'text-indigo-400', bg: 'bg-indigo-900/40' },
  { letter: 'A', icon: <Star size={14} />, color: 'text-emerald-400', bg: 'bg-emerald-900/40' },
  { letter: 'R', icon: <Shield size={14} />, color: 'text-amber-400', bg: 'bg-amber-900/40' },
  { letter: 'E', icon: <DollarSign size={14} />, color: 'text-blue-400', bg: 'bg-blue-900/40' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const location = useLocation();

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 h-full z-30 flex flex-col',
        'bg-bg-secondary border-r border-bg-border',
        'transition-all duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className={clsx(
        'flex items-center gap-3 px-4 py-5 border-b border-bg-border',
        collapsed ? 'justify-center' : 'justify-between'
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5">
              {CARE_LETTERS.map(({ letter, color, bg }) => (
                <span
                  key={letter}
                  className={clsx(
                    'w-7 h-7 rounded flex items-center justify-center',
                    'text-sm font-black', color, bg
                  )}
                >
                  {letter}
                </span>
              ))}
            </div>
            <div>
              <p className="text-xs font-bold text-slate-100 leading-none">CARE</p>
              <p className="text-[9px] text-slate-400 leading-none">EVALUATOR</p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="flex flex-col gap-0.5">
            {CARE_LETTERS.map(({ letter, color, bg }) => (
              <span
                key={letter}
                className={clsx('w-5 h-5 rounded text-[9px] font-black flex items-center justify-center', color, bg)}
              >
                {letter}
              </span>
            ))}
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-bg-hover text-slate-400 hover:text-slate-200 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = item.to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={collapsed ? item.label : undefined}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg',
                'transition-all duration-200 font-medium text-sm',
                collapsed ? 'justify-center' : '',
                isActive
                  ? 'bg-care-c/20 text-care-c border border-care-c/30'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-bg-hover'
              )}
            >
              <span className={clsx('flex-shrink-0', isActive ? 'text-care-c' : '')}>
                {item.icon}
              </span>
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer: Version badge */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-bg-border">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-care-c" />
            <span className="text-xs text-slate-500">CARE Evaluator v1.0</span>
          </div>
          <p className="text-[10px] text-slate-600 mt-1">Enterprise AI Evaluation</p>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;

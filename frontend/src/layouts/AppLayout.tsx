import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Bell, User, Search, Moon } from 'lucide-react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Sidebar from './Sidebar';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/evaluate': 'New Evaluation',
  '/history': 'Evaluation History',
  '/comparison': 'Agent Comparison',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

const AppLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  const pageTitle = Object.entries(PAGE_TITLES).find(([path]) =>
    path === '/' ? location.pathname === '/' : location.pathname.startsWith(path)
  )?.[1] || 'CARE Evaluator';

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((c) => !c)}
      />

      {/* Main content area */}
      <div
        className="flex-1 flex flex-col overflow-hidden transition-all duration-300"
        style={{ marginLeft: sidebarCollapsed ? '4rem' : '16rem' }}
      >
        {/* Top bar */}
        <header className="flex-shrink-0 h-16 flex items-center justify-between px-6 border-b border-bg-border bg-bg-secondary/80 backdrop-blur-sm">
          <div>
            <h1 className="text-lg font-semibold text-slate-100">{pageTitle}</h1>
            <p className="text-xs text-slate-500">Enterprise AI Evaluation Platform</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Notifications */}
            <button className="btn-ghost relative">
              <Bell size={18} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-care-c rounded-full" />
            </button>

            {/* User avatar – Auth scaffold */}
            <div className="flex items-center gap-2 pl-3 border-l border-bg-border">
              <div className="w-8 h-8 rounded-full bg-care-c/20 border border-care-c/40 flex items-center justify-center">
                <User size={16} className="text-care-c" />
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-medium text-slate-200">Admin</p>
                <p className="text-[10px] text-slate-500">Evaluator</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6 animate-fade-in">
          <Outlet />
        </main>
      </div>

      {/* Toast notifications */}
      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        pauseOnHover
        theme="dark"
        toastStyle={{ background: '#1E293B', border: '1px solid #2D3748' }}
      />
    </div>
  );
};

export default AppLayout;

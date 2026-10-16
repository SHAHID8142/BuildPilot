import React from 'react';
import { cmsConfig } from '../config/cms.config';

interface AdminLayoutProps {
  currentTab: string;
  children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ currentTab, children }) => {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex font-sans antialiased">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0">
        <div>
          <div className="flex items-center space-x-3 px-2 py-4 border-b border-slate-800 mb-6">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-slate-950">
              ⚡
            </div>
            <div>
              <h1 className="font-bold text-sm leading-tight text-white">{cmsConfig.siteTitle}</h1>
              <span className="text-xs text-emerald-400 font-mono">SPS-CMS v1.0</span>
            </div>
          </div>

          <nav className="space-y-1">
            <a
              href="/admin"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                currentTab === 'dashboard' ? 'bg-emerald-500/10 text-emerald-400 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
              }`}
            >
              📊 Overview
            </a>

            <a
              href="/admin/pages"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                currentTab === 'pages' ? 'bg-emerald-500/10 text-emerald-400 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
              }`}
            >
              📄 Site Pages (Visual Editor)
            </a>

            <div className="pt-4 pb-2 px-3 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Collections
            </div>

            {cmsConfig.collections.map((col) => (
              <a
                key={col.name}
                href={`/admin/collections/${col.name}`}
                className={`flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  currentTab === col.name ? 'bg-emerald-500/10 text-emerald-400 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
                }`}
              >
                <span>📦 {col.label}</span>
              </a>
            ))}

            <div className="pt-4 pb-2 px-3 text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Assets & System
            </div>

            <a
              href="/admin/media"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                currentTab === 'media' ? 'bg-emerald-500/10 text-emerald-400 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
              }`}
            >
              🖼️ Media Library
            </a>

            <a
              href="/admin/settings"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                currentTab === 'settings' ? 'bg-emerald-500/10 text-emerald-400 font-semibold' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
              }`}
            >
              ⚙️ Site Settings
            </a>
          </nav>
        </div>

        <div className="border-t border-slate-800 pt-4 flex items-center justify-between px-2">
          <a href="/" target="_blank" className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
            🌐 View Public Site ↗
          </a>
          <a href="/api/auth/logout" className="text-xs text-rose-400 hover:underline">
            Logout
          </a>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-slate-950/50 backdrop-blur sticky top-0 z-10">
          <div className="text-sm text-slate-400">
            Admin Portal / <span className="text-white font-medium capitalize">{currentTab}</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Sync Active
            </span>
          </div>
        </header>

        <div className="p-8 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

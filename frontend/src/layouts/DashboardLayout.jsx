import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';

export function DashboardLayout() {
  return (
    <div className="flex h-screen bg-brand-bg text-white overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 scrollbar-hide">
          <div className="animate-in fade-in duration-500 h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

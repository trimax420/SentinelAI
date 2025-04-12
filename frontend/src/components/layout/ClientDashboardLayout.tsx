"use client";

import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface ClientDashboardLayoutProps {
  children: ReactNode;
}

export default function ClientDashboardLayout({ children }: ClientDashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
} 
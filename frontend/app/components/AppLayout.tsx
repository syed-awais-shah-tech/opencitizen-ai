"use client";

import React, { useState } from "react";
import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />

      {/* Main Content Area */}
      <div className="app-main">
        <TopNavbar onToggleSidebar={toggleSidebar} />
        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
}

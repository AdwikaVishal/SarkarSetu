"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/layout/Sidebar";
import { MobileDrawer } from "@/components/layout/MobileDrawer";
import { Topbar } from "@/components/layout/Topbar";
import { useAuth } from "@/context/AuthContext";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { isLoading, isAuthenticated } = useAuth();
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // Close mobile drawer on route change
  useEffect(() => {
    const handleRouteChange = () => {
      setMobileDrawerOpen(false);
    };
    const handlePopState = () => {
      setMobileDrawerOpen(false);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-lime border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center p-8">
          <div className="w-16 h-16 rounded-full bg-accent-lime/10 flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-accent-lime" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="font-heading font-bold text-xl text-text-primary mb-2">SarkarSetu AI</h2>
          <p className="text-text-muted">Application is ready. Redirecting to dashboard...</p>
          <p className="text-text-muted text-sm">Loading business data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col lg:flex-row">
      {/* Mobile Drawer */}
      <MobileDrawer
        isOpen={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
      />

      {/* Sidebar - hidden on mobile, shown on lg+ */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:bg-bg-elevated">
        <Sidebar />
      </aside>

      {/* Topbar - shown on mobile only, hidden on lg+ (sidebar handles branding) */}
      <Topbar
        onMenuClick={() => setMobileDrawerOpen(true)}
        className="lg:hidden"
      />

      {/* Main Content */}
      <div className="flex flex-col lg:flex-row lg:ml-64 lg:wcalc-[calc(100%-64px)] min-w-0">
        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 pt-4 lg:pt-8 min-h-[calc(100vh-2rem)] lg:min-h-[calc(100vh-3rem)] overflow-x-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
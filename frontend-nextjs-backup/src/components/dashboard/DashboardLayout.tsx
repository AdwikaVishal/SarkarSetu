"use client";

import { useState, useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { MobileDrawer } from "@/components/layout/MobileDrawer";
import { useAuth } from "@/context/AuthContext";
import { LoadingState } from "@/components/ui/LoadingState";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const PAGE_META: Record<string, { title: string; breadcrumb?: string }> = {
  "/dashboard": { title: "Dashboard" },
  "/assistant": { title: "AI Assistant" },
  "/profile": { title: "Business Profile" },
  "/schemes": { title: "Scheme Discovery" },
  "/recommendations": { title: "Recommendations" },
  "/eligibility": { title: "Eligibility Checker" },
  "/documents": { title: "Document Centre" },
  "/roadmap": { title: "Action Roadmap" },
  "/tasks": { title: "My Tasks" },
  "/activity": { title: "Activity History" },
  "/settings": { title: "Settings" },
};

export function getPageMeta(pathname: string) {
  const base = `/${pathname.split("/").filter(Boolean)[0] ?? ""}`;
  return PAGE_META[base] ?? { title: "SarkarSetu AI" };
}

/**
 * The one and only authenticated application shell.
 *
 * Desktop:  [ Sidebar 250px | Topbar + page content ]  via CSS grid, so the
 *           sidebar participates in layout and can never overlap the content.
 * Mobile:   the sidebar is removed from the grid and rendered as a drawer.
 *
 * The shell owns the only Topbar/Sidebar instances; pages render content only.
 */
export function DashboardLayout({ children }: { children: ReactNode }) {
  const {
    user,
    logout,
    isLoading: authLoading,
    retryAuth,
    isDevMode,
  } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const meta = getPageMeta(pathname);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  const handleLogout = async () => {
    await logout();
    router.replace("/");
  };

  if (authLoading) {
    return <ShellMessage title="Loading your workspace" loading />;
  }

  if (!user) {
    return (
      <ShellMessage
        title="Sign in required"
        description={
          isDevMode
            ? "We couldn't reach the SarkarSetu API to start your demo session. Make sure the backend is running on http://localhost:8000, then try again."
            : "Please sign in to access your SarkarSetu workspace."
        }
        action={
          <Button variant="primary" size="md" onClick={retryAuth}>
            Try again
          </Button>
        }
      />
    );
  }

  const displayName = user.full_name || user.email?.split("@")[0] || "Account";

  return (
    <div
      className={cn(
        "min-h-dvh bg-bg-primary lg:grid",
        collapsed
          ? "lg:grid-cols-[76px_minmax(0,1fr)]"
          : "lg:grid-cols-[250px_minmax(0,1fr)]"
      )}
    >
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((value) => !value)}
      />

      <div className="flex min-h-dvh min-w-0 flex-col">
        <Topbar
          title={meta.title}
          breadcrumb="SarkarSetu"
          showSearch={false}
          userName={displayName}
          email={user.email}
          onOpenMenu={() => setDrawerOpen(true)}
          onLogout={handleLogout}
        />

        <main id="main-content" className="min-w-0 flex-1">
          <div className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            {children}
          </div>
        </main>
      </div>

      <MobileDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        userName={displayName}
        email={user.email}
        onLogout={handleLogout}
      />
    </div>
  );
}

function ShellMessage({
  title,
  description,
  loading = false,
  action,
}: {
  title: string;
  description?: string;
  loading?: boolean;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-bg-primary px-6">
      <div className="flex max-w-sm flex-col items-center text-center">
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-deep-rose/15">
          <span className="h-6 w-6 rounded-full bg-deep-rose" aria-hidden="true" />
        </div>
        <h1 className="font-heading text-xl font-bold text-text-primary">{title}</h1>
        {description && <p className="mt-2 text-sm text-text-muted">{description}</p>}
        {loading && <LoadingState variant="dots" size="md" className="mt-5" />}
        {action && <div className="mt-6">{action}</div>}
      </div>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Building2,
  ChevronRight,
  ClipboardCheck,
  Compass,
  FolderOpen,
  History,
  LayoutDashboard,
  ListChecks,
  LogOut,
  MessageSquare,
  Settings,
  Sparkles,
  Target,
  X,
  type LucideIcon,
} from "lucide-react";

interface DrawerLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

const groups: Array<{ label: string; links: DrawerLink[] }> = [
  {
    label: "Workspace",
    links: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/profile", label: "My Business", icon: Building2 },
      { href: "/assistant", label: "AI Assistant", icon: MessageSquare },
    ],
  },
  {
    label: "Discover",
    links: [
      { href: "/schemes", label: "Scheme Discovery", icon: Compass },
      { href: "/recommendations", label: "Recommendations", icon: Sparkles },
      { href: "/eligibility", label: "Eligibility Checker", icon: ClipboardCheck },
    ],
  },
  {
    label: "Manage",
    links: [
      { href: "/documents", label: "Document Centre", icon: FolderOpen },
      { href: "/roadmap", label: "Action Roadmap", icon: Target },
      { href: "/tasks", label: "My Tasks", icon: ListChecks },
      { href: "/activity", label: "Activity History", icon: History },
    ],
  },
  {
    label: "Preferences",
    links: [{ href: "/settings", label: "Settings", icon: Settings }],
  },
];

export function MobileDrawer({
  open,
  onClose,
  userName,
  email,
  onLogout,
}: {
  open: boolean;
  onClose: () => void;
  userName?: string;
  email?: string;
  onLogout?: () => void | Promise<void>;
}) {
  const pathname = usePathname();

  // Close when the route changes.
  useEffect(() => {
    onClose();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  // Lock page scroll while the drawer is open.
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  // Escape closes the drawer.
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 lg:hidden",
        open ? "visible" : "invisible pointer-events-none"
      )}
      aria-hidden={!open}
    >
      {/* Backdrop */}
      <div
        className={cn(
          "absolute inset-0 bg-text-primary/30 backdrop-blur-sm transition-opacity duration-300",
          open ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        className={cn(
          "absolute inset-y-0 left-0 flex w-[280px] max-w-[85vw] flex-col bg-bg-elevated shadow-xl transition-transform duration-300 ease-out",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-border px-4">
          <Link
            href="/dashboard"
            onClick={onClose}
            className="flex min-w-0 items-center gap-2.5"
          >
            <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-deep-rose">
              <Sparkles className="h-5 w-5 text-white" aria-hidden="true" />
            </span>
            <span className="truncate font-heading text-base font-bold text-text-primary">
              SarkarSetu AI
            </span>
          </Link>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-bg-primary hover:text-text-primary"
            aria-label="Close navigation menu"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <nav aria-label="Primary" className="min-h-0 flex-1 overflow-y-auto px-3 py-4">
          {groups.map((group) => (
            <div key={group.label} className="mb-4">
              <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                {group.label}
              </p>
              <ul className="flex flex-col gap-1">
                {group.links.map((link) => {
                  const active =
                    pathname === link.href ||
                    (link.href !== "/dashboard" && pathname.startsWith(`${link.href}/`));
                  const Icon = link.icon;
                  return (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        onClick={onClose}
                        aria-current={active ? "page" : undefined}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                          active
                            ? "bg-deep-rose/15 text-text-primary"
                            : "text-text-muted hover:bg-bg-primary hover:text-text-primary"
                        )}
                      >
                        <Icon
                          className={cn(
                            "h-[18px] w-[18px] flex-shrink-0",
                            active ? "text-deep-rose" : "text-text-muted"
                          )}
                          aria-hidden="true"
                        />
                        <span className="truncate">{link.label}</span>
                        {active && (
                          <ChevronRight className="ml-auto h-4 w-4 text-deep-rose" aria-hidden="true" />
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="flex-shrink-0 border-t border-border p-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-light-lavender text-xs font-semibold text-text-primary">
              {(userName || "U")
                .split(/\s+/)
                .filter(Boolean)
                .slice(0, 2)
                .map((part) => part[0]?.toUpperCase())
                .join("") || "U"}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-text-primary">
                {userName || "Account"}
              </p>
              {email && <p className="truncate text-xs text-text-muted">{email}</p>}
            </div>
          </div>
          <button
            type="button"
            onClick={async () => {
              onClose();
              await onLogout?.();
            }}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-border py-2.5 text-sm font-medium text-error transition-colors hover:bg-error/10"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign out
          </button>
        </div>
      </aside>
    </div>
  );
}

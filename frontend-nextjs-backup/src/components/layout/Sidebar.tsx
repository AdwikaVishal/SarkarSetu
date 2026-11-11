"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Building2,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Compass,
  FolderOpen,
  History,
  LayoutDashboard,
  ListChecks,
  MessageSquare,
  Settings,
  Sparkles,
  Target,
  type LucideIcon,
} from "lucide-react";

export interface SidebarNavLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  links: SidebarNavLink[];
}

const navGroups: NavGroup[] = [
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

export function Sidebar({
  collapsed = false,
  onToggleCollapse,
}: {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-dvh w-full flex-col border-r border-border bg-bg-elevated lg:flex",
        collapsed ? "px-2" : "px-4"
      )}
      aria-label="Main navigation"
    >
      {/* Brand */}
      <div
        className={cn(
          "flex h-16 flex-shrink-0 items-center gap-3 border-b border-border/60",
          collapsed ? "justify-center px-0" : "px-2"
        )}
      >
        <Link
          href="/dashboard"
          className="flex min-w-0 items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
          aria-label="SarkarSetu AI home"
        >
          <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-deep-rose">
            <Sparkles className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          {!collapsed && (
            <span className="truncate font-heading text-base font-bold tracking-tight text-text-primary">
              SarkarSetu AI
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav aria-label="Primary" className="min-h-0 flex-1 overflow-y-auto py-4">
        <ul className="flex flex-col gap-1">
          {navGroups.map((group) => (
            <li key={group.label} className="flex flex-col gap-1">
              <p
                className={cn(
                  "px-3 pb-1 pt-4 text-[11px] font-semibold uppercase tracking-wider text-text-muted",
                  collapsed && "sr-only"
                )}
              >
                {group.label}
              </p>
              {collapsed && <span className="sr-only">{group.label}</span>}
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
                        title={collapsed ? link.label : undefined}
                        aria-current={active ? "page" : undefined}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose",
                          collapsed && "justify-center px-0",
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
                        {!collapsed && <span className="truncate">{link.label}</span>}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>
      </nav>

      {/* Collapse control */}
      <div className="flex-shrink-0 border-t border-border/60 py-3">
        <button
          type="button"
          onClick={onToggleCollapse}
          className={cn(
            "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-text-muted transition-colors hover:bg-bg-primary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose",
            collapsed && "justify-center px-0"
          )}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

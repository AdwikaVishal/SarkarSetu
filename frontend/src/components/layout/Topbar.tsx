"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronRight,
  LogOut,
  Menu,
  Search,
  Settings,
  Sparkles,
  User,
} from "lucide-react";

export interface TopbarProps {
  title: string;
  /** Segment shown before the page title in the breadcrumb. */
  breadcrumb?: string;
  showSearch?: boolean;
  onSearch?: (query: string) => void;
  userName?: string;
  email?: string;
  onOpenMenu?: () => void;
  onLogout?: () => void | Promise<void>;
  /** Ref to the menu trigger button for focus management. */
  menuTriggerRef?: React.RefObject<HTMLButtonElement>;
}

export function Topbar({
  title,
  breadcrumb = "Dashboard",
  showSearch = true,
  onSearch,
  userName,
  email,
  onOpenMenu,
  onLogout,
  menuTriggerRef,
}: TopbarProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const pathname = usePathname();

  const closeMenu = useCallback(() => setMenuOpen(false), []);

  // Close on navigation.
  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  // Close on outside click.
  useEffect(() => {
    if (!menuOpen) return;

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node;
      if (
        menuRef.current?.contains(target) ||
        triggerRef.current?.contains(target)
      ) {
        return;
      }
      closeMenu();
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [menuOpen, closeMenu]);

  // Escape closes the menu and returns focus to the trigger.
  useEffect(() => {
    if (!menuOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenu();
        triggerRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [menuOpen, closeMenu]);

  const initials = (userName || "User")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  return (
    <header className="sticky top-0 z-30 flex h-16 flex-shrink-0 items-center gap-3 border-b border-border bg-bg-elevated px-4 sm:px-6 lg:px-8">
      {/* Mobile drawer trigger */}
      <button
        ref={menuTriggerRef}
        type="button"
        onClick={onOpenMenu}
        className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-text-primary transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose lg:hidden"
        aria-label="Open navigation menu"
        aria-haspopup="true"
        aria-expanded={menuOpen}
        aria-controls="mobile-drawer"
      >
        <Menu className="h-5 w-5" aria-hidden="true" />
      </button>

      {/* Breadcrumb / page context */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2">
          <Link
            href="/dashboard"
            className="hidden flex-shrink-0 text-xs font-semibold uppercase tracking-wider text-text-muted transition-colors hover:text-text-primary sm:inline"
          >
            {breadcrumb}
          </Link>
          <ChevronRight
            className="hidden h-3.5 w-3.5 flex-shrink-0 text-text-muted/70 sm:block"
            aria-hidden="true"
          />
          <span className="truncate font-heading text-sm font-semibold text-text-primary">
            {title}
          </span>
        </nav>
      </div>

      {/* Search */}
      {showSearch && (
        <div className="relative hidden md:block">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted"
            aria-hidden="true"
          />
          <input
            type="search"
            placeholder="Search schemes, documents..."
            aria-label="Search"
            className="h-9 w-48 rounded-full border border-border bg-bg-primary pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-transparent focus:outline-none focus:ring-2 focus:ring-deep-rose/40 lg:w-64"
            onChange={(event) => onSearch?.(event.target.value)}
          />
        </div>
      )}

      {/* Assistant shortcut */}
      <Link
        href="/assistant"
        className="flex h-9 flex-shrink-0 items-center gap-2 rounded-full bg-soft-yellow/40 px-3 text-sm font-medium text-text-primary transition-colors hover:bg-soft-yellow/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
        aria-label="Open AI Assistant"
      >
        <Sparkles className="h-4 w-4 text-deep-rose" aria-hidden="true" />
        <span className="hidden lg:inline">Ask Assistant</span>
      </Link>

      {/* User menu */}
      <div className="relative flex-shrink-0">
        <button
          ref={triggerRef}
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          className="flex h-9 items-center gap-2 rounded-full border border-border bg-bg-elevated pl-1 pr-2.5 text-sm font-medium text-text-primary transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
          aria-label="Account menu"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          aria-controls="account-menu"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-light-lavender text-xs font-semibold text-text-primary">
            {initials || <User className="h-4 w-4" aria-hidden="true" />}
          </span>
          <span className="hidden max-w-[10rem] truncate sm:inline">
            {userName || "Account"}
          </span>
        </button>

        {menuOpen && (
          <div
            id="account-menu"
            ref={menuRef}
            role="menu"
            aria-label="Account menu"
            className="absolute right-0 top-full z-50 mt-2 w-64 origin-top-right rounded-xl border border-border bg-bg-elevated p-2 shadow-lg"
          >
            <div className="border-b border-border/70 px-3 py-2.5">
              <p className="truncate text-sm font-semibold text-text-primary">
                {userName || "Account"}
              </p>
              {email && (
                <p className="mt-0.5 truncate text-xs text-text-muted">{email}</p>
              )}
            </div>

            <div className="pt-1">
              <Link
                href="/profile"
                role="menuitem"
                onClick={closeMenu}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-primary transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
              >
                <User className="h-4 w-4 text-text-muted" aria-hidden="true" />
                Business profile
              </Link>
              <Link
                href="/settings"
                role="menuitem"
                onClick={closeMenu}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-primary transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
              >
                <Settings className="h-4 w-4 text-text-muted" aria-hidden="true" />
                Settings
              </Link>
            </div>

            <div className="mt-1 border-t border-border/70 pt-1">
              <button
                type="button"
                role="menuitem"
                onClick={async () => {
                  closeMenu();
                  await onLogout?.();
                }}
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm font-medium text-error transition-colors hover:bg-error/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-error"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                Sign out
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

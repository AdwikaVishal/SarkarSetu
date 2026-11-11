"use client";

import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Menu, X, Search, MessageSquare, Building2, Home, Bot, ClipboardCheck, FolderOpen, MapPin, CheckSquare, BarChart2, History, User, Settings, LogOut, Sparkles, ChevronRight } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { useEffect, useState, useRef } from "react";

export interface TopbarProps {
  className?: string;
  children?: React.ReactNode;
  onMenuClick?: () => void;
  /** Title to display in the breadcrumb (for desktop) */
  title?: string;
  /** Segment shown before the page title in the breadcrumb. */
  breadcrumb?: string;
}

export function Topbar({ className, children, onMenuClick, title, breadcrumb = "Dashboard" }: TopbarProps) {
  const { user, isDevMode, logout } = useAuth();
  const location = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchTimeout, setSearchTimeout] = useState<number | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const initials = user?.full_name
    ?.split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "U";

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    setSearchTimeout(
      setTimeout(async () => {
        try {
          const results: any[] = [];

          // Search schemes
          try {
            const schemeResults = await fetch(`/api/v1/schemes/search?q=${encodeURIComponent(query)}`, {
              method: "GET",
              headers: { "Content-Type": "application/json" },
            });
            if (schemeResults.ok) {
              const data = await schemeResults.json();
              results.push(...data.map((s: any) => ({ ...s, type: "scheme" })));
            }
          } catch {}

          // Search knowledge
          try {
            const knowledgeResults = await fetch(`/api/v1/knowledge/search`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ query, limit: 5 }),
            });
            if (knowledgeResults.ok) {
              const data = await knowledgeResults.json();
              results.push(...data.results.map((r: any) => ({ ...r, type: "knowledge" })));
            }
          } catch {}

          setSearchResults(results);
        } catch (err) {
          setSearchResults([]);
        }
      }, 300)
    );
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSearchResults([]);
    if (searchTimeout) {
      clearTimeout(searchTimeout);
      setSearchTimeout(null);
    }
  };

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node) &&
          triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSearchOpen(false);
        setMenuOpen(false);
      }
    };
    const handlePopState = () => {
      setSearchOpen(false);
      setMenuOpen(false);
    };
    window.addEventListener("popstate", handlePopState);
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("popstate", handlePopState);
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  // Close menus on route change
  useEffect(() => {
    setSearchOpen(false);
    setMenuOpen(false);
  }, [location.pathname]);

  return (
    <>
      <header className={cn(
        "fixed top-0 left-0 right-0 z-30 bg-bg-elevated/80 backdrop-blur-sm border-b border-border lg:hidden",
        className
      )}>
        <div className="flex items-center justify-between h-14 px-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onMenuClick?.()}
              className="p-2 rounded-lg text-text-primary hover:bg-bg-card transition-colors"
              aria-label="Open menu"
            >
              <Menu className="w-6 h-6" aria-hidden="true" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-xl bg-accent-lime flex items-center justify-center">
                <svg className="w-4 h-4 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <span className="font-heading font-bold text-lg text-text-primary">SarkarSetu</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {children}

            {/* Mobile search dropdown - wrapped in fragment */}
            {searchOpen && (
              <>
                <div className="fixed inset-0 z-40 bg-black/50 lg:hidden animate-fade-in" onClick={() => setSearchOpen(false)} aria-hidden="true" />
                <div className="fixed inset-y-0 left-0 z-50 w-80 bg-bg-elevated border-r border-border lg:hidden animate-slide-in pt-6">
                  <div className="flex items-center justify-between px-4 mb-6">
                    <h2 className="font-heading font-semibold text-text-primary">Search</h2>
                    <button
                      onClick={() => setSearchOpen(false)}
                      className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors"
                      aria-label="Close search"
                    >
                      <X className="w-5 h-5" aria-hidden="true" />
                    </button>
                  </div>

                  <div className="px-4 mb-6">
                    <div className="flex flex-1 rounded-xl bg-bg-card border border-border focus-within:ring-2 focus-within:ring-accent-lime/50">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Escape") setSearchOpen(false); }}
                        placeholder="Search schemes, knowledge, documents..."
                        className="flex-1 py-2 px-3 rounded-xl text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                        aria-label="Search"
                      />
                    </div>
                  </div>

                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {searchResults.length > 0 ? (
                      searchResults.map((result) => {
                        const isScheme = result.type === "scheme";
                        const isKnowledge = result.type === "knowledge";
                        const title = isScheme ? result.name || result.full_name : (result.source_title || "Untitled");
                        const desc = isScheme
                          ? (result.category || "Government scheme")
                          : (result.relevant_excerpt || "Knowledge result");
                        const path = isScheme ? `/schemes/${result.id}` : `/knowledge/${result.id}`;

                        return (
                          <div
                            key={result.id}
                            className="px-3 py-2 rounded-xl bg-bg-card border-b border-border hover:bg-accent-lime/5 cursor-pointer"
                            onClick={() => {
                              setSearchOpen(false);
                              window.location.href = path;
                            }}
                          >
                            <div className="flex items-center gap-3">
                              <span className="w-3 h-3 rounded-full bg-primary/60 flex items-center justify-center text-sm">
                                {isScheme ? "📋" : "📄"}
                              </span>
                              <span className="min-w-0 flex-1 truncate text-text-primary">
                                {title}
                              </span>
                              <span className="text-xs text-text-muted truncate">{desc}</span>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-text-muted text-sm py-4">No results found</p>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* User context - only on desktop */}
            {user && (
              <div className="hidden lg:flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-bg-card text-sm text-text-muted">
                  <span className="avatar w-3 h-3 rounded-full bg-accent-lime" aria-hidden="true" />
                  <span>{user.full_name || user.email}</span>
                </div>
                <Button variant="ghost" size="sm" className="px-2 py-1">
                  <MessageSquare className="w-3.5 h-3.5" aria-hidden="true" />
                  Messages
                </Button>
                <Button variant="ghost" size="sm" className="px-2 py-1">
                  <Building2 className="w-3.5 h-3.5" aria-hidden="true" />
                  Profile
                </Button>
              </div>
            )}

            {/* Mobile search toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSearchOpen(true)}
              className="lg:hidden px-3 py-2"
              aria-label="Search"
            >
              <Search className="w-4 h-4" aria-hidden="true" />
            </Button>
          </div>
        </div>
      </header>

      {/* Desktop topbar */}
      <header className="hidden lg:sticky lg:top-0 lg:z-30 flex h-16 flex-shrink-0 items-center gap-3 border-b border-border bg-bg-elevated px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb / page context */}
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2">
            <NavLink
              to="/dashboard"
              className="hidden flex-shrink-0 text-xs font-semibold uppercase tracking-wider text-text-muted transition-colors hover:text-text-primary sm:inline"
            >
              {breadcrumb}
            </NavLink>
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
            onChange={(event) => handleSearch(event.target.value)}
            value={searchQuery}
          />
        </div>

        {/* Assistant shortcut */}
        <NavLink
          to="/assistant"
          className="flex h-9 flex-shrink-0 items-center gap-2 rounded-full bg-soft-yellow/40 px-3 text-sm font-medium text-text-primary transition-colors hover:bg-soft-yellow/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
          aria-label="Open AI Assistant"
        >
          <Sparkles className="h-4 w-4 text-deep-rose" aria-hidden="true" />
          <span className="hidden lg:inline">Ask Assistant</span>
        </NavLink>

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
              {user?.full_name || user?.email || "Account"}
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
                  {user?.full_name || user?.email || "Account"}
                </p>
                {user?.email && (
                  <p className="mt-0.5 truncate text-xs text-text-muted">{user.email}</p>
                )}
              </div>

              <div className="pt-1">
                <NavLink
                  to="/profile"
                  role="menuitem"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-primary transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
                >
                  <User className="h-4 w-4 text-text-muted" aria-hidden="true" />
                  Business profile
                </NavLink>
                <NavLink
                  to="/settings"
                  role="menuitem"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-text-primary transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-deep-rose"
                >
                  <Settings className="h-4 w-4 text-text-muted" aria-hidden="true" />
                  Settings
                </NavLink>
              </div>

              <div className="mt-1 border-t border-border/70 pt-1">
                <button
                  type="button"
                  role="menuitem"
                  onClick={async () => {
                    setMenuOpen(false);
                    await logout();
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

      {/* Mobile drawer */}
      <div
        className="fixed inset-0 z-40 bg-black/50 lg:hidden animate-fade-in"
        onClick={() => onMenuClick?.()}
        aria-hidden="true"
      />
      <aside
        className="fixed inset-y-0 left-0 z-50 w-72 max-w-[85%] bg-bg-elevated border-r border-border lg:hidden animate-slide-in"
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-accent-lime flex items-center justify-center">
              <svg className="w-5 h-5 text-text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <span className="font-heading font-bold text-xl text-text-primary">SarkarSetu</span>
          </div>
          <button
            onClick={() => onMenuClick?.()}
            className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors lg:hidden"
            aria-label="Close menu"
          >
            <X className="w-6 h-6" aria-hidden="true" />
          </button>
        </div>

        <nav className="p-4 space-y-1 overflow-y-auto flex-1" aria-label="Mobile navigation">
          {[
            { name: "Dashboard", href: "/dashboard", icon: Home },
            { name: "AI Assistant", href: "/assistant", icon: Bot },
            { name: "Eligibility", href: "/eligibility", icon: ClipboardCheck },
            { name: "Documents", href: "/documents", icon: FolderOpen },
            { name: "Roadmaps", href: "/roadmap", icon: MapPin },
            { name: "Tasks", href: "/tasks", icon: CheckSquare },
            { name: "Schemes", href: "/schemes", icon: BarChart2 },
            { name: "Activity", href: "/activity", icon: History },
            { name: "Profile", href: "/profile", icon: User },
            { name: "Settings", href: "/settings", icon: Settings },
          ].map((item) => {
            const isActive = item.href === location.pathname;
            const ItemIcon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => onMenuClick?.()}
                className={({ isActive: active }) => cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent-lime/10 text-text-primary border border-accent-lime/20"
                    : "text-text-muted hover:bg-bg-card hover:text-text-primary"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <ItemIcon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-accent-lime")} aria-hidden="true" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 p-2 rounded-xl bg-bg-card mb-3">
            <div className="w-8 h-8 rounded-full bg-accent-lime/10 flex items-center justify-center">
              <Building2 className="w-4 h-4 text-accent-lime" aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-text-primary truncate">
                {user?.full_name || user?.email || "User"}
              </p>
              <p className="text-xs text-text-muted truncate">{user?.email}</p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            fullWidth
            className="justify-start"
            onClick={async () => { onMenuClick?.(); await logout(); }}
          >
            <LogOut className="w-4 h-4" aria-hidden="true" /> Sign Out
          </Button>
        </div>
      </aside>
    </>
  );
}
"use client";

import { useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  MessageSquare, 
  Target, 
  FileText, 
  ClipboardCheck, 
  Sparkles, 
  ListTodo, 
  Building2, 
  Settings,
  Activity,
  X,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "../ui/Button";
import { LogOut } from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "AI Assistant", href: "/assistant", icon: MessageSquare },
  { name: "Eligibility", href: "/eligibility", icon: Target },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Roadmaps", href: "/roadmap", icon: ListTodo },
  { name: "Tasks", href: "/tasks", icon: ClipboardCheck },
  { name: "Schemes", href: "/schemes", icon: Sparkles },
  { name: "Activity", href: "/activity", icon: Activity },
  { name: "Profile", href: "/profile", icon: Building2 },
  { name: "Settings", href: "/settings", icon: Settings },
];

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MobileDrawer({ isOpen, onClose }: MobileDrawerProps) {
  const location = useLocation();
  const { user, logout } = useAuth();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 z-40 bg-black/50 lg:hidden animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      <aside className="fixed inset-y-0 left-0 z-50 w-72 max-w-[85%] bg-bg-elevated border-r border-border lg:hidden animate-slide-in">
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
            onClick={onClose}
            className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors lg:hidden"
            aria-label="Close menu"
          >
            <X className="w-6 h-6" aria-hidden="true" />
          </button>
        </div>

        <nav className="p-4 space-y-1 overflow-y-auto flex-1" aria-label="Mobile navigation">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== "/dashboard" && location.pathname.startsWith(item.href));
            
            const Icon = item.icon;
            
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={onClose}
                className={({ isActive: active }) => cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent-lime/10 text-text-primary border border-accent-lime/20"
                    : "text-text-muted hover:bg-bg-card hover:text-text-primary"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-accent-lime")} aria-hidden="true" />
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
            leftIcon={<LogOut className="w-4 h-4" />}
            onClick={() => { logout(); onClose(); }}
          >
            Sign Out
          </Button>
        </div>
      </aside>
    </>
  );
}
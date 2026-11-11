"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, "id">) => string;
  hideToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);
    
    // Auto-hide
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
    
    return id;
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, hideToast }}>
      {children}
      <ToastContainer toasts={toasts} onClose={hideToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

function ToastContainer({ toasts, onClose }: { toasts: Toast[]; onClose: (id: string) => void }) {
  if (toasts.length === 0) return null;

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const colors = {
    success: "bg-success/10 border-success/20 text-success",
    error: "bg-error/10 border-error/20 text-error",
    warning: "bg-warning/10 border-warning/20 text-warning",
    info: "bg-accent-purple/10 border-accent-purple/20 text-accent-purple",
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 w-full max-w-sm sm:max-w-md pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          icons={icons}
          colors={colors}
          onClose={onClose}
        />
      ))}
    </div>
  );
}

function ToastItem({ 
  toast, 
  icons, 
  colors, 
  onClose 
}: { 
  toast: Toast; 
  icons: Record<ToastType, React.ComponentType<{ className?: string }>>;
  colors: Record<ToastType, string>;
  onClose: (id: string) => void;
}) {
  const Icon = icons[toast.type];
  
  useEffect(() => {
    if (toast.duration !== 0) {
      const timer = setTimeout(() => onClose(toast.id), toast.duration ?? 5000);
      return () => clearTimeout(timer);
    }
  }, [toast, onClose]);

  return (
    <div 
      className={cn(
        "pointer-events-auto flex items-start gap-3 p-4 rounded-[16px] border shadow-lg animate-slide-in",
        colors[toast.type]
      )}
      role="alert"
      aria-live="polite"
    >
      <div className={cn("flex-shrink-0 w-5 h-5 mt-0.5", colors[toast.type])}>
        <Icon className="w-5 h-5" aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-heading font-semibold text-text-primary">{toast.title}</p>
        {toast.message && (
          <p className="mt-1 text-sm text-text-muted">{toast.message}</p>
        )}
        {toast.action && (
          <button
            onClick={() => {
              toast.action?.onClick();
              onClose(toast.id);
            }}
            className="mt-2 text-sm font-medium underline hover:no-underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 p-1 rounded-lg hover:bg-black/10 transition-colors text-text-muted"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4" aria-hidden="true" />
      </button>
    </div>
  );
}

// Hook for easy access
export function useToastHelpers() {
  const { showToast, hideToast } = useToast();
  
  return {
    success: (title: string, message?: string, options?: { duration?: number; action?: Toast["action"] }) => 
      showToast({ type: "success", title, message, ...options }),
    error: (title: string, message?: string, options?: { duration?: number; action?: Toast["action"] }) => 
      showToast({ type: "error", title, message, ...options }),
    warning: (title: string, message?: string, options?: { duration?: number; action?: Toast["action"] }) => 
      showToast({ type: "warning", title, message, ...options }),
    info: (title: string, message?: string, options?: { duration?: number; action?: Toast["action"] }) => 
      showToast({ type: "info", title, message, ...options }),
    dismiss: hideToast,
  };
}


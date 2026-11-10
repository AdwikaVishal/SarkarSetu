"use client";

import { type HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { X } from "lucide-react";

export interface ConfirmDialogProps extends HTMLAttributes<HTMLDivElement> {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary" | "secondary";
  isLoading?: boolean;
  children?: ReactNode;
}

export function ConfirmDialog({
  open,
  onClose,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
  children,
  className,
  ...props
}: ConfirmDialogProps) {
  if (!open) return null;

  const confirmVariants = {
    danger: "error",
    primary: "lime",
    secondary: "outline",
  } as const;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose} {...props}>
      <div
        className={cn(
          "bg-bg-elevated rounded-[24px] max-w-md w-full animate-scale-in",
          className
        )}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="flex items-start justify-between p-4 border-b border-border">
          <div />
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <h2 id="confirm-dialog-title" className="font-heading font-bold text-xl text-text-primary">
              {title}
            </h2>
            {description && (
              <p className="mt-2 text-text-muted">{description}</p>
            )}
          </div>
          
          {children && (
            <div className="pt-2">
              {children}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 p-4 border-t border-border bg-bg-card/50 rounded-b-[24px]">
          <Button
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={confirmVariants[variant]}
            onClick={onClose}
            isLoading={isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

// Hook for managing confirm dialogs
import { useState, useCallback } from "react";

interface ConfirmDialogState {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary" | "secondary";
  isLoading?: boolean;
  onConfirm: () => void | Promise<void>;
  children?: ReactNode;
}

export function useConfirmDialog() {
  const [state, setState] = useState<ConfirmDialogState | null>(null);

  const confirm = useCallback((
    options: Omit<ConfirmDialogState, "open"> & { open: true }
  ) => {
    setState({ ...options, open: true });
  }, []);

  const close = useCallback(() => {
    setState(null);
  }, []);

  const handleConfirm = useCallback(async () => {
    if (state?.onConfirm) {
      setState((prev) => prev ? { ...prev, isLoading: true } : null);
      try {
        await state.onConfirm();
      } finally {
        close();
      }
    } else {
      close();
    }
  }, [state, close]);

  return {
    state,
    confirm,
    close,
    handleConfirm,
    ConfirmDialog: state ? (
      <ConfirmDialog
        {...state}
        onClose={close}
      />
    ) : null,
  };
}
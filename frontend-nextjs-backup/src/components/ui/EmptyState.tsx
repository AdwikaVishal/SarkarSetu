"use client";

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { LucideIcon } from "lucide-react";

export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "primary" | "secondary" | "outline" | "ghost" | "lime" | "purple";
  };
  alignment?: "center" | "left";
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  alignment = "center",
  className,
  ...props
}: EmptyStateProps) {
  const alignments = {
    center: "text-center items-center",
    left: "text-left items-start",
  };

  return (
    <div
      className={cn(
        "flex flex-col gap-3 px-4 py-8",
        alignments[alignment],
        className
      )}
      {...props}
    >
      {Icon && (
        <div className="w-12 h-12 rounded-full bg-accent-lime/10 flex items-center justify-center text-accent-lime">
          <Icon className="w-6 h-6" aria-hidden="true" />
        </div>
      )}
      <div>
        <h3 className="font-heading font-bold text-lg text-text-primary sm:text-xl">{title}</h3>
        {description && (
          <p className="mt-1.5 max-w-md text-sm text-text-muted">{description}</p>
        )}
      </div>
      {action && (
        <Button
          variant={action.variant || "lime"}
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

export interface ErrorStateProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  code?: string | number;
  onRetry?: () => void;
  retryLabel?: string;
  alignment?: "center" | "left";
}

export function ErrorState({
  title = "Something went wrong",
  message,
  code,
  onRetry,
  retryLabel = "Try again",
  alignment = "center",
  className,
  ...props
}: ErrorStateProps) {
  const alignments = {
    center: "text-center items-center",
    left: "text-left items-start",
  };

  return (
    <div
      className={cn(
        "flex flex-col gap-4 py-12 px-6 bg-error/5 border border-error/20 rounded-[24px]",
        alignments[alignment],
        className
      )}
      {...props}
    >
      <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center text-error">
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <div>
        <h3 className="font-heading font-bold text-xl text-text-primary">{title}</h3>
        <p className="mt-1 text-text-muted">{message}</p>
        {code && (
          <p className="mt-2 text-xs font-mono text-text-muted">Error code: {code}</p>
        )}
      </div>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          {retryLabel}
        </Button>
      )}
    </div>
  );
}
"use client";

import { cn } from "@/lib/utils";

export interface LoadingStateProps {
  variant?: "dots" | "spinner" | "pulse";
  size?: "sm" | "md" | "lg";
  text?: string;
  className?: string;
}

export function LoadingState({ variant = "dots", size = "md", text, className }: LoadingStateProps) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
  };

  const textSizes = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
  };

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      {variant === "dots" && (
        <div className="flex gap-1" role="status" aria-label="Loading">
          <div className={cn(sizeClasses[size], "rounded-full bg-accent-lime animate-bounce [animation-delay:-0.3s]")} />
          <div className={cn(sizeClasses[size], "rounded-full bg-accent-lime animate-bounce [animation-delay:-0.15s]")} />
          <div className={cn(sizeClasses[size], "rounded-full bg-accent-lime animate-bounce")} />
        </div>
      )}
      {variant === "spinner" && (
        <svg
          className={cn(sizeClasses[size], "animate-spin text-accent-lime")}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {variant === "pulse" && (
        <div className={cn(sizeClasses[size], "rounded-full bg-accent-lime/30 animate-pulse")} />
      )}
      {text && (
        <p className={cn(textSizes[size], "text-text-muted")}>{text}</p>
      )}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-lg bg-bg-card border border-border animate-pulse", className)}>
      <div className="h-6 w-3/4 bg-border/50 rounded mx-4 mt-4" />
      <div className="h-4 w-1/2 bg-border/50 rounded mx-4 mt-2" />
      <div className="h-4 w-full bg-border/50 rounded mx-4 mt-2 mb-4" />
    </div>
  );
}
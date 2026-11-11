"use client";

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface LoadingStateProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "spinner" | "skeleton" | "dots";
  size?: "sm" | "md" | "lg" | "xl";
  text?: string;
}

export function LoadingState({ variant = "spinner", size = "md", text, className, ...props }: LoadingStateProps) {
  const sizes = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
    xl: "h-16 w-16",
  };

  const textSizes = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
    xl: "text-lg",
  };

  if (variant === "dots") {
    return (
      <div className={cn("flex items-center justify-center gap-1", className)} {...props}>
        <span className={cn("w-2 h-2 rounded-full bg-accent-lime animate-bounce", sizes[size])} style={{ animationDelay: "0ms" }} />
        <span className={cn("w-2 h-2 rounded-full bg-accent-purple animate-bounce", sizes[size])} style={{ animationDelay: "150ms" }} />
        <span className={cn("w-2 h-2 rounded-full bg-accent-lime animate-bounce", sizes[size])} style={{ animationDelay: "300ms" }} />
        {text && <span className={cn("ml-2 text-text-muted", textSizes[size])}>{text}</span>}
      </div>
    );
  }

  if (variant === "skeleton") {
    return (
      <div className={cn("animate-pulse space-y-4", className)} {...props}>
        <div className="h-8 w-3/4 bg-bg-dark/10 rounded" />
        <div className="h-4 w-full bg-bg-dark/10 rounded" />
        <div className="h-4 w-5/6 bg-bg-dark/10 rounded" />
        <div className="h-4 w-2/3 bg-bg-dark/10 rounded" />
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col items-center justify-center gap-3", className)} {...props}>
      <svg
        className={cn("animate-spin text-accent-lime", sizes[size])}
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
      {text && <span className={cn("text-text-muted font-medium", textSizes[size])}>{text}</span>}
    </div>
  );
}

export function SkeletonCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("animate-pulse bg-bg-card rounded-[28px] p-6", className)} {...props}>
      <div className="h-8 w-1/3 bg-bg-dark/10 rounded mb-4" />
      <div className="h-6 w-1/2 bg-bg-dark/10 rounded mb-2" />
      <div className="h-4 w-full bg-bg-dark/10 rounded mb-2" />
      <div className="h-4 w-5/6 bg-bg-dark/10 rounded" />
    </div>
  );
}

export function SkeletonList({ count = 3, className, ...props }: HTMLAttributes<HTMLDivElement> & { count?: number }) {
  return (
    <div className={cn("space-y-4", className)} {...props}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
"use client";

import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "error" | "outline" | "lime" | "purple";
  size?: "sm" | "md" | "lg";
  dot?: boolean;
}

const variants = {
  default: "bg-bg-dark text-text-inverse",
  success: "bg-success-light text-success",
  warning: "bg-warning/10 text-warning",
  error: "bg-error/10 text-error",
  outline: "border-2 border-border text-text-muted",
  lime: "bg-accent-lime/10 text-accent-lime",
  purple: "bg-accent-purple/10 text-accent-purple",
};

const sizes = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-sm",
  lg: "px-4 py-1.5 text-base",
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", size = "md", dot = false, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1.5 font-medium rounded-full",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" aria-hidden="true" />}
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";
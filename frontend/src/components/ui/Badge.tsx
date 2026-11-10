"use client";

import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "lime" | "purple" | "success" | "warning" | "error" | "outline";
  size?: "sm" | "md" | "lg";
  dot?: boolean;
}

const variants = {
  default: "bg-text-primary text-text-inverse",
  lime: "bg-accent-lime text-text-primary",
  purple: "bg-accent-purple text-text-inverse",
  success: "bg-success text-text-inverse",
  warning: "bg-warning text-text-primary",
  error: "bg-error text-text-inverse",
  outline: "border-2 border-border bg-transparent text-text-primary",
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
          "inline-flex items-center gap-1.5 font-heading font-medium rounded-full",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn(
              "w-1.5 h-1.5 rounded-full",
              variant === "lime" && "bg-text-primary",
              variant === "purple" && "bg-text-inverse",
              variant === "default" && "bg-text-inverse",
              variant === "success" && "bg-text-inverse",
              variant === "warning" && "bg-text-primary",
              variant === "error" && "bg-text-inverse",
              variant === "outline" && "bg-text-primary"
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";
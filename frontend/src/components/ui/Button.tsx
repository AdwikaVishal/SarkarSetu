"use client";

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "lime" | "purple" | "error";
  size?: "sm" | "md" | "lg" | "xl";
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
  asChild?: boolean;
}

const baseStyles = "inline-flex items-center justify-center font-heading font-medium transition-all duration-200 ease-out rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

const variants = {
  primary: "bg-text-primary text-bg-primary hover:bg-text-primary/90 active:bg-text-primary focus-visible:ring-text-primary",
  secondary: "bg-accent-purple text-text-inverse hover:bg-accent-purple-hover active:bg-accent-purple-hover focus-visible:ring-accent-purple",
  outline: "border-2 border-text-primary text-text-primary hover:bg-text-primary hover:text-bg-primary active:bg-text-primary/90 focus-visible:ring-text-primary",
  ghost: "text-text-primary hover:bg-bg-card active:bg-bg-card focus-visible:ring-text-primary",
  lime: "bg-accent-lime text-text-primary hover:bg-accent-lime-hover active:bg-accent-lime-hover focus-visible:ring-accent-lime shadow-lg shadow-lime/30",
  purple: "bg-accent-purple text-text-inverse hover:bg-accent-purple-hover active:bg-accent-purple-hover focus-visible:ring-accent-purple shadow-lg shadow-purple/30",
  error: "bg-error text-text-inverse hover:bg-error-hover active:bg-error-hover focus-visible:ring-error shadow-lg shadow-error/30",
};

const sizes = {
  sm: "px-4 py-2 text-sm gap-2",
  md: "px-6 py-3 text-base gap-2.5",
  lg: "px-8 py-4 text-lg gap-3",
  xl: "px-10 py-5 text-xl gap-3",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      children,
      asChild = false,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? "span" : "button";
    
    const buttonProps = asChild 
      ? { ...props, ref, className: cn(baseStyles, variants[variant], sizes[size], fullWidth && "w-full", className) }
      : { ...props, ref, disabled: disabled || isLoading, className: cn(baseStyles, variants[variant], sizes[size], fullWidth && "w-full", className) };

    return (
      <Comp {...buttonProps}>
        {isLoading ? (
          <svg
            className="animate-spin h-5 w-5"
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
        ) : (
          <>
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
          </>
        )}
      </Comp>
    );
  }
);

Button.displayName = "Button";
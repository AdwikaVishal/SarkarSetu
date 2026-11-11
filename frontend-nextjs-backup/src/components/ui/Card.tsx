"use client";

import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "outlined" | "dark";
  padding?: "none" | "sm" | "md" | "lg" | "xl";
  hover?: boolean;
  asChild?: boolean;
}

const variants = {
  default: "bg-bg-card border border-border",
  elevated: "bg-bg-elevated shadow-sm",
  outlined: "bg-bg-elevated border-2 border-border",
  dark: "bg-bg-dark text-text-inverse border border-border-dark",
};

const paddings = {
  none: "",
  sm: "p-3 sm:p-4",
  md: "p-4 sm:p-6",
  lg: "p-5 sm:p-8",
  xl: "p-6 sm:p-10",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = "default",
      padding = "md",
      hover = false,
      asChild = false,
      children,
      ...props
    },
    ref
  ) => {
    const Component = asChild ? "div" : "div";
    
    return (
      <Component
        ref={ref}
        className={cn(
          "rounded-lg transition-all duration-300 ease-out",
          variants[variant],
          paddings[padding],
          hover && "hover:-translate-y-1 hover:shadow-sm hover:border-accent-lime/50 cursor-pointer",
          className
        )}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("mb-4", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardHeader.displayName = "CardHeader";

export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  size?: "sm" | "md" | "lg" | "xl";
}

const titleSizes = {
  sm: "text-lg",
  md: "text-xl",
  lg: "text-2xl",
  xl: "text-3xl",
};

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, size = "md", children, ...props }, ref) => {
    return (
      <h3
        ref={ref}
        className={cn(
          "font-heading font-bold tracking-tight",
          titleSizes[size],
          className
        )}
        {...props}
      >
        {children}
      </h3>
    );
  }
);

CardTitle.displayName = "CardTitle";

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <p
        ref={ref}
        className={cn("text-text-muted mt-1", className)}
        {...props}
      >
        {children}
      </p>
    );
  }
);

CardDescription.displayName = "CardDescription";

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardContent.displayName = "CardContent";

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("mt-4 pt-4 border-t border-border/50 flex items-center gap-3", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = "CardFooter";
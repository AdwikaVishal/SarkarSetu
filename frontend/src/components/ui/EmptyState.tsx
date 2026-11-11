"use client";

import { type ReactNode, type ComponentType, isValidElementType } from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";

export interface EmptyStateProps {
  icon: ReactNode | ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "primary" | "secondary" | "outline" | "ghost" | "lime" | "purple" | "error";
  };
  alignment?: "center" | "left";
  className?: string;
}

export function EmptyState({ 
  icon, 
  title, 
  description, 
  action, 
  alignment = "center", 
  className 
}: EmptyStateProps) {
  // Handle icon rendering: component, element, or string
  const renderIcon = () => {
    if (icon == null) return null;
    
    // If it's a valid React component type (function/class/ForwardRefExoticComponent)
    if (isValidElementType(icon)) {
      const IconComponent = icon;
      return <IconComponent className="w-8 h-8" />;
    }
    
    // If it's already a React element, render it directly
    if (typeof icon === "object" && icon !== null && "$$typeof" in icon) {
      return icon;
    }
    
    // Otherwise render as-is (string, number, etc.)
    return icon;
  };
  
  return (
    <div className={cn(
      "py-12 px-6",
      alignment === "center" ? "text-center" : "text-left",
      className
    )}>
      <div className={cn(
        "w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 text-text-muted",
        alignment === "left" && "mx-0"
      )}>
        {renderIcon()}
      </div>
      <h3 className="font-heading font-bold text-lg text-text-primary mb-2">{title}</h3>
      <p className="text-text-muted mb-6">{description}</p>
      {action && (
        <Button variant={action.variant || "lime"} onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

export interface ErrorStateProps {
  title: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  alignment?: "center" | "left";
  className?: string;
}

export function ErrorState({ 
  title, 
  message, 
  onRetry, 
  retryLabel = "Try Again", 
  alignment = "center", 
  className 
}: ErrorStateProps) {
  return (
    <div className={cn(
      "py-12 px-6",
      alignment === "center" ? "text-center" : "text-left",
      className
    )}>
      <div className="w-16 h-16 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-6 text-error">
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 className="font-heading font-bold text-lg text-text-primary mb-2">{title}</h3>
      <p className="text-text-muted mb-6">{message}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          {retryLabel}
        </Button>
      )}
    </div>
  );
}
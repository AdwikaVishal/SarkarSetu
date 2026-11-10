"use client";

import { cn } from "@/lib/utils";
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  HelpCircle, 
  XCircle,
  Target,
  Info,
  AlertTriangle
} from "lucide-react";

export type StatusType = 
  | "eligible" 
  | "ineligible" 
  | "potentially_eligible" 
  | "needs_information" 
  | "unverified"
  | "pending"
  | "in_progress"
  | "completed"
  | "skipped"
  | "blocked"
  | "success"
  | "error"
  | "warning"
  | "info";

export interface StatusBadgeProps {
  status: StatusType;
  size?: "sm" | "md" | "lg";
  showIcon?: boolean;
  showLabel?: boolean;
  dot?: boolean;
  className?: string;
}

const statusConfig: Record<StatusType, { 
  label: string; 
  icon: React.ComponentType<{ className?: string }>;
  variant: "success" | "error" | "warning" | "lime" | "purple" | "outline" | "info";
  bg: string;
  text: string;
  border: string;
}> = {
  eligible: { 
    label: "Eligible", 
    icon: CheckCircle, 
    variant: "success",
    bg: "bg-success/10", 
    text: "text-success", 
    border: "border-success/20" 
  },
  ineligible: { 
    label: "Not Eligible", 
    icon: XCircle, 
    variant: "error",
    bg: "bg-error/10", 
    text: "text-error", 
    border: "border-error/20" 
  },
  potentially_eligible: { 
    label: "Potentially Eligible", 
    icon: Target, 
    variant: "lime",
    bg: "bg-accent-lime/10", 
    text: "text-accent-lime", 
    border: "border-accent-lime/20" 
  },
  needs_information: { 
    label: "Needs Information", 
    icon: AlertCircle, 
    variant: "warning",
    bg: "bg-warning/10", 
    text: "text-warning", 
    border: "border-warning/20" 
  },
  unverified: { 
    label: "Unverified", 
    icon: HelpCircle, 
    variant: "outline",
    bg: "bg-text-muted/10", 
    text: "text-text-muted", 
    border: "border-border" 
  },
  pending: { 
    label: "Pending", 
    icon: Clock, 
    variant: "outline",
    bg: "bg-text-muted/10", 
    text: "text-text-muted", 
    border: "border-border" 
  },
  in_progress: { 
    label: "In Progress", 
    icon: Clock, 
    variant: "lime",
    bg: "bg-accent-lime/10", 
    text: "text-accent-lime", 
    border: "border-accent-lime/20" 
  },
  completed: { 
    label: "Completed", 
    icon: CheckCircle, 
    variant: "success",
    bg: "bg-success/10", 
    text: "text-success", 
    border: "border-success/20" 
  },
  skipped: { 
    label: "Skipped", 
    icon: AlertCircle, 
    variant: "warning",
    bg: "bg-warning/10", 
    text: "text-warning", 
    border: "border-warning/20" 
  },
  blocked: { 
    label: "Blocked", 
    icon: XCircle, 
    variant: "error",
    bg: "bg-error/10", 
    text: "text-error", 
    border: "border-error/20" 
  },
  success: { 
    label: "Success", 
    icon: CheckCircle, 
    variant: "success",
    bg: "bg-success/10", 
    text: "text-success", 
    border: "border-success/20" 
  },
  error: { 
    label: "Error", 
    icon: XCircle, 
    variant: "error",
    bg: "bg-error/10", 
    text: "text-error", 
    border: "border-error/20" 
  },
  warning: { 
    label: "Warning", 
    icon: AlertTriangle, 
    variant: "warning",
    bg: "bg-warning/10", 
    text: "text-warning", 
    border: "border-warning/20" 
  },
  info: { 
    label: "Info", 
    icon: Info, 
    variant: "purple",
    bg: "bg-accent-purple/10", 
    text: "text-accent-purple", 
    border: "border-accent-purple/20" 
  },
};

const sizeStyles = {
  sm: "px-2 py-0.5 text-xs gap-1",
  md: "px-3 py-1 text-sm gap-1.5",
  lg: "px-4 py-1.5 text-base gap-2",
};

const iconSizes = {
  sm: "w-3 h-3",
  md: "w-4 h-4",
  lg: "w-5 h-5",
};

export function StatusBadge({ 
  status, 
  size = "md", 
  showIcon = true, 
  showLabel = true,
  dot = false,
  className 
}: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.unverified;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center font-heading font-medium rounded-full border",
        sizeStyles[size],
        config.bg,
        config.text,
        config.border,
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full flex-shrink-0",
            size === "sm" && "w-1 h-1",
            size === "lg" && "w-2 h-2",
            config.text
          )}
          aria-hidden="true"
        />
      )}
      {showIcon && <Icon className={cn(iconSizes[size], config.text)} aria-hidden="true" />}
      {showLabel && <span>{config.label}</span>}
    </span>
  );
}

// For eligibility-specific badges with dot indicator
export function EligibilityBadge({ 
  status, 
  size = "md",
  dot = true 
}: { 
  status: "eligible" | "ineligible" | "potentially_eligible" | "needs_information" | "unverified";
  size?: "sm" | "md" | "lg";
  dot?: boolean;
}) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center font-heading font-medium rounded-full border",
        sizeStyles[size],
        config.bg,
        config.text,
        config.border
      )}
    >
      {dot && (
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full flex-shrink-0",
            size === "sm" && "w-1 h-1",
            size === "lg" && "w-2 h-2",
            config.text
          )}
          aria-hidden="true"
        />
      )}
      <Icon className={cn(iconSizes[size], config.text)} aria-hidden="true" />
      <span>{config.label}</span>
    </span>
  );
}

// Need to import Info icon

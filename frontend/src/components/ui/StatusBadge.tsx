"use client";

import { cn } from "@/lib/utils";

export type StatusType = 
  | "eligible" 
  | "potentially_eligible" 
  | "needs_information" 
  | "ineligible" 
  | "unverified" 
  | "pending" 
  | "processing" 
  | "completed" 
  | "error" 
  | "success";

interface StatusBadgeProps {
  status: StatusType;
  size?: "sm" | "md" | "lg";
  dot?: boolean;
  className?: string;
}

const STATUS_TYPES: StatusType[] = [
  "eligible",
  "potentially_eligible",
  "needs_information",
  "ineligible",
  "unverified",
  "pending",
  "processing",
  "completed",
  "error",
  "success",
];

/** Safely narrow an arbitrary backend status string to a StatusType. */
export function toStatusType(value: string | null | undefined): StatusType {
  if (value && (STATUS_TYPES as string[]).includes(value)) {
    return value as StatusType;
  }
  return "unverified";
}

const statusConfigs: Record<StatusType, { label: string; variant: "success" | "lime" | "warning" | "error" | "outline" }> = {
  eligible: { label: "Eligible", variant: "success" },
  potentially_eligible: { label: "Potentially Eligible", variant: "lime" },
  needs_information: { label: "Needs Information", variant: "warning" },
  ineligible: { label: "Not Eligible", variant: "error" },
  unverified: { label: "Unverified", variant: "outline" },
  pending: { label: "Pending", variant: "outline" },
  processing: { label: "Processing", variant: "lime" },
  completed: { label: "Completed", variant: "success" },
  error: { label: "Error", variant: "error" },
  success: { label: "Success", variant: "success" },
};

export function StatusBadge({ status, size = "md", dot = false, className }: StatusBadgeProps) {
  const config = statusConfigs[status] || { label: status, variant: "outline" };
  
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded-full",
        size === "sm" && "px-2 py-0.5 text-xs",
        size === "md" && "px-3 py-1 text-sm",
        size === "lg" && "px-4 py-1.5 text-base",
        className
      )}
    >
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" aria-hidden="true" />}
      {config.label}
    </span>
  );
}
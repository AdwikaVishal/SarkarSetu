"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  action?: ReactNode;
  className?: string;
}

export function SectionHeading({ title, subtitle, eyebrow, action, className }: SectionHeadingProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4", className)}>
      <div>
        {eyebrow && (
          <span className="text-xs font-medium uppercase tracking-wider text-accent-lime mb-1 block">
            {eyebrow}
          </span>
        )}
        <h2 className="font-heading font-bold text-2xl sm:text-3xl text-text-primary">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-text-muted sm:text-lg">{subtitle}</p>
        )}
      </div>
      {action && (
        <div className="flex-shrink-0 mt-4 sm:mt-0">
          {action}
        </div>
      )}
    </div>
  );
}
"use client";

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface SectionHeadingProps extends HTMLAttributes<HTMLDivElement> {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  highlight?: string;
  highlightColor?: "lime" | "purple";
  alignment?: "left" | "center" | "right";
  className?: string;
}

export function SectionHeading({
  eyebrow,
  title,
  subtitle,
  highlight,
  highlightColor = "lime",
  alignment = "left",
  className,
  children,
  ...props
}: SectionHeadingProps) {
  const highlightClass = highlightColor === "lime" 
    ? "text-accent-lime" 
    : "text-accent-purple";

  const alignments = {
    left: "text-left items-start",
    center: "text-center items-center",
    right: "text-right items-end",
  };

  return (
    <div
      className={cn("flex flex-col gap-2 max-w-4xl", alignments[alignment], className)}
      {...props}
    >
      {eyebrow && (
        <span className="font-heading text-xs font-semibold uppercase tracking-widest text-text-muted">
          {eyebrow}
        </span>
      )}
      <h2 className="font-heading text-xl font-bold tracking-tight text-text-primary sm:text-2xl">
        {title.split(highlight || "").map((part, i) => (
          <span key={i}>
            {part}
            {i < (title.split(highlight || "").length - 1) && (
              <span className={highlightClass}>{highlight}</span>
            )}
          </span>
        ))}
      </h2>
      {subtitle && (
        <p className="max-w-2xl text-sm text-text-muted leading-relaxed">
          {subtitle}
        </p>
      )}
      {children}
    </div>
  );
}
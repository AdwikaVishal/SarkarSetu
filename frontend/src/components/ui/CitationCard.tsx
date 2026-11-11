"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { type RetrievalSourceResponse } from "@/types/api";
import { ExternalLink, FileText, Building2 } from "lucide-react";

interface CitationCardProps {
  citation: RetrievalSourceResponse;
  compact?: boolean;
  showScores?: boolean;
  className?: string;
}

export function CitationCard({ citation, compact = false, showScores = false, className }: CitationCardProps) {
  if (compact) {
    return (
      <div className={cn("p-3 rounded-xl bg-bg-card border border-border", className)}>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-purple/10 flex items-center justify-center flex-shrink-0">
            <FileText className="w-4 h-4 text-accent-purple" aria-hidden="true" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm text-text-primary truncate">
              {citation.source_title || "Untitled Source"}
            </p>
            <div className="flex flex-wrap gap-2 mt-1 text-xs text-text-muted">
              {citation.issuing_authority && (
                <span className="flex items-center gap-1">
                  <Building2 className="w-3 h-3" aria-hidden="true" />
                  {citation.issuing_authority}
                </span>
              )}
              {citation.page_or_section && (
                <span>Page: {citation.page_or_section}</span>
              )}
              {showScores && citation.retrieval_score && (
                <span>Score: {citation.retrieval_score.toFixed(2)}</span>
              )}
            </div>
          </div>
          {citation.source_url && (
            <a
              href={citation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-lg text-text-muted hover:text-accent-purple hover:bg-bg-elevated transition-colors"
              aria-label="Open source"
            >
              <ExternalLink className="w-4 h-4" aria-hidden="true" />
            </a>
          )}
        </div>
        {citation.relevant_excerpt && (
          <p className="mt-2 text-sm text-text-muted line-clamp-2">{citation.relevant_excerpt}</p>
        )}
      </div>
    );
  }

  return (
    <div className={cn("p-4 rounded-xl bg-bg-card border border-border", className)}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-accent-purple/10 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-accent-purple" aria-hidden="true" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-text-primary">{citation.source_title || "Untitled Source"}</p>
          
          <div className="flex flex-wrap gap-3 mt-2 text-sm text-text-muted">
            {citation.issuing_authority && (
              <span className="flex items-center gap-1">
                <Building2 className="w-4 h-4" aria-hidden="true" />
                {citation.issuing_authority}
              </span>
            )}
            {citation.publication_date && (
              <span>Published: {new Date(citation.publication_date).toLocaleDateString("en-IN")}</span>
            )}
            {citation.page_or_section && (
              <span>Page/Section: {citation.page_or_section}</span>
            )}
            {showScores && citation.retrieval_score && (
              <span className="flex items-center gap-1">
                <span className="px-2 py-0.5 rounded-full bg-accent-lime/20 text-accent-lime text-xs font-mono">
                  {citation.retrieval_score.toFixed(3)}
                </span>
              </span>
            )}
          </div>

          {citation.relevant_excerpt && (
            <div className="mt-3 p-3 rounded-lg bg-bg-elevated border border-border/50">
              <p className="text-sm text-text-muted italic">"{citation.relevant_excerpt}"</p>
            </div>
          )}

          {citation.source_url && (
            <a
              href={citation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 mt-3 text-sm text-accent-purple hover:text-accent-purple-hover transition-colors"
            >
              <ExternalLink className="w-4 h-4" aria-hidden="true" />
              View Official Source
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

interface CitationListProps {
  citations: RetrievalSourceResponse[];
  compact?: boolean;
  showScores?: boolean;
  title?: string;
  className?: string;
}

export function CitationList({ citations, compact = false, showScores = false, title, className }: CitationListProps) {
  if (citations.length === 0) {
    return (
      <div className={cn("text-center py-8 text-text-muted", className)}>
        <p>No sources available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {title && (
        <h3 className="font-heading font-bold text-lg text-text-primary mb-3">{title}</h3>
      )}
      {citations.map((citation, index) => (
        <CitationCard
          key={`${citation.document_id || index}`}
          citation={citation}
          compact={compact}
          showScores={showScores}
        />
      ))}
    </div>
  );
}
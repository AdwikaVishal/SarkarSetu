"use client";

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { FileText, Building, Calendar, Globe } from "lucide-react";
import { RetrievalSourceResponse } from "@/types/api";

export interface CitationCardProps extends HTMLAttributes<HTMLDivElement> {
  citation: RetrievalSourceResponse;
  index?: number;
  compact?: boolean;
  showScore?: boolean;
}

export function CitationCard({ 
  citation, 
  index, 
  compact = false, 
  showScore = false,
  className,
  ...props 
}: CitationCardProps) {
  if (compact) {
    return (
      <div 
        className={cn(
          "flex items-start gap-3 p-3 rounded-xl bg-bg-card border border-border hover:border-accent-lime/50 transition-colors",
          className
        )}
        {...props}
      >
        {index !== undefined && (
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-accent-lime/10 text-accent-lime text-xs font-heading font-bold flex items-center justify-center">
            {index + 1}
          </span>
        )}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-text-primary line-clamp-1">
            {citation.source_title || "Untitled Source"}
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-text-muted">
            {citation.issuing_authority && (
              <span className="flex items-center gap-1">
                <Building className="w-3 h-3" aria-hidden="true" />
                {citation.issuing_authority}
              </span>
            )}
            {citation.page_or_section && (
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" aria-hidden="true" />
                {citation.page_or_section}
              </span>
            )}
            {citation.publication_date && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" aria-hidden="true" />
                {citation.publication_date}
              </span>
            )}
            {citation.source_url && (
              <a 
                href={citation.source_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-accent-purple hover:text-accent-purple-hover"
              >
                <Globe className="w-3 h-3" aria-hidden="true" />
                View Source
              </a>
            )}
          </div>
          {citation.relevant_excerpt && (
            <p className="mt-2 text-sm text-text-muted line-clamp-2 italic">
              &ldquo;{citation.relevant_excerpt}&rdquo;
            </p>
          )}
        </div>
        {showScore && citation.retrieval_score !== null && (
          <span className="flex-shrink-0 text-xs font-mono text-text-muted">
            {Math.round(citation.retrieval_score * 100)}%
          </span>
        )}
      </div>
    );
  }

  return (
    <div 
      className={cn(
        "p-4 rounded-xl bg-bg-card border border-border hover:border-accent-lime/50 transition-colors",
        className
      )}
      {...props}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            {index !== undefined && (
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-accent-lime/10 text-accent-lime text-xs font-heading font-bold flex items-center justify-center">
                {index + 1}
              </span>
            )}
            <h4 className="font-medium text-text-primary">
              {citation.source_title || "Untitled Source"}
            </h4>
          </div>
          
          {citation.relevant_excerpt && (
            <blockquote className="border-l-2 border-accent-lime/30 pl-3 my-3 italic text-text-muted">
              {citation.relevant_excerpt}
            </blockquote>
          )}
          
          <div className="flex flex-wrap items-center gap-3 text-sm text-text-muted">
            {citation.issuing_authority && (
              <span className="flex items-center gap-1">
                <Building className="w-4 h-4" aria-hidden="true" />
                {citation.issuing_authority}
              </span>
            )}
            {citation.source_url && (
              <a 
                href={citation.source_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-accent-purple hover:text-accent-purple-hover"
              >
                <Globe className="w-4 h-4" aria-hidden="true" />
                View Source
              </a>
            )}
            {citation.page_or_section && (
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" aria-hidden="true" />
                Section: {citation.page_or_section}
              </span>
            )}
            {citation.publication_date && (
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" aria-hidden="true" />
                Published: {citation.publication_date}
              </span>
            )}
            {citation.document_version && (
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" aria-hidden="true" />
                v{citation.document_version}
              </span>
            )}
          </div>
        </div>
        
        {showScore && citation.retrieval_score !== null && (
          <div className="flex-shrink-0 text-right">
            <span className="text-xs font-mono text-text-muted">
              Relevance: {Math.round(citation.retrieval_score * 100)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export interface CitationListProps {
  citations: RetrievalSourceResponse[];
  compact?: boolean;
  showScores?: boolean;
  maxVisible?: number;
  title?: string;
}

export function CitationList({ 
  citations, 
  compact = true, 
  showScores = false,
  maxVisible,
  title = "Sources"
}: CitationListProps) {
  if (!citations || citations.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-bg-card border border-border">
        <p className="text-text-muted text-sm">No sources available for this response.</p>
      </div>
    );
  }

  const visibleCitations = maxVisible ? citations.slice(0, maxVisible) : citations;
  const hasMore = maxVisible && citations.length > maxVisible;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-heading font-semibold text-text-primary">{title}</h4>
        <span className="text-sm text-text-muted">{citations.length} source{citations.length !== 1 ? "s" : ""}</span>
      </div>
      <div className="space-y-2">
        {visibleCitations.map((citation, index) => (
          <CitationCard 
            key={citation.document_id || index} 
            citation={citation} 
            index={index} 
            compact={compact}
            showScore={showScores}
          />
        ))}
        {hasMore && (
          <button className="w-full text-sm text-accent-purple hover:text-accent-purple-hover font-medium py-2">
            Show {citations.length - maxVisible} more source{ citations.length - maxVisible !== 1 ? "s" : "" }
          </button>
        )}
      </div>
    </div>
  );
}
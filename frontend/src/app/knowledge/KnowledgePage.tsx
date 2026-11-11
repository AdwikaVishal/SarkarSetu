"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ArrowRight } from "lucide-react";

function KnowledgePage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(null);
  const [defaultBusiness, setDefaultBusiness] = useState<any | null>(null);

  useEffect(() => {
    if (!isAuthenticated || authLoading) return;
    const load = async () => {
      try {
        const result = await api.listBusinesses();
        setSelectedBusiness(result.items?.[0]?.id ?? null);
        if (result.items?.length > 0) {
          setDefaultBusiness(result.items[0]);
        }
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load business profiles");
      }
    };
    load();
  }, [isAuthenticated, authLoading]);

  const searchKnowledge = async () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.searchKnowledge({
        query,
        limit: 10,
      });
      setResults(result.results ?? []);
      setError(null);
    } catch (err: any) {
      setError(err.detail || "Failed to search knowledge");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("en-IN", {
        day: "numeric", month: "short", year: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-bg-primary flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-lime border-t-transparent" />
        </div>
      </DashboardLayout>
    );
  }

  if (!isAuthenticated) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-bg-primary flex items-center justify-center">
          <div className="text-center p-8">
            <h2 className="font-heading font-bold text-xl text-text-primary mb-2">SarkarSetu AI</h2>
            <p className="text-text-muted">Application is ready. Redirecting to dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Compute defaultBusiness outside JSX
  let db: any | null = null;
  if (selectedBusiness) {
    // We'll fetch it inline when needed, or just use the first business
    db = defaultBusiness;
  }

  const welcomeContent = (
    <div className="mb-6">
      <p className="text-text-muted mb-4">
        Search the government knowledge base for guidance on registrations, schemes,
        compliance requirements, and more.
      </p>
    </div>
  );

  const searchContent = (
    <Card variant="outlined" padding="md" className="mb-6">
      <CardHeader>
        <CardTitle size="md">Search Knowledge Base</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Search query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Udyam registration process, GST documents, PMEGP guidelines..."
              className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
              aria-label="Search query"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Business profile (optional)
            </label>
            <select
              className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
              disabled={!selectedBusiness}
            >
              <option value="">All knowledge</option>
              {selectedBusiness ? (
                <option value={selectedBusiness}>Selected business profile</option>
              ) : null}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <Button
            variant="lime"
            size="lg"
            onClick={searchKnowledge}
            disabled={loading}
          >
            {loading ? "Searching..." : "Search"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const resultsContent = results.length > 0 ? (
    <div className="space-y-4">
      {results.map((result) => {
        const score = result.retrieval_score ? `${(result.retrieval_score * 100).toFixed(1)}%` : "N/A";
        return (
          <Card key={result.document_id} variant="outlined" padding="md" className="h-full">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle size="sm">{result.source_title || "Untitled"}</CardTitle>
                  <p className="text-xs text-text-muted">
                    {result.issuing_authority || "Government of India"}
                  </p>
                  <p className="text-xs text-text-muted">
                    {result.publication_date ? `Published: ${formatDate(result.publication_date)}` : ""}
                  </p>
                </div>
                <div>
                  <StatusBadge status="success" size="sm" className="h-6 w-6" />
                  <span className="text-xs text-text-muted">Score: {score}</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-muted line-clamp-3">
                {result.relevant_excerpt || "No excerpt available"}
              </p>
              <div className="mt-3 pt-3 border-t border-border">
                <a
                  href={result.source_url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-deep-rose hover:text-primary transition-colors"
                >
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                  View official source
                </a>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  ) : (
    <EmptyState
      icon="Search"
      title="No results found"
      description={
        query
          ? "No knowledge results match your search criteria. Try different keywords or adjust your search."
          : "Enter a search query to explore government guidance and regulations."
      }
      alignment="left"
    />
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {welcomeContent}

        {selectedBusiness ? (
          <div className="mb-6">
            <Badge variant="outline" size="sm">
              Using business profile: {selectedBusiness}
            </Badge>
          </div>
        ) : null}

        {searchContent}

        {resultsContent}

        {error && (
          <ErrorState
            title="Error"
            message={error}
            onRetry={() => setError(null)}
            alignment="left"
          />
        )}
      </div>
    </DashboardLayout>
  );
}

export default KnowledgePage;

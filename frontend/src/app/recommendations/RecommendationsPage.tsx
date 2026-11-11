"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type {
  BusinessProfileResponse,
  RecommendationDetail,
  RecommendationResponse,
} from "@/types/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { StatusBadge, toStatusType } from "@/components/ui/StatusBadge";
import { ArrowRight, Building2, ExternalLink, Search, Sparkles } from "lucide-react";

type StatusFilter = "all" | "eligible" | "potentially_eligible" | "needs_information" | "ineligible";

const STATUS_FILTERS: Array<{ value: StatusFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "eligible", label: "Eligible" },
  { value: "potentially_eligible", label: "Potentially eligible" },
  { value: "needs_information", label: "Needs information" },
  { value: "ineligible", label: "Not eligible" },
];

function RecommendationsPage() {
  const { isLoading: authLoading, isAuthenticated } = useAuth();

  const [businesses, setBusinesses] = useState<BusinessProfileResponse[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string>("");
  const [recommendations, setRecommendations] = useState<RecommendationDetail[]>([]);
  const [summary, setSummary] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const applyResponses = useCallback((items: RecommendationResponse[]) => {
    const seen = new Set<string>();
    const flattened: RecommendationDetail[] = [];
    for (const response of items) {
      for (const recommendation of response.recommendations ?? []) {
        const id = recommendation.scheme?.id;
        if (!id || seen.has(id)) continue;
        seen.add(id);
        flattened.push(recommendation);
      }
    }
    return flattened;
  }, []);

  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const result = await api.listBusinesses();
        if (cancelled) return;
        const items = result.items ?? [];
        setBusinesses(items);
        const preferred = items.find((b) => b.is_default) ?? items[0] ?? null;
        setSelectedBusiness(preferred?.id ?? "");
        setError(null);
      } catch (err: unknown) {
        if (cancelled) return;
        const detail =
          typeof err === "object" && err !== null && "detail" in err
            ? String((err as { detail?: unknown }).detail)
            : "Failed to load business profiles";
        setError(detail);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, authLoading]);

  // Load any previously generated recommendations for the selected business.
  useEffect(() => {
    if (!selectedBusiness) {
      setRecommendations([]);
      setSummary(null);
      return;
    }

    let cancelled = false;

    const loadExisting = async () => {
      try {
        const result = await api.listRecommendations(selectedBusiness);
        if (cancelled) return;
        const items = result.items ?? [];
        setRecommendations(applyResponses(items));
        setSummary(items[items.length - 1] ?? null);
        setActionError(null);
      } catch {
        if (!cancelled) {
          setRecommendations([]);
          setSummary(null);
        }
      }
    };

    loadExisting();
    return () => {
      cancelled = true;
    };
  }, [selectedBusiness, applyResponses]);

  const generateRecommendations = async () => {
    if (!selectedBusiness) {
      setActionError("Please select a business profile first.");
      return;
    }

    setGenerating(true);
    setActionError(null);

    try {
      const result = await api.getRecommendations({ business_profile_id: selectedBusiness });
      setRecommendations(result.recommendations ?? []);
      setSummary(result);
    } catch (err: unknown) {
      const detail =
        typeof err === "object" && err !== null && "detail" in err
          ? String((err as { detail?: unknown }).detail)
          : "Failed to generate recommendations";
      setActionError(detail);
    } finally {
      setGenerating(false);
    }
  };

  const defaultBusiness = useMemo(
    () => businesses.find((b) => b.id === selectedBusiness) ?? null,
    [businesses, selectedBusiness]
  );

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return recommendations.filter((rec) => {
      if (statusFilter !== "all" && rec.eligibility_status !== statusFilter) return false;
      if (!query) return true;
      return (
        rec.scheme.name.toLowerCase().includes(query) ||
        rec.scheme.ministry.toLowerCase().includes(query) ||
        rec.scheme.category.toLowerCase().includes(query)
      );
    });
  }, [recommendations, search, statusFilter]);

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </DashboardLayout>
    );
  }

  if (!isAuthenticated) {
    return (
      <DashboardLayout>
        <EmptyState
          icon={Building2}
          title="Sign-in required"
          description="Your session is not ready yet. Reload the page to continue."
        />
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <ErrorState
          title="Could not load business profiles"
          message={error}
          onRetry={() => window.location.reload()}
        />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="font-heading text-2xl font-bold text-text-primary sm:text-3xl">
            Recommendations
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Personalised scheme matches based on your business profile.
          </p>
        </div>

        {businesses.length === 0 ? (
          <div className="space-y-4">
            <EmptyState
              icon={Building2}
              title="No business profile yet"
              description="Create a business profile to receive personalised scheme recommendations."
              alignment="left"
            />
            <Button variant="lime" size="md" asChild>
              <Link to="/profile?create=true">Create business profile</Link>
            </Button>
          </div>
        ) : (
          <>
            <Card variant="outlined" padding="md">
              <CardHeader>
                <CardTitle size="md">Business profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <label className="block">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-text-muted">
                    Select business
                  </span>
                  <select
                    value={selectedBusiness}
                    onChange={(event) => setSelectedBusiness(event.target.value)}
                    className="w-full rounded-xl border border-border bg-bg-primary/50 px-3 py-2 text-sm text-text-primary focus:border-transparent focus:outline-none focus:ring-2 focus:ring-accent-lime/50"
                  >
                    {businesses.map((business) => (
                      <option key={business.id} value={business.id}>
                        {business.business_name} ({business.business_structure})
                      </option>
                    ))}
                  </select>
                </label>

                {defaultBusiness && (
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="lime" size="sm">
                      {defaultBusiness.business_structure}
                    </Badge>
                    <Badge variant="purple" size="sm">
                      {defaultBusiness.business_stage}
                    </Badge>
                    <span className="text-sm text-text-muted">
                      {[defaultBusiness.city, defaultBusiness.state, defaultBusiness.district]
                        .filter(Boolean)
                        .join(", ")}
                    </span>
                  </div>
                )}

                <Button
                  variant="lime"
                  size="md"
                  onClick={generateRecommendations}
                  disabled={!selectedBusiness || generating}
                >
                  {generating ? "Evaluating schemes..." : "Generate recommendations"}
                </Button>
              </CardContent>
            </Card>

            {actionError && (
              <ErrorState
                title="Could not generate recommendations"
                message={actionError}
                onRetry={generateRecommendations}
                alignment="left"
              />
            )}

            {summary && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { label: "Evaluated", value: summary.total_schemes_evaluated },
                  { label: "Eligible", value: summary.eligible_count },
                  { label: "Potentially eligible", value: summary.potentially_eligible_count },
                  { label: "Needs information", value: summary.needs_info_count },
                ].map((stat) => (
                  <Card key={stat.label} variant="outlined" padding="md">
                    <p className="font-heading text-2xl font-bold text-text-primary">
                      {stat.value}
                    </p>
                    <p className="text-xs text-text-muted">{stat.label}</p>
                  </Card>
                ))}
              </div>
            )}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="relative w-full sm:max-w-xs">
                <Search
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted"
                  aria-hidden="true"
                />
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search schemes..."
                  aria-label="Search schemes"
                  className="w-full rounded-full border border-border bg-bg-card py-2 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-muted focus:border-transparent focus:outline-none focus:ring-2 focus:ring-accent-lime/50"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {STATUS_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    type="button"
                    onClick={() => setStatusFilter(filter.value)}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                      statusFilter === filter.value
                        ? "bg-text-primary text-bg-primary"
                        : "border border-border text-text-muted hover:bg-bg-card"
                    }`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>

            {recommendations.length === 0 ? (
              <EmptyState
                icon={Sparkles}
                title="No recommendations yet"
                description="Generate recommendations to see personalised scheme matches for this business."
                alignment="left"
              />
            ) : filtered.length === 0 ? (
              <EmptyState
                icon={Search}
                title="No matching schemes"
                description="Try adjusting your search or eligibility filter."
                alignment="left"
              />
            ) : (
              <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                {filtered.map((rec) => {
                  const sources = rec.official_sources ?? [];
                  return (
                    <Card key={rec.scheme.id} variant="outlined" padding="md" className="h-full">
                      <CardHeader className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <CardTitle size="md">{rec.scheme.name}</CardTitle>
                          <p className="mt-1 text-xs text-text-muted">
                            {rec.scheme.ministry} · {rec.scheme.category}
                          </p>
                        </div>
                        <StatusBadge status={toStatusType(rec.eligibility_status)} size="sm" dot />
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-sm text-text-muted">{rec.explanation}</p>

                        {rec.matched_rules.length > 0 && (
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Matched conditions
                            </p>
                            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-text-primary">
                              {rec.matched_rules.map((rule, index) => (
                                <li key={`matched-${index}`}>{rule}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {rec.failed_rules.length > 0 && (
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Unmet conditions
                            </p>
                            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-error">
                              {rec.failed_rules.map((rule, index) => (
                                <li key={`failed-${index}`}>{rule}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {rec.required_documents.length > 0 && (
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Required documents
                            </p>
                            <div className="mt-1 flex flex-wrap gap-2">
                              {rec.required_documents.map((doc, index) => (
                                <Badge key={`doc-${index}`} variant="outline" size="sm">
                                  {doc}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {sources.length > 0 && (
                          <div>
                            <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
                              Official sources
                            </p>
                            <ul className="mt-1 space-y-1">
                              {sources.map((source, index) => (
                                <li key={`source-${index}`}>
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-sm text-deep-rose hover:underline"
                                  >
                                    {source.title || source.url}
                                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                                  </a>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          <Button variant="outline" size="sm" asChild>
                            <Link
                              to={`/eligibility?business=${selectedBusiness}&scheme=${rec.scheme.id}`}
                            >
                              Check eligibility <ArrowRight className="h-3.5 w-3.5" />
                            </Link>
                          </Button>
                          {rec.scheme.official_url && (
                            <a
                              href={rec.scheme.official_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-deep-rose hover:underline"
                            >
                              Scheme details
                            </a>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            <p className="text-xs text-text-muted">
              Eligibility guidance is generated from published rules and is not an official
              government approval. Always verify requirements with the issuing authority.
            </p>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

export default RecommendationsPage;

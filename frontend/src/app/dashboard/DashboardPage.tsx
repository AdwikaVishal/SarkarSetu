"use client";

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type {
  BusinessProfileResponse,
  ConversationResponse,
  DocumentResponse,
  EligibilityAssessmentResponse,
  RecommendationDetail,
  RoadmapResponse,
} from "@/types/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { cn } from "@/lib/utils";
import {
  ArrowRight,
  Building2,
  MessageSquare,
  Target,
  FolderOpen,
  FileText,
  ClipboardCheck,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

interface DashboardData {
  businesses: BusinessProfileResponse[];
  conversations: ConversationResponse[];
  roadmaps: RoadmapResponse[];
  documents: DocumentResponse[];
  assessments: EligibilityAssessmentResponse[];
  recommendations: RecommendationDetail[];
}

const EMPTY_DATA: DashboardData = {
  businesses: [],
  conversations: [],
  roadmaps: [],
  documents: [],
  assessments: [],
  recommendations: [],
};

type BadgeVariant = "success" | "warning" | "error" | "outline" | "lime" | "purple";

const ASSESSMENT_BADGES: Record<string, { label: string; variant: BadgeVariant }> = {
  eligible: { label: "Eligible", variant: "success" },
  potentially_eligible: { label: "Potentially eligible", variant: "lime" },
  needs_information: { label: "Needs information", variant: "warning" },
  ineligible: { label: "Not eligible", variant: "error" },
  unverified: { label: "Unverified", variant: "outline" },
};

function relativeTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "Just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function formatBytes(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) return "0 KB";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function calculateCompletion(business: BusinessProfileResponse): number {
  const requiredFields: Array<keyof BusinessProfileResponse> = [
    "business_name",
    "business_type",
    "industry",
    "state",
    "district",
    "business_structure",
    "business_stage",
  ];
  const provided = requiredFields.filter((field) => Boolean(business[field])).length;
  return Math.round((provided / requiredFields.length) * 100);
}

function DashboardPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const [data, setData] = useState<DashboardData>(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [failedSections, setFailedSections] = useState<string[]>([]);

  const loadData = useCallback(async () => {
    if (!isAuthenticated || authLoading) return;

    setLoading(true);
    setError(null);

    const [businessesResult, conversationsResult, roadmapsResult, documentsResult] =
      await Promise.allSettled([
        api.listBusinesses(),
        api.listConversations(0, 10),
        api.listRoadmaps(),
        api.listDocuments(),
      ]);

    const failed: string[] = [];

    const businesses =
      businessesResult.status === "fulfilled" ? businessesResult.value.items ?? [] : [];
    if (businessesResult.status === "rejected") failed.push("business profiles");

    const conversations =
      conversationsResult.status === "fulfilled" ? conversationsResult.value ?? [] : [];
    if (conversationsResult.status === "rejected") failed.push("conversations");

    const roadmaps =
      roadmapsResult.status === "fulfilled" ? roadmapsResult.value.roadmaps ?? [] : [];
    if (roadmapsResult.status === "rejected") failed.push("roadmaps");

    const documents =
      documentsResult.status === "fulfilled" ? documentsResult.value.items ?? [] : [];
    if (documentsResult.status === "rejected") failed.push("documents");

    const defaultBusiness =
      businesses.find((business) => business.is_default) ?? businesses[0] ?? null;

    let assessments: EligibilityAssessmentResponse[] = [];
    let recommendations: RecommendationDetail[] = [];

    if (defaultBusiness) {
      const [assessmentsResult, recommendationsResult] = await Promise.allSettled([
        api.listBusinessAssessments(defaultBusiness.id),
        api.listRecommendations(defaultBusiness.id),
      ]);

      if (assessmentsResult.status === "fulfilled") {
        assessments = [...(assessmentsResult.value ?? [])].sort(
          (a, b) => new Date(b.evaluated_at).getTime() - new Date(a.evaluated_at).getTime()
        );
      } else {
        failed.push("eligibility assessments");
      }

      if (recommendationsResult.status === "fulfilled") {
        const seen = new Set<string>();
        recommendations = (recommendationsResult.value.items ?? [])
          .flatMap((response) => response.recommendations ?? [])
          .filter((recommendation) => {
            const id = recommendation.scheme?.id;
            if (!id || seen.has(id)) return false;
            seen.add(id);
            return true;
          });
      } else {
        failed.push("recommendations");
      }
    }

    setData({
      businesses,
      conversations,
      roadmaps,
      documents,
      assessments,
      recommendations,
    });
    setFailedSections(failed);

    if (failed.length >= 4) {
      setError("We could not reach the SarkarSetu service. Please try again.");
    }

    setLoading(false);
  }, [isAuthenticated, authLoading]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const defaultBusiness =
    data.businesses.find((business) => business.is_default) ?? data.businesses[0] ?? null;

  const totalTasks = data.roadmaps.reduce((sum, roadmap) => sum + roadmap.total_tasks, 0);
  const completedTasks = data.roadmaps.reduce(
    (sum, roadmap) => sum + roadmap.completed_tasks,
    0
  );
  const overallProgress = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const metrics = [
    {
      label: "Business profiles",
      value: data.businesses.length,
      icon: Building2,
      accent: "bg-light-lavender/40 text-text-primary",
    },
    {
      label: "Active conversations",
      value: data.conversations.length,
      icon: MessageSquare,
      accent: "bg-soft-pink/30 text-text-primary",
    },
    {
      label: "Roadmaps in progress",
      value: data.roadmaps.filter((roadmap) => roadmap.status !== "completed").length,
      icon: Target,
      accent: "bg-soft-green/40 text-text-primary",
    },
    {
      label: "Uploaded documents",
      value: data.documents.length,
      icon: FolderOpen,
      accent: "bg-soft-yellow/40 text-text-primary",
    },
  ];

  if (authLoading || (loading && !error && data.businesses.length === 0)) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <SkeletonCard />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <SkeletonCard />
        </div>
      </DashboardLayout>
    );
  }

  if (error && failedSections.length >= 4) {
    return (
      <DashboardLayout>
        <ErrorState
          title="Dashboard unavailable"
          message={error}
          onRetry={loadData}
        />
      </DashboardLayout>
    );
  }

  const userName = user?.full_name || defaultBusiness?.business_name || "Entrepreneur";

  const welcomeContent = (
    <div className="flex flex-col gap-1">
      <p className="text-sm font-medium text-text-muted">Welcome back</p>
      <h1 className="font-heading text-2xl font-bold text-text-primary sm:text-3xl">
        {userName}
      </h1>
      <p className="text-sm text-text-muted">
        Here is what is happening with your SarkarSetu workspace.
      </p>
      {failedSections.length > 0 && (
        <p className="mt-2 text-xs text-warning">
          Some sections could not load: {failedSections.join(", ")}.{" "}
          <button
            type="button"
            onClick={loadData}
            className="font-medium underline underline-offset-2"
          >
            Retry
          </button>
        </p>
      )}
    </div>
  );

  const metricsGrid = (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <Card key={metric.label} variant="outlined" padding="md" className="h-full">
            <CardContent className="flex items-center gap-4">
              <span
                className={cn(
                  "flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl",
                  metric.accent
                )}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <div className="min-w-0">
                <p className="font-heading text-2xl font-bold leading-none text-text-primary">
                  {metric.value}
                </p>
                <p className="mt-1 truncate text-sm text-text-muted">{metric.label}</p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );

  const mainContent = (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      {/* Business overview */}
      <Card variant="outlined" padding="md" className="h-full lg:col-span-12">
        <CardHeader className="flex items-start justify-between gap-4">
          <div>
            <CardTitle size="md">Business overview</CardTitle>
            <p className="mt-1 text-sm text-text-muted">
              The profile used to personalise your recommendations.
            </p>
          </div>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/profile" className="flex items-center gap-1 whitespace-nowrap">
              Manage <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {defaultBusiness ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="lime" size="sm">
                  {defaultBusiness.business_structure}
                </Badge>
                <Badge variant="purple" size="sm">
                  {defaultBusiness.business_stage}
                </Badge>
                {defaultBusiness.is_default && (
                  <Badge variant="outline" size="sm">
                    Default profile
                  </Badge>
                )}
              </div>
              <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
                {[
                  ["Business name", defaultBusiness.business_name],
                  ["Industry", defaultBusiness.industry],
                  [
                    "Location",
                    [defaultBusiness.city, defaultBusiness.state].filter(Boolean).join(", "),
                  ],
                  ["Business type", defaultBusiness.business_type],
                ].map(([label, value]) => (
                  <div key={label} className="min-w-0">
                    <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                      {label}
                    </dt>
                    <dd className="truncate text-sm font-medium text-text-primary">
                      {value || "Not provided"}
                    </dd>
                  </div>
                ))}
              </dl>
              <div>
                <div className="mb-1.5 flex items-center justify-between text-sm">
                  <span className="text-text-muted">Profile completeness</span>
                  <span className="font-medium text-text-primary">
                    {calculateCompletion(defaultBusiness)}%
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-bg-dark/40">
                  <div
                    className="h-full rounded-full bg-deep-rose"
                    style={{ width: `${calculateCompletion(defaultBusiness)}%` }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Building2}
              title="No business profile yet"
              description="Create a business profile to unlock personalised schemes and roadmaps."
              alignment="left"
              className="py-6"
            />
          )}
          {!defaultBusiness && (
            <Button variant="lime" size="md" className="mt-2" asChild>
              <Link to="/profile?create=true">Create business profile</Link>
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Roadmap progress */}
      <Card variant="outlined" padding="md" className="h-full lg:col-span-6">
        <CardHeader className="flex items-start justify-between gap-4">
          <div>
            <CardTitle size="md">Roadmap progress</CardTitle>
            <p className="mt-1 text-sm text-text-muted">
              {completedTasks} of {totalTasks} tasks completed
            </p>
          </div>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/roadmap" className="flex items-center gap-1 whitespace-nowrap">
              View <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {data.roadmaps.length > 0 ? (
            <div className="space-y-4">
              <div>
                <div className="mb-1.5 flex items-center justify-between text-sm">
                  <span className="text-text-muted">Overall progress</span>
                  <span className="font-medium text-text-primary">{overallProgress}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-bg-dark/40">
                  <div
                    className="h-full rounded-full bg-accent-lime"
                    style={{ width: `${overallProgress}%` }}
                  />
                </div>
              </div>
              <ul className="space-y-3">
                {data.roadmaps.slice(0, 3).map((roadmap) => (
                  <li key={roadmap.id}>
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className="min-w-0 truncate font-medium text-text-primary">
                        {roadmap.title}
                      </span>
                      <span className="flex-shrink-0 text-text-muted">
                        {roadmap.progress_percentage}%
                      </span>
                    </div>
                    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-bg-dark/30">
                      <div
                        className="h-full rounded-full bg-accent-lime"
                        style={{ width: `${roadmap.progress_percentage}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState
              icon={Target}
              title="No roadmaps yet"
              description="Generate a roadmap to track your compliance steps."
              alignment="left"
              className="py-6"
            />
          )}
        </CardContent>
      </Card>

      {/* Recent conversations */}
      <Card variant="outlined" padding="md" className="h-full lg:col-span-6">
        <CardHeader className="flex items-start justify-between gap-4">
          <CardTitle size="md">Recent conversations</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/assistant" className="flex items-center gap-1 whitespace-nowrap">
              Open <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {data.conversations.length > 0 ? (
            <ul className="divide-y divide-border/70">
              {data.conversations.slice(0, 4).map((conversation) => (
                <li key={conversation.id}>
                  <Link
                    to={`/assistant?conversation=${conversation.id}`}
                    className="flex items-center gap-3 py-3 transition-colors hover:text-deep-rose"
                  >
                    <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-soft-pink/25">
                      <MessageSquare className="h-4 w-4 text-deep-rose" aria-hidden="true" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-text-primary">
                        {conversation.title || "Untitled conversation"}
                      </span>
                      <span className="block text-xs text-text-muted">
                        {relativeTime(conversation.updated_at)}
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={MessageSquare}
              title="No conversations yet"
              description="Ask the assistant about registrations, schemes, or compliance."
              alignment="left"
              className="py-6"
            />
          )}
        </CardContent>
      </Card>

      {/* Eligibility assessments */}
      <Card variant="outlined" padding="md" className="h-full lg:col-span-6">
        <CardHeader className="flex items-start justify-between gap-4">
          <CardTitle size="md">Eligibility assessments</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/eligibility" className="flex items-center gap-1 whitespace-nowrap">
              Check <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {data.assessments.length > 0 ? (
            <ul className="divide-y divide-border/70">
              {data.assessments.slice(0, 4).map((assessment) => {
                const badge = ASSESSMENT_BADGES[assessment.assessment_status] ?? {
                  label: assessment.assessment_status,
                  variant: "outline" as const,
                };
                return (
                  <li
                    key={assessment.assessment_id}
                    className="flex items-center justify-between gap-3 py-3"
                  >
                    <span className="flex min-w-0 items-center gap-3">
                      <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-soft-green/35">
                        <ClipboardCheck className="h-4 w-4 text-text-primary" aria-hidden="true" />
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium text-text-primary">
                          {assessment.scheme_name}
                        </span>
                        <span className="block text-xs text-text-muted">
                          {relativeTime(assessment.evaluated_at)}
                        </span>
                      </span>
                    </span>
                    <Badge variant={badge.variant} size="sm" dot>
                      {badge.label}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          ) : (
            <EmptyState
              icon={ClipboardCheck}
              title="No assessments yet"
              description="Run an eligibility check to see which schemes fit your business."
              alignment="left"
              className="py-6"
            />
          )}
        </CardContent>
      </Card>

      {/* Recent documents */}
      <Card variant="outlined" padding="md" className="h-full lg:col-span-6">
        <CardHeader className="flex items-start justify-between gap-4">
          <CardTitle size="md">Recent documents</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/documents" className="flex items-center gap-1 whitespace-nowrap">
              View all <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {data.documents.length > 0 ? (
            <ul className="divide-y divide-border/70">
              {data.documents.slice(0, 4).map((document) => (
                <li key={document.id} className="flex items-center gap-3 py-3">
                  <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-soft-yellow/30">
                    <FileText className="h-4 w-4 text-text-primary" aria-hidden="true" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-text-primary">
                      {document.original_filename}
                    </span>
                    <span className="block text-xs text-text-muted">
                      {formatBytes(document.file_size)} · {relativeTime(document.created_at)}
                    </span>
                  </span>
                  <Badge
                    variant={
                      document.processing_status === "completed"
                        ? "success"
                        : document.processing_status === "error" ||
                          document.processing_status === "failed"
                        ? "error"
                        : "outline"
                    }
                    size="sm"
                  >
                    {document.processing_status}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={FolderOpen}
              title="No documents yet"
              description="Upload documents to check them against scheme requirements."
              alignment="left"
              className="py-6"
            />
          )}
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card variant="outlined" padding="md" className="h-full lg:col-span-6">
        <CardHeader className="flex items-start justify-between gap-4">
          <CardTitle size="md">Recommended schemes</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/schemes" className="flex items-center gap-1 whitespace-nowrap">
              Explore <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {data.recommendations.length > 0 ? (
            <ul className="divide-y divide-border/70">
              {data.recommendations.slice(0, 4).map((recommendation) => {
                const badge = ASSESSMENT_BADGES[recommendation.eligibility_status] ?? {
                  label: recommendation.eligibility_status,
                  variant: "outline" as const,
                };
                return (
                  <li
                    key={recommendation.scheme.id}
                    className="flex items-start justify-between gap-3 py-3"
                  >
                    <span className="flex min-w-0 items-start gap-3">
                      <span className="mt-0.5 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-light-lavender/40">
                        <CheckCircle2 className="h-4 w-4 text-text-primary" aria-hidden="true" />
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium text-text-primary">
                          {recommendation.scheme.name}
                        </span>
                        <span className="block truncate text-xs text-text-muted">
                          {recommendation.scheme.ministry}
                        </span>
                      </span>
                    </span>
                    <Badge variant={badge.variant} size="sm">
                      {badge.label}
                    </Badge>
                  </li>
                );
              })}
            </ul>
          ) : (
            <EmptyState
              icon={Sparkles}
              title="No recommendations yet"
              description={
                defaultBusiness
                  ? "Recommendations will appear once schemes are evaluated for your profile."
                  : "Create a business profile to receive scheme recommendations."
              }
              alignment="left"
              className="py-6"
            />
          )}
        </CardContent>
      </Card>
    </div>
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {welcomeContent}
        {metricsGrid}
        {mainContent}
      </div>
    </DashboardLayout>
  );
}

export default DashboardPage;

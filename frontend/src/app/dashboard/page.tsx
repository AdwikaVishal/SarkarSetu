"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import {
  api,
  type BusinessProfileResponse,
  type ConversationResponse,
  type DocumentResponse,
  type EligibilityAssessmentResponse,
  type RecommendationDetail,
  type RoadmapResponse,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  FolderOpen,
  MessageSquare,
  Sparkles,
  Target,
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

const ASSESSMENT_BADGES: Record<
  string,
  { label: string; variant: "success" | "lime" | "warning" | "error" | "outline" }
> = {
  eligible: { label: "Eligible", variant: "success" },
  potentially_eligible: { label: "Potentially eligible", variant: "lime" },
  needs_info: { label: "Needs information", variant: "warning" },
  ineligible: { label: "Not eligible", variant: "error" },
  pending: { label: "Pending", variant: "outline" },
  unverified: { label: "Unverified", variant: "outline" },
  unknown: { label: "Unknown", variant: "outline" },
};

function formatBytes(bytes: number) {
  if (!bytes) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function relativeTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const diff = Date.now() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function businessCompletion(business: BusinessProfileResponse) {
  const fields = [
    business.business_name,
    business.business_type,
    business.industry,
    business.state,
    business.district,
    business.business_structure,
    business.business_stage,
    business.city,
    business.pincode,
    business.annual_turnover,
    business.employee_count,
    business.gstin,
  ];
  const filled = fields.filter(
    (field) => field !== null && field !== undefined && field !== ""
  ).length;
  return Math.round((filled / fields.length) * 100);
}

function DashboardPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  const [data, setData] = useState<DashboardData>(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [failedSections, setFailedSections] = useState<string[]>([]);

  const loadDashboard = useCallback(async () => {
    if (!user || authLoading) return;

    setLoading(true);
    setError(null);

    const failed: string[] = [];

    const [businessesResult, conversationsResult, roadmapsResult, documentsResult] =
      await Promise.allSettled([
        api.listBusinesses(),
        api.listConversations(0, 10),
        api.listRoadmaps(),
        api.listDocuments(),
      ]);

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

    const defaultBusiness = businesses.find((business) => business.is_default) ?? businesses[0];

    let assessments: EligibilityAssessmentResponse[] = [];
    let recommendations: RecommendationDetail[] = [];

    if (defaultBusiness) {
      const [assessmentsResult, recommendationsResult] = await Promise.allSettled([
        api.listBusinessAssessments(defaultBusiness.id),
        api.listRecommendations(defaultBusiness.id),
      ]);

      if (assessmentsResult.status === "fulfilled") {
        assessments = [...(assessmentsResult.value ?? [])].sort(
          (a, b) =>
            new Date(b.evaluated_at).getTime() - new Date(a.evaluated_at).getTime()
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

    if (failed.length === 4) {
      setError("We could not reach the SarkarSetu service. Please try again.");
    }

    setLoading(false);
  }, [user, authLoading]);

  useEffect(() => {
    // Data fetching intentionally updates loading state when auth resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDashboard();
  }, [loadDashboard]);

  const defaultBusiness =
    data.businesses.find((business) => business.is_default) ?? data.businesses[0] ?? null;

  const totalTasks = data.roadmaps.reduce((sum, roadmap) => sum + roadmap.total_tasks, 0);
  const completedTasks = data.roadmaps.reduce(
    (sum, roadmap) => sum + roadmap.completed_tasks,
    0
  );
  const overallProgress = totalTasks
    ? Math.round((completedTasks / totalTasks) * 100)
    : 0;

  if (loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6" aria-busy="true" aria-label="Loading dashboard">
          <div className="h-9 w-64 animate-pulse rounded-lg bg-bg-dark/20" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map((item) => (
              <SkeletonCard key={item} />
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <SkeletonCard />
            </div>
            <div className="lg:col-span-5">
              <SkeletonCard />
            </div>
            <div className="lg:col-span-6">
              <SkeletonCard />
            </div>
            <div className="lg:col-span-6">
              <SkeletonCard />
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <ErrorState
          title="Dashboard unavailable"
          message={error}
          onRetry={loadDashboard}
          alignment="center"
        />
      </DashboardLayout>
    );
  }

  const metrics = [
    {
      label: "Business profiles",
      value: data.businesses.length,
      icon: Building2,
      accent: "bg-light-lavender/40 text-text-primary",
    },
    {
      label: "Conversations",
      value: data.conversations.length,
      icon: MessageSquare,
      accent: "bg-soft-pink/30 text-text-primary",
    },
    {
      label: "Active roadmaps",
      value: data.roadmaps.filter((roadmap) => roadmap.status !== "completed").length,
      icon: Target,
      accent: "bg-soft-green/40 text-text-primary",
    },
    {
      label: "Documents",
      value: data.documents.length,
      icon: FolderOpen,
      accent: "bg-soft-yellow/40 text-text-primary",
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <h1 className="font-heading text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
              Welcome back, {defaultBusiness?.business_name || user?.full_name || "there"}
            </h1>
            <p className="mt-1 text-sm text-text-muted sm:text-base">
              Here is an overview of your business compliance journey.
            </p>
          </div>
          <Button variant="lime" size="md" leftIcon={<Sparkles className="h-4 w-4" />} asChild>
            <Link href="/assistant">Ask the assistant</Link>
          </Button>
        </div>

        {failedSections.length > 0 && failedSections.length < 4 && (
          <div className="flex flex-col gap-3 rounded-xl border border-warning/30 bg-warning/5 p-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-text-primary">
              Some sections could not be loaded: {failedSections.join(", ")}.
            </p>
            <Button variant="outline" size="sm" onClick={loadDashboard}>
              Retry
            </Button>
          </div>
        )}

        {/* Metrics */}
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

        {/* Main grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Business overview */}
          <Card variant="outlined" padding="md" className="h-full lg:col-span-7">
            <CardHeader className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <CardTitle size="md">Business overview</CardTitle>
                <p className="mt-1 text-sm text-text-muted">
                  The profile used to personalise your recommendations.
                </p>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/profile" className="flex items-center gap-1 whitespace-nowrap">
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
                      ["Location", [defaultBusiness.city, defaultBusiness.state].filter(Boolean).join(", ")],
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
                        {businessCompletion(defaultBusiness)}%
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-bg-dark/40">
                      <div
                        className="h-full rounded-full bg-deep-rose"
                        style={{ width: `${businessCompletion(defaultBusiness)}%` }}
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
                  <Link href="/profile?create=true">Create business profile</Link>
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Roadmap progress */}
          <Card variant="outlined" padding="md" className="h-full lg:col-span-5">
            <CardHeader className="flex items-start justify-between gap-4">
              <div>
                <CardTitle size="md">Roadmap progress</CardTitle>
                <p className="mt-1 text-sm text-text-muted">
                  {completedTasks} of {totalTasks} tasks completed
                </p>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/roadmap" className="flex items-center gap-1 whitespace-nowrap">
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
                <Link href="/assistant" className="flex items-center gap-1 whitespace-nowrap">
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
                        href={`/assistant?conversation=${conversation.id}`}
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
                <Link href="/eligibility" className="flex items-center gap-1 whitespace-nowrap">
                  Check <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              {data.assessments.length > 0 ? (
                <ul className="divide-y divide-border/70">
                  {data.assessments.slice(0, 4).map((assessment) => {
                    const badge =
                      ASSESSMENT_BADGES[assessment.assessment_status] ?? {
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
                <Link href="/documents" className="flex items-center gap-1 whitespace-nowrap">
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
                <Link href="/schemes" className="flex items-center gap-1 whitespace-nowrap">
                  Explore <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              {data.recommendations.length > 0 ? (
                <ul className="divide-y divide-border/70">
                  {data.recommendations.slice(0, 4).map((recommendation) => {
                    const badge =
                      ASSESSMENT_BADGES[recommendation.eligibility_status] ?? {
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
      </div>
    </DashboardLayout>
  );
}

export default function DashboardPage() {
  return <DashboardPageContent />;
}

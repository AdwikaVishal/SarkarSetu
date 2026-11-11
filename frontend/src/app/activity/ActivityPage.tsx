"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { BusinessProfileResponse } from "@/types/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ArrowRight, Clock } from "lucide-react";

function ActivityPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  const [activities, setActivities] = useState<any[]>([]);
  const [businesses, setBusinesses] = useState<BusinessProfileResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || authLoading) return;
    const load = async () => {
      try {
        const result = await api.listBusinesses();
        setBusinesses(result.items ?? []);
        setError(null);
      } catch (err: unknown) {
        const detail =
          typeof err === "object" && err !== null && "detail" in err
            ? String((err as { detail?: unknown }).detail)
            : "Failed to load business profiles";
        setError(detail);
      }
    };
    load();
  }, [isAuthenticated, authLoading]);

  useEffect(() => {
    if (!isAuthenticated || authLoading) return;
    const defaultBusiness = businesses.find((b) => b.is_default) ?? businesses[0] ?? null;
    if (!defaultBusiness) return;

    let cancelled = false;

    const load = async () => {
      try {
        const [assessmentsResult, roadmapsResult] = await Promise.allSettled([
          api.listBusinessAssessments(defaultBusiness.id),
          api.listRoadmaps(defaultBusiness.id),
        ]);
        if (cancelled) return;

        const allActivities: any[] = [];
        if (assessmentsResult.status === "fulfilled" && assessmentsResult.value) {
          const assessments = [...assessmentsResult.value];
          assessments.forEach((assessment) => {
            allActivities.push({
              id: `assessment-${assessment.assessment_id}`,
              type: "eligibility_assessment",
              title: `Eligibility assessment: ${assessment.scheme_name}`,
              description: `Assessed eligibility for ${assessment.scheme_name}`,
              timestamp: assessment.evaluated_at,
              status: assessment.assessment_status,
            });
          });
        }
        if (roadmapsResult.status === "fulfilled" && roadmapsResult.value) {
          const roadmaps = [...roadmapsResult.value.roadmaps];
          roadmaps.forEach((roadmap) => {
            allActivities.push({
              id: `roadmap-${roadmap.id}`,
              type: "roadmap_generation",
              title: `Roadmap generated: ${roadmap.title}`,
              description: `Roadmap for ${roadmap.service_type} with ${roadmap.total_tasks} tasks`,
              timestamp: roadmap.created_at,
              status: roadmap.status,
            });
          });
        }
        allActivities.sort((a, b) => {
          const dateA = new Date(a.timestamp).getTime();
          const dateB = new Date(b.timestamp).getTime();
          return dateB - dateA;
        });
        if (!cancelled) {
          setActivities(allActivities);
          setError(null);
        }
      } catch (err: unknown) {
        if (cancelled) return;
        const detail =
          typeof err === "object" && err !== null && "detail" in err
            ? String((err as { detail?: unknown }).detail)
            : "Failed to load activity history";
        setError(detail);
        setActivities([]);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, authLoading, businesses]);

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return timestamp;
    }
  };

  const activityStatusBadges: Record<string, { label: string; variant: "success" | "lime" | "warning" | "error" | "outline" }> = {
    eligible: { label: "Eligible", variant: "success" },
    potentially_eligible: { label: "Potentially Eligible", variant: "lime" },
    needs_information: { label: "Needs Information", variant: "warning" },
    ineligible: { label: "Not Eligible", variant: "error" },
    active: { label: "Active", variant: "lime" },
    completed: { label: "Completed", variant: "success" },
    draft: { label: "Draft", variant: "outline" },
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

  const welcomeContent = (
    <div className="mb-6">
      <p className="text-text-muted mb-4">
        View your activity history - business profile changes, assessments, roadmaps and more.
      </p>
    </div>
  );

  const activitiesContent = activities.length > 0 ? (
    <div className="space-y-3">
      {activities.map((activity) => (
        <Card key={activity.id} variant="outlined" padding="md" className="h-full">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle size="md" className="font-medium text-text-primary">
                  {activity.title}
                </CardTitle>
                {activity.description && (
                  <p className="text-sm text-text-muted line-clamp-2">
                    {activity.description}
                  </p>
                )}
              </div>
              <div>
                <StatusBadge status={activity.status || "active"} size="sm" />
                <span className="text-xs text-text-muted">
                  {formatTimestamp(activity.timestamp)}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-x-3 gap-y-2 text-sm">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">Type</dt>
                <dd>
                  <span className="text-text-muted capitalize">
                    {activity.type?.replace(/_/g, " ") || "Activity"}
                  </span>
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      ))}
    </div>
  ) : (
    <EmptyState
      icon={Clock}
      title="No activity yet"
      description="Activity will appear here as you use SarkarSetu AI."
      alignment="left"
    />
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {welcomeContent}
        {activitiesContent}
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

export default ActivityPage;
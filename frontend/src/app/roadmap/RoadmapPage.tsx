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
import { Link } from "react-router-dom";

interface RoadmapSummary {
  id: string;
  title: string;
  service_type: string;
  status: string;
  progress_percentage: number;
  total_tasks: number;
  completed_tasks: number;
}

function RoadmapPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // State
  const [roadmaps, setRoadmaps] = useState<RoadmapSummary[]>([]);
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load businesses
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    const load = async () => {
      try {
        const result = await api.listBusinesses();
        setBusinesses(result.items ?? []);
        if (result.items?.length > 0) {
          setSelectedBusiness(result.items[0].id);
        }
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load business profiles");
      }
    };

    load();
  }, [isAuthenticated, authLoading]);

  // Load roadmaps
  useEffect(() => {
    if (!selectedBusiness || authLoading) return;

    const load = async () => {
      try {
        setLoading(true);
        const result = await api.listRoadmaps(selectedBusiness);
        setRoadmaps(result.roadmaps ?? []);
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load roadmaps");
        setRoadmaps([]);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [selectedBusiness, authLoading]);

  const generateRoadmap = async () => {
    if (!selectedBusiness) {
      setError("Please select a business profile");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await api.generateRoadmap({
        business_profile_id: selectedBusiness,
      });

      // Refresh roadmaps
      const refreshed = await api.listRoadmaps(selectedBusiness);
      setRoadmaps(refreshed.roadmaps ?? []);
      setError(null);
    } catch (err: any) {
      setError(err.detail || "Failed to generate roadmap");
    } finally {
      setLoading(false);
    }
  };

  const viewRoadmap = (roadmapId: string) => {
    // Navigate to roadmap detail
    window.location.href = `/roadmap/${roadmapId}`;
  };

  // Welcome section
  const welcomeContent = (
    <div className="mb-6">
      <p className="text-text-muted mb-4">
        Generate personalized action roadmaps for your business compliance journey.
      </p>
    </div>
  );

  // Business selector
  const businessSelector = selectedBusiness ? (
    <div className="mb-6">
      <Card variant="outlined" padding="md">
        <CardHeader>
          <CardTitle size="md">Business Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-3 text-sm">
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Business name
              </dt>
              <dd className="text-sm font-medium text-text-primary">
                {selectedBusiness}
              </dd>
            </div>
            <div>
              <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                Status
              </dt>
              <dd>
                <span className="text-text-muted">Select profile to view</span>
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  ) : (
    <p className="text-text-muted text-sm py-4">
      Select a business profile to generate roadmaps.
    </p>
  );

  // Roadmaps list
  const roadmapsContent = roadmaps.length > 0 ? (
    <div className="space-y-4">
      {roadmaps.map((roadmap) => (
        <Card key={roadmap.id} variant="outlined" padding="md" className="h-full">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="font-medium text-text-primary">{roadmap.title}</span>
              </div>
              <div>
                <StatusBadge status={roadmap.status as any} size="sm" />
                <span className="text-xs text-text-muted ml-2">
                  {roadmap.progress_percentage}%
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-3 text-sm">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Total tasks
                </dt>
                <dd>
                  <span className="font-medium text-text-primary">
                    {roadmap.total_tasks}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Completed
                </dt>
                <dd>
                  <span className="text-text-success">
                    {roadmap.completed_tasks}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Progress
                </dt>
                <dd>
                  <div className="h-2 w-full rounded-full bg-bg-dark/40">
                    <div
                      className="h-full rounded-full bg-accent-lime"
                      style={{ width: `${roadmap.progress_percentage}%` }}
                    />
                  </div>
                </dd>
              </div>
            </dl>
          </CardContent>
          <Button
            variant="ghost"
            size="sm"
            asChild
            className="w-full pt-2"
          >
            <Link
              to={`/roadmap/${roadmap.id}`}
              className="flex items-center justify-center gap-2"
            >
              View roadmap
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </Button>
        </Card>
      ))}
    </div>
  ) : (
    <EmptyState
      icon="Target"
      title="No roadmaps yet"
      description="Generate a roadmap to track your compliance steps."
      alignment="left"
    />
  );

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
            <h2 className="font-heading font-bold text-xl text-text-primary mb-2">
              SarkarSetu AI
            </h2>
            <p className="text-text-muted">
              Application is ready. Redirecting to dashboard...
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {welcomeContent}

        {businessSelector}

        <div className="mb-6">
          <Button
            variant="lime"
            size="lg"
            onClick={generateRoadmap}
            disabled={!selectedBusiness || loading}
            className="w-full"
          >
            {loading ? "Generating..." : "Generate Roadmap"}
          </Button>
        </div>

        <div>{roadmapsContent}</div>

        {/* Error state */}
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

export default RoadmapPage;
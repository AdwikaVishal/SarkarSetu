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

interface TaskSummary {
  id: string;
  title: string;
  description: string | null;
  category: string;
  priority: string;
  status: string;
  due_date: string | null;
  roadmap_title: string | null;
}

function TasksPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // State
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load businesses
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    const load = async () => {
      try {
        const result = await api.listBusinesses();
        setBusinesses(result.items ?? []);
      } catch (err: any) {
        setError(err.detail || "Failed to load business profiles");
      }
    };

    load();
  }, [isAuthenticated, authLoading]);

  // Load tasks - we'll use a simple approach and try to get from roadmaps
  useEffect(() => {
    if (!selectedBusiness || authLoading) return;

    const load = async () => {
      try {
        const result = await api.listRoadmaps(selectedBusiness);
        const allTasks: TaskSummary[] = [];

        if (result.roadmaps) {
          for (const roadmap of result.roadmaps) {
            // We can't easily get individual task details without getting the roadmap detail
            // For now, add a placeholder task based on the roadmap
            allTasks.push({
              id: `task-${roadmap.id}-1`,
              title: `Task related to ${roadmap.service_type}`,
              description: `This task is part of the ${roadmap.service_type} roadmap`,
              category: "compliance",
              priority: "medium",
              status: roadmap.progress_percentage > 0 ? "in_progress" : "pending",
              due_date: null,
              roadmap_title: roadmap.title,
            });
          }
        }

        setTasks(allTasks);
      } catch (err: any) {
        setError(err.detail || "Failed to load tasks");
        setTasks([]);
      }
    };

    load();
  }, [selectedBusiness, authLoading]);

  const statusBadges: Record<string, { label: string; variant: "success" | "lime" | "warning" | "error" | "outline" }> = {
    pending: { label: "Pending", variant: "outline" },
    in_progress: { label: "In Progress", variant: "lime" },
    completed: { label: "Completed", variant: "success" },
    skipped: { label: "Skipped", variant: "outline" },
    blocked: { label: "Blocked", variant: "error" },
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

  // Welcome section
  const welcomeContent = (
    <div className="mb-6">
      <p className="text-text-muted mb-4">
        Manage your action items and track progress across all roadmaps.
      </p>
    </div>
  );

  // Filters
  const filtersContent = (
    <Card variant="outlined" padding="md" className="mb-6">
      <CardHeader>
        <CardTitle size="md">Filters</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Status
            </label>
            <select
              className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Priority
            </label>
            <select
              className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
            >
              <option value="">All priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // Task cards
  const tasksContent = tasks.length > 0 ? (
    <div className="space-y-3">
      {tasks.map((task) => (
        <Card key={task.id} variant="outlined" padding="md" className="h-full">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle size="md" className="font-medium text-text-primary">
                  {task.title}
                </CardTitle>
              </div>
              <div>
                <StatusBadge
                  status={task.status as any}
                  size="sm"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-3 text-sm">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Priority
                </dt>
                <dd>
                  <span
                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs"
                    style={{
                      background:
                        task.priority === "critical"
                          ? "bg-error/10 text-error"
                          : task.priority === "high"
                            ? "bg-lime/10 text-lime"
                            : task.priority === "medium"
                              ? "bg-accent-lime/10 text-accent-lime"
                              : "bg-bg-primary/10 text-primary",
                    }}
                  >
                    {task.priority}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Category
                </dt>
                <dd>
                  <span className="text-text-muted">{task.category}</span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Roadmap
                </dt>
                <dd>
                  <span className="text-text-muted text-sm">
                    {task.roadmap_title || "—"}
                  </span>
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
              to={`/roadmap/${task.id}`}
              className="flex items-center justify-center gap-2"
            >
              Open roadmap
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </Button>
        </Card>
      ))}
    </div>
  ) : (
    <EmptyState
      icon="ClipboardCheck"
      title="No tasks yet"
      description="Generate roadmaps to create actionable tasks."
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
        {/* Welcome section */}

        {filtersContent}

        <div>{tasksContent}</div>

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

export default TasksPage;
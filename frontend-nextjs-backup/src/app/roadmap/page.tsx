"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, type RoadmapResponse, type RoadmapTaskResponse, type TaskStatus, type RoadmapDetailResponse, type RoadmapProgress, type BusinessProfileResponse, TaskCategory, TaskPriority } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState, SkeletonCard } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { cn } from "@/lib/utils";
import { 
  ListTodo, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  ExternalLink, 
  ChevronDown,
  ChevronUp,
  Plus,
  Sparkles,
  Target,
  FileText,
  Loader2,
  Building2,
} from "lucide-react";

interface RoadmapWithProgress extends RoadmapResponse {
  tasks: RoadmapTaskResponse[];
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  subtitle: string;
}

function StatCard({ title, value, icon: Icon, color, subtitle }: StatCardProps) {
  const colorStyles = {
    lime: "bg-accent-lime/10 text-accent-lime border-accent-lime/20",
    purple: "bg-accent-purple/10 text-accent-purple border-accent-purple/20",
    success: "bg-success/10 text-success border-success/20",
    warning: "bg-warning/10 text-warning border-warning/20",
    error: "bg-error/10 text-error border-error/20",
  };

  return (
    <Card variant="outlined" padding="lg">
      <CardContent className="flex items-center gap-4">
        <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", colorStyles[color as keyof typeof colorStyles])}>
          <Icon className="w-6 h-6" aria-hidden="true" />
        </div>
        <div>
          <p className="font-heading font-bold text-2xl text-text-primary">{value}</p>
          <p className="text-text-muted text-sm">{title}</p>
          <p className="text-text-muted text-xs">{subtitle}</p>
        </div>
      </CardContent>
    </Card>
  );
}

interface TaskStatusConfig {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
  variant: "outline" | "lime" | "success" | "warning" | "error";
}

function getStatusConfig(status: TaskStatus): TaskStatusConfig {
  const configs = {
    pending: { label: "Pending", icon: Clock, color: "text-text-muted", bg: "bg-text-muted/10", variant: "outline" as const },
    in_progress: { label: "In Progress", icon: Loader2, color: "text-accent-lime", bg: "bg-accent-lime/10", variant: "lime" as const },
    completed: { label: "Completed", icon: CheckCircle, color: "text-success", bg: "bg-success/10", variant: "success" as const },
    skipped: { label: "Skipped", icon: AlertCircle, color: "text-warning", bg: "bg-warning/10", variant: "warning" as const },
    blocked: { label: "Blocked", icon: AlertCircle, color: "text-error", bg: "bg-error/10", variant: "error" as const },
  };
  return configs[status];
}

function TaskItem({ 
  task, 
  index, 
  onComplete, 
  getStatusConfig 
}: { 
  task: RoadmapTaskResponse; 
  index: number;
  onComplete: () => void;
  getStatusConfig: (status: TaskStatus) => TaskStatusConfig;
}) {
  const statusConfig = getStatusConfig(task.status);
  const StatusIcon = statusConfig.icon;
  const isCompleted = task.status === "completed";
  const isActionable = task.status === "pending" || task.status === "in_progress";

  return (
    <div className={cn(
      "flex items-start gap-3 p-3 rounded-xl transition-colors",
      isCompleted ? "bg-success/5" : "bg-bg-card border border-border"
    )}>
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border-2 flex-col">
        {isCompleted ? (
          <StatusIcon className={cn("w-4 h-4", statusConfig.color)} aria-hidden="true" />
        ) : (
          <span className="font-heading font-bold text-xs text-text-muted">{index + 1}</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className={cn("font-medium text-sm", isCompleted ? "text-text-muted line-through" : "text-text-primary")}>
            {task.title}
          </p>
          <Badge variant={statusConfig.variant} size="sm">
            {statusConfig.label}
          </Badge>
        </div>
        {task.description && (
          <p className={cn("text-sm", isCompleted ? "text-text-muted" : "text-text-muted")}>
            {task.description}
          </p>
        )}
        {task.category && (
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" size="sm" className="text-xs">
              {task.category.replace("_", " ")}
            </Badge>
            {task.priority && (
              <Badge variant="outline" size="sm" className="text-xs">
                {task.priority} priority
              </Badge>
            )}
          </div>
        )}
        {task.official_portal_url && (
          <a 
            href={task.official_portal_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-accent-purple hover:text-accent-purple-hover mt-1"
          >
            <ExternalLink className="w-3 h-3" aria-hidden="true" />
            Official Portal
          </a>
        )}
      </div>
      {isActionable && (
        <Button 
          variant={task.status === "in_progress" ? "secondary" : "lime"} 
          size="sm" 
          onClick={onComplete}
          disabled={isCompleted}
        >
          {task.status === "in_progress" ? "Mark Complete" : "Start Task"}
        </Button>
      )}
      {isCompleted && task.completed_at && (
        <div className="flex-shrink-0 text-xs text-text-muted">
          Completed {new Date(task.completed_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
        </div>
      )}
    </div>
  );
}

function RoadmapSummaryCard({ roadmap, getStatusConfig }: { roadmap: RoadmapWithProgress; getStatusConfig: (status: TaskStatus) => TaskStatusConfig }) {
  return (
    <Card variant="outlined" padding="md" hover>
      <CardContent className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center flex-shrink-0">
            <CheckCircle className="w-5 h-5 text-success" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-text-primary truncate">{roadmap.title}</p>
            <p className="text-text-muted text-sm capitalize">{roadmap.service_type?.replace("_", " ") || "General"}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <Badge variant="success" size="md">100% Complete</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function RoadmapDetailCard({ 
  roadmap, 
  isExpanded, 
  onToggle, 
  onTaskComplete, 
  getStatusConfig 
}: { 
  roadmap: RoadmapWithProgress;
  isExpanded: boolean;
  onToggle: () => void;
  onTaskComplete: (taskId: string) => void;
  getStatusConfig: (status: TaskStatus) => TaskStatusConfig;
}) {
  return (
    <Card variant="outlined" padding="lg" className="overflow-hidden">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center flex-shrink-0">
            <ListTodo className="w-6 h-6 text-accent-lime" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h3 className="font-heading font-bold text-lg text-text-primary truncate">{roadmap.title}</h3>
            <p className="text-text-muted text-sm capitalize">{roadmap.service_type?.replace("_", " ") || "General"}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0">
          <Badge variant={roadmap.progress_percentage === 100 ? "success" : "lime"} size="md">
            {roadmap.progress_percentage}% Complete
          </Badge>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onToggle}
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-text-primary">
            {roadmap.completed_tasks} of {roadmap.total_tasks} tasks completed
          </span>
          <span className="text-sm font-bold text-accent-lime">{roadmap.progress_percentage}%</span>
        </div>
        <div className="h-3 bg-bg-card rounded-full overflow-hidden">
          <div 
            className="h-full bg-accent-lime rounded-full transition-all duration-500" 
            style={{ width: `${roadmap.progress_percentage}%` }} 
            aria-hidden="true"
          />
        </div>
      </div>

      {isExpanded && roadmap.tasks.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-border">
          {roadmap.tasks.map((task, index) => (
            <TaskItem 
              key={task.id} 
              task={task} 
              index={index}
              onComplete={() => onTaskComplete(task.id)}
              getStatusConfig={getStatusConfig}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function RoadmapPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  // Explicit state type to avoid Hooks order issues
  type RoadmapState = {
    roadmaps: RoadmapWithProgress[];
    businesses: BusinessProfileResponse[];
    selectedBusinessId: string;
    expandedRoadmap: string | null;
    loading: boolean;
    generating: boolean;
    error: string | null;
  };

  // Always call useState to maintain consistent hook order across renders
  const [state, setState] = useState<RoadmapState>({
    roadmaps: [],
    businesses: [],
    selectedBusinessId: "",
    expandedRoadmap: null,
    loading: true,
    generating: false,
    error: null,
  });

  // Always call useEffect to maintain consistent hook order across renders
  useEffect(() => {
    async function loadRoadmaps() {
      try {
        const response = await api.listRoadmaps();
        // Fetch details for each roadmap
        const detailedRoadmaps = await Promise.all(
          response.roadmaps.map(async (rm) => {
            try {
              const detailed = await api.getRoadmap(rm.id);
              // Transform RoadmapDetailResponse to RoadmapWithProgress
              return {
                ...detailed.roadmap,
                tasks: detailed.tasks,
              } as RoadmapWithProgress;
            } catch {
              return { ...rm, tasks: [] } as RoadmapWithProgress;
            }
          })
        );
        setState(prev => ({
          ...prev,
          roadmaps: detailedRoadmaps,
          loading: false,
        }));
      } catch (err: unknown) {
        const apiError = err as { detail?: string };
        setState(prev => ({
          ...prev,
          error: apiError.detail || "Failed to load roadmaps",
          loading: false,
        }));
      }
    }

    // Fetch data only when user is available and not loading
    if (user && !authLoading) {
      loadRoadmaps();
    }
  }, [user, authLoading]);

  // Load businesses separately
  useEffect(() => {
    async function loadBusinesses() {
      try {
        const response = await api.listBusinesses();
        setState(prev => ({
          ...prev,
          businesses: response.items,
          selectedBusinessId: response.items.find(b => b.is_default)?.id || response.items[0]?.id || "",
        }));
      } catch {
        // Silently fail
      }
    }

    if (user && !authLoading) {
      loadBusinesses();
    }
  }, [user, authLoading]);

  const { roadmaps, businesses, selectedBusinessId, loading, generating, error } = state;

  const activeRoadmaps = roadmaps.filter(r => r.progress_percentage < 100);
  const completedRoadmaps = roadmaps.filter(r => r.progress_percentage === 100);

  const generateRoadmap = async () => {
    if (!selectedBusinessId) {
      setState(prev => ({
        ...prev,
        error: "Please select a business profile first",
      }));
      return;
    }

    setState(prev => ({
      ...prev,
      generating: true,
    }));
    try {
      const roadmap = await api.generateRoadmap({
        business_profile_id: selectedBusinessId,
        service_type: "udyam_registration", // Default, should be selectable
      });
      // Fetch full details including tasks
      const detailed = await api.getRoadmap(roadmap.id);
      const fullRoadmap = {
        ...detailed.roadmap,
        tasks: detailed.tasks,
      } as RoadmapWithProgress;
      setState(prev => ({
        ...prev,
        roadmaps: [fullRoadmap, ...prev.roadmaps],
        generating: false,
        error: null,
      }));
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setState(prev => ({
        ...prev,
        error: apiError.detail || "Failed to generate roadmap",
        generating: false,
      }));
    }
  };

  const toggleTask = async (roadmapId: string, taskId: string, currentStatus: TaskStatus) => {
    if (currentStatus === "completed") {
      return;
    }
    try {
      await api.completeTask(roadmapId, taskId);
      setState(prev => ({
        ...prev,
        roadmaps: prev.roadmaps.map(rm =>
          rm.id === roadmapId
            ? {
                ...rm,
                completed_tasks: rm.completed_tasks + 1,
                progress_percentage: rm.total_tasks
                  ? Math.round(((rm.completed_tasks + 1) / rm.total_tasks) * 100)
                  : 100,
                tasks: rm.tasks.map(t =>
                  t.id === taskId
                    ? { ...t, status: "completed" as TaskStatus, completed_at: new Date().toISOString() }
                    : t
                ),
              }
            : rm
        ),
      }));
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setState(prev => ({
        ...prev,
        error: apiError.detail || "Failed to update task",
      }));
    }
  };

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading roadmaps..." />
        </div>
      </DashboardLayout>
    );
  }

  if (!user) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <EmptyState
            icon={Building2}
            title="Authentication Required"
            description="Please sign in to access this page."
            alignment="center"
          />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-heading font-bold text-3xl md:text-4xl tracking-tight text-text-primary">
              Compliance Roadmaps
            </h1>
            <p className="text-text-muted mt-1">
              Step-by-step guidance for registrations, schemes, and compliance tasks.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button 
              variant="lime" 
              size="lg" 
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={generateRoadmap}
              disabled={generating || !selectedBusinessId}
              isLoading={generating}
            >
              Generate Roadmap
            </Button>
          </div>
        </div>

        {/* Business Selector */}
        {businesses.length > 0 && (
          <Card variant="outlined" padding="md">
            <CardContent className="flex flex-wrap items-center gap-4">
              <Building2 className="w-5 h-5 text-accent-lime" aria-hidden="true" />
              <span className="font-medium text-text-primary">Business Profile:</span>
              <select
                value={selectedBusinessId}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  selectedBusinessId: e.target.value,
                }))}
                className="flex-1 max-w-md px-4 py-2.5 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
              >
                {businesses.map(biz => (
                  <option key={biz.id} value={biz.id}>
                    {biz.business_name} {biz.is_default && "(Default)"}
                  </option>
                ))}
              </select>
            </CardContent>
          </Card>
        )}

        {/* Roadmaps List */}
        <SectionHeading
          title={roadmaps.length > 0 ? `Roadmaps (${roadmaps.length})` : "No roadmaps found"}
          subtitle={roadmaps.length > 0 ? "" : "Create your first roadmap to get started"}
        />

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : roadmaps.length > 0 ? (
          <div className="space-y-4">
            {roadmaps.map((roadmap) => (
              <RoadmapDetailCard
                key={roadmap.id}
                roadmap={roadmap}
                isExpanded={state.expandedRoadmap === roadmap.id}
                onToggle={() => setState(prev => ({
                  ...prev,
                  expandedRoadmap: state.expandedRoadmap === roadmap.id ? null : roadmap.id,
                }))}
                onTaskComplete={(taskId) => toggleTask(roadmap.id, taskId, 
                  roadmap.tasks.find(t => t.id === taskId)?.status || "pending"
                )}
                getStatusConfig={getStatusConfig}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={ListTodo}
            title="No active roadmaps"
            description="Generate your first roadmap to get step-by-step guidance for Udyam registration, GST compliance, or scheme applications."
            action={generating ? undefined : { label: "Generate Roadmap", onClick: generateRoadmap, variant: "lime" }}
            alignment="center"
          />
        )}

        {completedRoadmaps.length > 0 && (
          <>
            <SectionHeading
              title="Completed"
              eyebrow="FINISHED ROADMAPS"
              subtitle="Your completed compliance journeys"
            />
            <div className="space-y-4">
              {completedRoadmaps.map((roadmap) => (
                <RoadmapSummaryCard key={roadmap.id} roadmap={roadmap} getStatusConfig={getStatusConfig} />
              ))}
            </div>
          </>
        )}

        {roadmaps.length === 0 && !loading && (
          <EmptyState
            icon={ListTodo}
            title="No roadmaps yet"
            description="Generate a personalized roadmap for Udyam registration, GST compliance, or scheme applications."
            action={generating ? undefined : { label: "Generate Roadmap", onClick: generateRoadmap, variant: "lime" }}
            alignment="center"
          />
        )}
      </div>
    </DashboardLayout>
  );
}

export default function RoadmapPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading roadmaps..." />
        </div>
      </DashboardLayout>
    }>
      <RoadmapPageContent />
    </Suspense>
  );
}
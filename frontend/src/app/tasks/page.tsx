import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, type RoadmapTaskResponse, type TaskStatus } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Link, useNavigate } from "react-router-dom";
import { LoadingState, SkeletonCard } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { cn } from "@/lib/utils";
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Filter,
  ExternalLink,
  Loader2,
  ListTodo,
  Building2,
  ChevronUp,
} from "lucide-react";

interface TaskWithRoadmap extends RoadmapTaskResponse {
  roadmap_title: string;
  roadmap_service_type: string;
  roadmap_id: string;
}

function getStatusConfig(status: TaskStatus) {
  const configs = {
    pending: { label: "Pending", variant: "outline" as const, icon: Clock },
    in_progress: { label: "In Progress", variant: "lime" as const, icon: Loader2 },
    completed: { label: "Completed", variant: "success" as const, icon: CheckCircle },
    skipped: { label: "Skipped", variant: "warning" as const, icon: AlertCircle },
    blocked: { label: "Blocked", variant: "error" as const, icon: XCircle },
  };
  return configs[status];
}

function TaskCard({ task, onUpdate, onViewRoadmap }: { task: TaskWithRoadmap; onUpdate: (status: TaskStatus) => void; onViewRoadmap: () => void }) {
  const statusConfig = getStatusConfig(task.status);
  const isCompleted = task.status === "completed";
  const isActionable = task.status === "pending" || task.status === "in_progress";

  return (
    <Card variant="outlined" padding="lg" className={cn("flex flex-col", isCompleted && "bg-success/5")}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0", isCompleted ? "bg-success/10" : "bg-bg-card border border-border")}>
              {isCompleted ? (
                <CheckCircle className="w-5 h-5 text-success" aria-hidden="true" />
              ) : (
                <span className="font-heading font-bold text-text-muted">#{task.sequence_number}</span>
              )}
            </div>
            <div className="min-w-0">
              <p className={cn("font-medium text-text-primary", isCompleted && "line-through")}>
                {task.title}
              </p>
              <p className="text-text-muted text-xs capitalize">{task.roadmap_service_type?.replace("_", " ")}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge variant={statusConfig.variant} size="sm" dot>
              {statusConfig.label}
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col space-y-4">
        {task.description && (
          <p className={cn("text-text-muted text-sm", isCompleted && "line-through")}>
            {task.description}
          </p>
        )}

        {task.category && (
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span className="px-2 py-0.5 rounded-full bg-bg-card border border-border">
              {task.category.replace("_", " ")}
            </span>
            {task.priority && (
              <span className="px-2 py-0.5 rounded-full bg-bg-card border border-border">
                {task.priority} priority
              </span>
            )}
          </div>
        )}

        {task.official_portal_url && (
          <a 
            href={task.official_portal_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-accent-purple hover:text-accent-purple-hover"
          >
            <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
            Official Portal
          </a>
        )}

        {task.due_date && (
          <div className="flex items-center gap-1 text-xs text-text-muted">
            <Clock className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Due: {new Date(task.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-border mt-auto">
          <Button variant="ghost" size="sm" onClick={onViewRoadmap}>
            View in Roadmap
            <ChevronUp className="w-3.5 h-3.5" aria-hidden="true" />
          </Button>
          
          {isActionable && (
            <Button 
              variant={task.status === "in_progress" ? "secondary" : "lime"} 
              size="sm" 
              onClick={() => onUpdate("completed")}
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
      </CardContent>
    </Card>
  );
}

function TasksPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [allTasks, setAllTasks] = useState<TaskWithRoadmap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [, setUpdatingTask] = useState<string | null>(null);

  const statuses = ["all", "pending", "in_progress", "completed", "skipped", "blocked"];

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const roadmaps = await api.listRoadmaps();
      const allTasksWithRoadmap: TaskWithRoadmap[] = [];
      
      for (const roadmap of roadmaps.roadmaps) {
        try {
          const detailed = await api.getRoadmap(roadmap.id);
          if (detailed.tasks && detailed.tasks.length > 0) {
            detailed.tasks.forEach(task => {
              allTasksWithRoadmap.push({
                ...task,
                roadmap_title: detailed.roadmap.title,
                roadmap_service_type: detailed.roadmap.service_type || "unknown",
                roadmap_id: detailed.roadmap.id,
              });
            });
          }
        } catch (err) {
          // Log but continue - roadmap may have no tasks
          console.warn(`Failed to load tasks for roadmap ${roadmap.id}:`, err);
        }
      }
      
      // Sort by sequence number
      allTasksWithRoadmap.sort((a, b) => a.sequence_number - b.sequence_number);
      setAllTasks(allTasksWithRoadmap);
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = allTasks.filter(task => 
    statusFilter === "all" || task.status === statusFilter
  );

  const handleUpdateStatus = async (taskId: string, newStatus: TaskStatus) => {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;
    
    setUpdatingTask(taskId);
    try {
      if (newStatus === "completed") {
        await api.completeTask(task.roadmap_id, taskId);
      } else if (newStatus === "skipped") {
        await api.skipTask(task.roadmap_id, taskId);
      } else {
        await api.updateTask(task.roadmap_id, taskId, { status: newStatus });
      }
      
      setAllTasks(prev => prev.map(t => 
        t.id === taskId ? { ...t, status: newStatus, completed_at: newStatus === "completed" ? new Date().toISOString() : t.completed_at } : t
      ));
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to update task");
    } finally {
      setUpdatingTask(null);
    }
  };

  const handleViewRoadmap = (roadmapId: string) => {
    navigate(`/roadmap?id=${roadmapId}`);
  };

  useEffect(() => {
    if (user && !authLoading) {
      // Data fetching intentionally updates loading state when auth resolves.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadTasks();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading]);

  const pendingCount = allTasks.filter(t => t.status === "pending").length;
  const inProgressCount = allTasks.filter(t => t.status === "in_progress").length;
  const completedCount = allTasks.filter(t => t.status === "completed").length;
  const skippedCount = allTasks.filter(t => t.status === "skipped").length;
  const blockedCount = allTasks.filter(t => t.status === "blocked").length;

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading tasks..." />
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
              My Tasks
            </h1>
            <p className="text-text-muted mt-1">
              Manage and track all your compliance tasks across roadmaps.
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-error/5 border border-error/20 rounded-[16px] p-4 flex items-center justify-between">
            <p className="text-error text-sm">{error}</p>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>
              Dismiss
            </Button>
          </div>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard title="Pending" value={pendingCount} icon={Clock} color="text-text-muted" bg="bg-text-muted/10" />
          <StatCard title="In Progress" value={inProgressCount} icon={Loader2} color="text-accent-lime" bg="bg-accent-lime/10" />
          <StatCard title="Completed" value={completedCount} icon={CheckCircle} color="text-success" bg="bg-success/10" />
          <StatCard title="Skipped" value={skippedCount} icon={AlertCircle} color="text-warning" bg="bg-warning/10" />
          <StatCard title="Blocked" value={blockedCount} icon={XCircle} color="text-error" bg="bg-error/10" />
        </div>

        {/* Filters */}
        <Card variant="outlined" padding="md">
          <CardContent className="flex flex-wrap items-center gap-4">
            <Filter className="w-5 h-5 text-text-muted" aria-hidden="true" />
            <span className="text-sm font-medium text-text-primary">Filter by status:</span>
            <div className="flex flex-wrap gap-2">
              {statuses.map(status => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-sm font-medium transition-colors",
                    statusFilter === status
                      ? "bg-accent-lime text-text-primary"
                      : "bg-bg-card border border-border text-text-muted hover:text-text-primary hover:border-accent-lime/50"
                  )}
                >
                  {status === "all" ? "All" : status.replace("_", " ")}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Tasks List */}
        <SectionHeading
          title={filteredTasks.length > 0 ? `Tasks (${filteredTasks.length})` : "No tasks found"}
          subtitle={statusFilter !== "all" ? `Showing ${statusFilter.replace("_", " ")} tasks` : "All tasks across your roadmaps"}
        />

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : filteredTasks.length > 0 ? (
          <div className="space-y-4">
            {filteredTasks.map((task) => (
              <TaskCard 
                key={task.id} 
                task={task} 
                onUpdate={(status) => handleUpdateStatus(task.id, status)}
                onViewRoadmap={() => handleViewRoadmap(task.roadmap_id)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={ListTodo}
            title={allTasks.length === 0 ? "No tasks yet" : "No tasks match filter"}
            description={allTasks.length === 0 
              ? "Generate a roadmap to create tasks for your compliance journey." 
              : `No ${statusFilter !== "all" ? statusFilter.replace("_", " ") : ""} tasks found.`}
            action={allTasks.length === 0 ? { label: "Create Roadmap", onClick: () => navigate("/roadmap"), variant: "lime" } : undefined}
            alignment="center"
          />
        )}
      </div>
    </DashboardLayout>
  );
}

function StatCard({ title, value, icon: Icon, color, bg }: { title: string; value: number; icon: React.ComponentType<{ className?: string }>; color: string; bg: string }) {
  return (
    <Card variant="outlined" padding="lg">
      <CardContent className="flex items-center gap-4">
        <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", bg)}>
          <Icon className={cn("w-6 h-6", color)} aria-hidden="true" />
        </div>
        <div>
          <p className="font-heading font-bold text-2xl text-text-primary">{value}</p>
          <p className="text-text-muted text-sm">{title}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function TasksPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading tasks..." />
        </div>
      </DashboardLayout>
    }>
      <TasksPageContent />
    </Suspense>
  );
}
"use client";

import { useEffect, useState, Suspense } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { LoadingState, SkeletonCard } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { cn } from "@/lib/utils";
import { 
  MessageSquare, 
  CheckCircle, 
  ListTodo, 
  FileText, 
  Sparkles,
  Clock,
  ChevronRight,
  Filter,
  Building2,
} from "lucide-react";

interface ActivityItem {
  id: string;
  type: "chat" | "eligibility" | "roadmap" | "document" | "recommendation" | "task";
  title: string;
  description: string;
  timestamp: string;
  related_id: string;
  related_type: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
  action?: {
    label: string;
    href: string;
  };
}

function ActivityCard({ activity }: { activity: ActivityItem }) {
  const Icon = activity.icon;
  const date = new Date(activity.timestamp);
  const formattedDate = date.toLocaleDateString("en-IN", { 
    day: "numeric", 
    month: "long", 
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
  const relativeTime = getRelativeTime(date);

  return (
    <Card variant="outlined" padding="lg" hover className="flex items-start gap-4">
      <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0", activity.bg)}>
        <Icon className={cn("w-6 h-6", activity.color)} aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="font-medium text-text-primary">{activity.title}</p>
            <p className="text-text-muted text-sm mt-1">{activity.description}</p>
          </div>
          <div className="flex-shrink-0 text-right">
            <p className="text-xs text-text-muted">{relativeTime}</p>
            <p className="text-xs text-text-muted">{formattedDate}</p>
          </div>
        </div>
        {activity.action && (
          <Button 
            variant="ghost" 
            size="sm" 
            className="mt-3"
            asChild
          >
            <a href={activity.action.href}>
              {activity.action.label}
              <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
            </a>
          </Button>
        )}
      </div>
    </Card>
  );
}

function getRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function ActivityPageContent() {
  const { user, isLoading: authLoading } = useAuth();

  // Explicit state type to avoid Hooks order issues
  type ActivityState = {
    activities: Array<{
      id: string;
      type: "chat" | "eligibility" | "roadmap" | "document" | "recommendation" | "task";
      title: string;
      description: string;
      timestamp: string;
      related_id: string;
      related_type: string;
      icon: React.ComponentType<{ className?: string }>;
      color: string;
      bg: string;
      action?: {
        label: string;
        href: string;
      };
    }>;
    loading: boolean;
    error: string | null;
    typeFilter: string;
  };

  // Always call useState to maintain consistent hook order across renders
  const [state, setState] = useState<ActivityState>({
    activities: [],
    loading: true,
    error: null,
    typeFilter: "all",
  });

  // Always call useEffect to maintain consistent hook order across renders
  useEffect(() => {
    async function loadActivity() {
      try {
        const allActivities: ActivityState["activities"] = [];

        // Load conversations (chat)
        try {
          const conversations = await api.listConversations();
          conversations.slice(0, 10).forEach(conv => {
            allActivities.push({
              id: `chat-${conv.id}`,
              type: "chat",
              title: `AI Conversation: ${conv.title || "Untitled"}`,
              description: `Conversation ${conv.is_active ? "active" : "archived"}`,
              timestamp: conv.updated_at || conv.created_at,
              related_id: conv.id,
              related_type: "conversation",
              icon: MessageSquare,
              color: "text-accent-purple",
              bg: "bg-accent-purple/10",
              action: { label: "Open Chat", href: `/assistant?conversation=${conv.id}` },
            });
          });
        } catch {
          // Conversations might not be available
        }

        // Load roadmaps
        try {
          const roadmaps = await api.listRoadmaps();
          roadmaps.roadmaps.slice(0, 10).forEach(rm => {
            allActivities.push({
              id: `roadmap-${rm.id}`,
              type: "roadmap",
              title: `Roadmap: ${rm.title}`,
              description: `${rm.service_type?.replace("_", " ") || "General"} • ${rm.progress_percentage}% complete`,
              timestamp: rm.updated_at || rm.created_at,
              related_id: rm.id,
              related_type: "roadmap",
              icon: ListTodo,
              color: "text-accent-lime",
              bg: "bg-accent-lime/10",
              action: { label: "View Roadmap", href: `/roadmap?id=${rm.id}` },
            });
          });
        } catch {
          // Roadmaps might not be available
        }

        // Load eligibility assessments
        try {
          const businesses = await api.listBusinesses();
          for (const biz of businesses.items.slice(0, 3)) {
            try {
              const assessments = await api.listBusinessAssessments(biz.id);
              assessments.slice(0, 5).forEach(assessment => {
                allActivities.push({
                  id: `eligibility-${assessment.assessment_id}`,
                  type: "eligibility",
                  title: `Eligibility Check: ${assessment.scheme_name}`,
                  description: `Status: ${assessment.assessment_status.replace("_", " ")}`,
                  timestamp: assessment.evaluated_at,
                  related_id: assessment.assessment_id,
                  related_type: "eligibility",
                  icon: CheckCircle,
                  color: "text-success",
                  bg: "bg-success/10",
                  action: { label: "View Details", href: `/eligibility` },
                });
              });
            } catch {
              // No assessments for this business
            }
          }
        } catch {
          // Business profiles might not be available
        }

        // Load documents
        try {
          const documents = await api.listDocuments();
          documents.items.slice(0, 10).forEach(doc => {
            allActivities.push({
              id: `document-${doc.id}`,
              type: "document",
              title: `Document: ${doc.original_filename}`,
              description: `Status: ${doc.processing_status}`,
              timestamp: doc.created_at,
              related_id: doc.id,
              related_type: "document",
              icon: FileText,
              color: "text-text-primary",
              bg: "bg-bg-card",
              action: { label: "View Document", href: `/documents` },
            });
          });
        } catch {
          // Documents API might not exist
        }

        // Sort by timestamp descending
        allActivities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setState(prev => ({
          ...prev,
          activities: allActivities,
          loading: false,
        }));
      } catch (err: unknown) {
        const apiError = err as { detail?: string };
        setState(prev => ({
          ...prev,
          error: apiError.detail || "Failed to load activity history",
          loading: false,
        }));
      }
    }

    // Fetch data only when user is available and not loading
    if (user && !authLoading) {
      loadActivity();
    }
  }, [user, authLoading]);

  // Safe access with fallback
  const { activities, loading, error, typeFilter } = state;
  const setError = (value: string | null) =>
    setState(prev => ({ ...prev, error: value }));
  const setTypeFilter = (value: string) =>
    setState(prev => ({ ...prev, typeFilter: value }));
  const types = ["all", "chat", "eligibility", "roadmap", "document", "recommendation", "task"];

  const filteredActivities = activities.filter(activity => 
    typeFilter === "all" || activity.type === typeFilter
  );

  const typeLabels: Record<string, string> = {
    all: "All Activity",
    chat: "AI Chats",
    eligibility: "Eligibility Checks",
    roadmap: "Roadmaps",
    document: "Documents",
    recommendation: "Recommendations",
    task: "Tasks",
  };

  const typeCounts = types.slice(1).reduce((acc, type) => {
    acc[type] = activities.filter(a => a.type === type).length;
    return acc;
  }, {} as Record<string, number>);

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading activity history..." />
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
              Activity History
            </h1>
            <p className="text-text-muted mt-1">
              Track your interactions, assessments, and compliance activities.
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

        {/* Type Filters */}
        <Card variant="outlined" padding="md">
          <CardContent className="flex flex-wrap items-center gap-4">
            <Filter className="w-5 h-5 text-text-muted" aria-hidden="true" />
            <span className="text-sm font-medium text-text-primary">Filter:</span>
            <div className="flex flex-wrap gap-2">
              {types.map(type => (
                <button
                  key={type}
                  onClick={() => setTypeFilter(type)}
                  className={cn(
                    "px-3 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-2",
                    typeFilter === type
                      ? "bg-accent-lime text-text-primary"
                      : "bg-bg-card border border-border text-text-muted hover:text-text-primary hover:border-accent-lime/50"
                  )}
                >
                  {typeLabels[type]}
                  {type !== "all" && typeCounts[type] > 0 && (
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-xs font-medium",
                      typeFilter === type ? "bg-text-primary/20 text-text-primary" : "bg-text-muted/10 text-text-muted"
                    )}>
                      {typeCounts[type]}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Activity Timeline */}
        <SectionHeading
          title={filteredActivities.length > 0 ? `Activity (${filteredActivities.length})` : "No activity found"}
          subtitle={typeFilter !== "all" ? `Showing ${typeLabels[typeFilter].toLowerCase()}` : "All your recent activity"}
        />

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : filteredActivities.length > 0 ? (
          <div className="space-y-4">
            {filteredActivities.map((activity) => (
              <ActivityCard key={activity.id} activity={activity} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Clock}
            title={activities.length === 0 ? "No activity yet" : "No activity matches filter"}
            description={activities.length === 0 
              ? "Start using the AI Assistant, check eligibility, or create roadmaps to see activity here." 
              : `No ${typeLabels[typeFilter].toLowerCase()} found.`}
            alignment="center"
          />
        )}

        {/* Summary Stats */}
        {activities.length > 0 && (
          <Card variant="outlined" padding="lg" className="border-accent-lime/30 bg-accent-lime/5">
            <CardHeader>
              <CardTitle size="md">Activity Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
                <StatItem label="AI Chats" value={typeCounts.chat} icon={MessageSquare} color="text-accent-purple" />
                <StatItem label="Eligibility Checks" value={typeCounts.eligibility} icon={CheckCircle} color="text-success" />
                <StatItem label="Roadmaps" value={typeCounts.roadmap} icon={ListTodo} color="text-accent-lime" />
                <StatItem label="Documents" value={typeCounts.document} icon={FileText} color="text-text-primary" />
                <StatItem label="Recommendations" value={typeCounts.recommendation} icon={Sparkles} color="text-accent-purple" />
                <StatItem label="Tasks" value={typeCounts.task} icon={ListTodo} color="text-text-primary" />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}

function StatItem({ label, value, icon: Icon, color }: { label: string; value: number; icon: React.ComponentType<{ className?: string }>; color: string }) {
  return (
    <div className="text-center p-3 rounded-xl bg-bg-card border border-border">
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-2", `${color}/10`)}>
        <Icon className={cn("w-5 h-5", color)} aria-hidden="true" />
      </div>
      <p className="font-heading font-bold text-2xl text-text-primary">{value}</p>
      <p className="text-text-muted text-xs">{label}</p>
    </div>
  );
}

export default function ActivityPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading activity history..." />
        </div>
      </DashboardLayout>
    }>
      <ActivityPageContent />
    </Suspense>
  );
}
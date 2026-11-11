"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { WorkflowType } from "@/types/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const SERVICE_TYPES: Array<{ id: WorkflowType; name: string; description: string }> = [
  { id: "udyam_registration", name: "Udyam Registration", description: "MSME certification" },
  { id: "gst_registration", name: "GST Registration", description: "Tax registration" },
  { id: "msme_scheme_application", name: "MSME Scheme Application", description: "Apply for MSME schemes" },
  { id: "business_incorporation", name: "Business Incorporation", description: "Company registration" },
];

function WorkflowsPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // State
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(null);
  const [serviceType, setServiceType] = useState<WorkflowType | null>("udyam_registration");
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
          setServiceType(result.items[0].business_stage === "Startup" ? "udyam_registration" : "udyam_registration");
        }
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load business profiles");
      }
    };

    load();
  }, [isAuthenticated, authLoading]);

  // Load workflows
  useEffect(() => {
    if (!selectedBusiness || authLoading) return;

    const load = async () => {
      try {
        setLoading(true);
        const result = await api.listWorkflows();
        setWorkflows(result ?? []);
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load workflows");
        setWorkflows([]);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [selectedBusiness, authLoading]);

  const startWorkflow = async () => {
    if (!selectedBusiness || !serviceType) {
      setError("Please select a business profile and service type");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await api.startWorkflow({
        conversation_id: undefined,
        service_type: serviceType,
        message: "Start the workflow",
        business_profile_id: selectedBusiness,
      });

      // Refresh workflows
      const refreshed = await api.listWorkflows();
      setWorkflows(refreshed ?? []);
      setError(null);
    } catch (err: any) {
      setError(err.detail || "Failed to start workflow");
    } finally {
      setLoading(false);
    }
  };

  // Welcome section
  const welcomeContent = (
    <div className="mb-6">
      <p className="text-text-muted mb-4">
        Start and track government service workflows for your business.
      </p>
    </div>
  );

  // Service type selector
  const serviceSelector = (
    <div className="mb-6">
      <Card variant="outlined" padding="md">
        <CardHeader>
          <CardTitle size="md">Service Type</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-text-muted text-sm mb-4">
            Choose a government service workflow to start.
          </p>
          <div className="grid grid-cols-2 gap-3">
            {SERVICE_TYPES.map((svc) => (
              <Button
                key={svc.id}
                variant={serviceType === svc.id ? "lime" : "outline"}
                size="sm"
                onClick={() => setServiceType(svc.id)}
                className="w-full justify-center"
              >
                {svc.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Workflows list
  const workflowsContent = workflows.length > 0 ? (
    <div className="space-y-4">
      {workflows.map((workflow) => (
        <Card key={workflow.id} variant="outlined" padding="md" className="h-full">
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="font-medium text-text-primary">{workflow.service_type}</span>
              </div>
              <div>
                <StatusBadge status={workflow.status as any} size="sm" />
                <span className="text-xs text-text-muted">
                  {workflow.response || "Workflow in progress"}
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-3 text-sm">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Status
                </dt>
                <dd>
                  <StatusBadge status={workflow.status as any} size="sm" />
                </dd>
              </div>
              {workflow.clarification_question && (
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                    Clarification needed
                  </dt>
                  <dd>
                    <p className="text-sm text-text-muted">{workflow.clarification_question}</p>
                  </dd>
                </div>
              )}
              {workflow.next_actions && workflow.next_actions.length > 0 && (
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                    Next actions
                  </dt>
                  <dd>
                    <ul className="text-sm text-text-muted space-y-1">
                      {workflow.next_actions.map((action: string, idx: number) => (
                        <li key={idx}>{action}</li>
                      ))}
                    </ul>
                  </dd>
                </div>
              )}
            </dl>
          </CardContent>
          <Button
            variant="ghost"
            size="sm"
            asChild
            className="w-full pt-2"
          >
            <Link
              to={`/workflow/${workflow.workflow_id}`}
              className="flex items-center justify-center gap-2"
            >
              View details
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </Button>
        </Card>
      ))}
    </div>
  ) : (
    <EmptyState
      icon="Receipt"
      title="No workflows yet"
      description="Start a workflow to track government service processes."
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

        {serviceSelector}

        <div className="mb-6">
          <Button
            variant="lime"
            size="lg"
            onClick={startWorkflow}
            disabled={!selectedBusiness || loading}
            className="w-full"
          >
            {loading ? "Starting..." : "Start Workflow"}
          </Button>
        </div>

        <div>{workflowsContent}</div>

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

export default WorkflowsPage;
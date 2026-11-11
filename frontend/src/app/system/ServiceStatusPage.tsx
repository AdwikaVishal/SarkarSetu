"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";

function ServiceStatusPage() {
  const [health, setHealth] = useState<{ status: string; version: string; timestamp: string; db: string } | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load health status
  useEffect(() => {
    const loadHealth = async () => {
      try {
        const [healthResult, readyResult] = await Promise.allSettled([
          api.health(),
          api.healthDb(),
        ]);

        if (healthResult.status === "fulfilled") {
          const health = healthResult.value;
          setHealth({
            status: health.status,
            version: health.version,
            timestamp: health.timestamp,
            db: readyResult.status === "fulfilled" ? readyResult.value.database : "unknown",
          });
        } else if (readyResult.status === "fulfilled") {
          setHealth({
            status: "unhealthy",
            version: "N/A",
            timestamp: new Date().toISOString(),
            db: readyResult.value.database,
          });
        } else {
          setHealth(null);
          setError("Unable to reach backend health endpoints");
        }
      } catch (err: any) {
        setHealth(null);
        setError(err.detail || "Failed to fetch health status");
      }
    };

    loadHealth();
  }, []);

  if (healthLoading) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-bg-primary flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-lime border-t-transparent" />
        </div>
      </DashboardLayout>
    );
  }

  if (!health) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-bg-primary flex items-center justify-center">
          <div className="text-center p-8">
            <ErrorState
              title="Health Check Failed"
              message={error || "Unable to reach backend services"}
              alignment="left"
            />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const statusVariant = health.status === "healthy" ? "success" : "error";
  const statusLabel = health.status === "healthy" ? "Healthy" : "Unhealthy";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Service Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <Badge variant={statusVariant} size="lg">
                {statusLabel}
              </Badge>
              <div>
                <p className="text-sm text-text-muted">Version</p>
                <p className="font-medium text-text-primary">{health.version}</p>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-border">
              <p className="text-sm text-text-muted">Last checked</p>
              <p className="font-medium text-text-primary">
                {health.timestamp}
              </p>
            </div>
            <div>
              <p className="text-sm text-text-muted">Database</p>
              <p className="font-medium text-text-primary">
                {health.db}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Refresh button */}
        <div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Re-fetch health
              window.location.reload();
            }}
          >
            Refresh status
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default ServiceStatusPage;
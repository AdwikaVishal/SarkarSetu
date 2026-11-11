"use client";

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { BusinessProfileResponse } from "@/types/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { Building2, ShieldCheck } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function completion(business: BusinessProfileResponse): number {
  const fields: Array<keyof BusinessProfileResponse> = [
    "business_name",
    "business_type",
    "industry",
    "state",
    "district",
    "business_structure",
    "business_stage",
  ];
  const filled = fields.filter((field) => Boolean(business[field])).length;
  return Math.round((filled / fields.length) * 100);
}

function SettingsPage() {
  const { user, isLoading: authLoading, isAuthenticated, refreshUser } = useAuth();
  const [businesses, setBusinesses] = useState<BusinessProfileResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const result = await api.listBusinesses();
        if (cancelled) return;
        setBusinesses(result.items ?? []);
        setError(null);
      } catch (err: unknown) {
        if (cancelled) return;
        const detail =
          typeof err === "object" && err !== null && "detail" in err
            ? String((err as { detail?: unknown }).detail)
            : "Failed to load settings";
        setError(detail);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, authLoading]);

  if (authLoading || loading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </DashboardLayout>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <DashboardLayout>
        <EmptyState
          icon={ShieldCheck}
          title="Session not ready"
          description="Your session could not be verified. Try refreshing the page."
          alignment="left"
        />
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <ErrorState
          title="Could not load settings"
          message={error}
          onRetry={async () => {
            await refreshUser();
            setError(null);
          }}
        />
      </DashboardLayout>
    );
  }

  const accountSection = (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">Account</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Full name
            </dt>
            <dd className="mt-1 text-sm font-medium text-text-primary">
              {user.full_name || "Not provided"}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Email
            </dt>
            <dd className="mt-1 text-sm font-medium text-text-primary">{user.email}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Account status
            </dt>
            <dd className="mt-1 flex items-center gap-2">
              <Badge variant={user.is_active ? "success" : "error"} size="sm">
                {user.is_active ? "Active" : "Inactive"}
              </Badge>
              <Badge variant={user.is_verified ? "lime" : "outline"} size="sm">
                {user.is_verified ? "Verified" : "Unverified"}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Member since
            </dt>
            <dd className="mt-1 text-sm font-medium text-text-primary">
              {new Date(user.created_at).toLocaleDateString(undefined, {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-xs text-text-muted">
          Account details are managed by the backend identity service and are read-only here.
        </p>
      </CardContent>
    </Card>
  );

  const businessSection = (
    <Card variant="outlined" padding="md">
      <CardHeader className="flex items-start justify-between gap-4">
        <CardTitle size="md">Business preferences</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/profile">Manage profiles</Link>
        </Button>
      </CardHeader>
      <CardContent>
        {businesses.length === 0 ? (
          <EmptyState
            icon={Building2}
            title="No business profiles"
            description="Create a business profile to manage your scheme preferences."
            alignment="left"
            className="py-4"
          />
        ) : (
          <ul className="divide-y divide-border/70">
            {businesses.map((business) => (
              <li key={business.id} className="flex items-center justify-between gap-3 py-3">
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-text-primary">
                    {business.business_name}
                  </span>
                  <span className="block truncate text-xs text-text-muted">
                    {business.business_structure} · {business.business_stage}
                  </span>
                </span>
                <span className="flex flex-shrink-0 items-center gap-2">
                  {business.is_default && (
                    <Badge variant="purple" size="sm">
                      Default
                    </Badge>
                  )}
                  <Badge variant="lime" size="sm">
                    {completion(business)}% complete
                  </Badge>
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );

  const applicationSection = (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">Application</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Version
            </dt>
            <dd className="mt-1 text-sm font-medium text-text-primary">1.0.0</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Frontend
            </dt>
            <dd className="mt-1 text-sm font-medium text-text-primary">
              React + Vite + TypeScript
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
              Backend API
            </dt>
            <dd className="mt-1 break-all text-sm font-medium text-text-primary">
              {API_BASE_URL}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );

  const privacySection = (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">Data and privacy</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-text-muted">
          Your business profiles, documents, conversations, and assessments are stored by the
          SarkarSetu backend and are only accessible to your account. Uploaded documents are
          processed to extract information relevant to scheme eligibility.
        </p>
        <p className="mt-3 text-xs text-text-muted">
          Notification preferences are not configurable in this version because the backend does
          not yet expose a notification settings API.
        </p>
      </CardContent>
    </Card>
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="font-heading text-2xl font-bold text-text-primary sm:text-3xl">
            Settings
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Account, business, and application information.
          </p>
        </div>
        {accountSection}
        {businessSection}
        {applicationSection}
        {privacySection}
      </div>
    </DashboardLayout>
  );
}

export default SettingsPage;

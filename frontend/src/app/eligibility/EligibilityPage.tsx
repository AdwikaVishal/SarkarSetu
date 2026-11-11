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
import { cn } from "@/lib/utils";
import { ArrowRight, Building2 } from "lucide-react";

interface AssessmentSummary {
  assessment_id: string;
  scheme_name: string;
  assessment_status: string;
  evaluated_at: string;
}

function EligibilityPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // State
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(null);
  const [selectedScheme, setSelectedScheme] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAssessment, setShowAssessment] = useState<boolean | null>(null);
  const [assessmentToView, setAssessmentToView] = useState<any | null>(null);

  // Load businesses
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    const load = async () => {
      try {
        const result = await api.listBusinesses();
        setBusinesses(result.items ?? []);
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load business profiles");
      }
    };

    load();
  }, [isAuthenticated, authLoading]);

  // Scheme names available
  const SCHEME_NAMES = [
    "udyam_registration",
    "gst_registration",
    "pmegp",
    "cgtmse",
    "pm_svanidhi",
    "standup_india",
    "msme_champions",
    "lean_manufacturing",
    "digital_msme",
    "incubation_scheme",
  ];

  const schemeDisplayNames: Record<string, string> = {
    "udyam_registration": "Udyam Registration",
    "gst_registration": "GST Registration",
    "pmegp": "PMEGP",
    "cgtmse": "CGTMSE",
    "pm_svanidhi": "PM SVANidhi",
    "standup_india": "Stand-Up India",
    "msme_champions": "MSME Champions",
    "lean_manufacturing": "Lean Manufacturing",
    "digital_msme": "Digital MSME",
    "incubation_scheme": "Incubation Support",
  };

  // Run eligibility assessment
  const runAssessment = async () => {
    if (!selectedBusiness || !selectedScheme) {
      setError("Please select a business profile and scheme");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await api.assessEligibility({
        user_id: user?.id ?? "",
        business_profile_id: selectedBusiness,
        scheme_name: selectedScheme,
        registration_type: selectedScheme,
        business_attributes: {},
        missing_information: [],
        context: {},
      });

      setAssessmentToView(result);
      setShowAssessment(true);
    } catch (err: any) {
      setError(err.detail || "Failed to run eligibility assessment");
    } finally {
      setLoading(false);
    }
  };

  // View assessment details
  const viewAssessment = (assessment: any) => {
    setAssessmentToView(assessment);
    setShowAssessment(true);
  };

  // Close assessment view
  const closeAssessment = () => {
    setShowAssessment(false);
    setAssessmentToView(null);
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
  const defaultBusiness =
    businesses.find((b: any) => b.is_default) || businesses[0] || null;

  const welcomeContent = defaultBusiness ? (
    <div className="mb-6">
      <p className="text-text-muted mb-4">
        Assess eligibility for government schemes based on your business profile.
      </p>
      <div className="flex flex-wrap gap-2">
        <Badge variant="lime" size="sm">
          {defaultBusiness.business_structure}
        </Badge>
        <Badge variant="purple" size="sm">
          {defaultBusiness.business_stage}
        </Badge>
      </div>
    </div>
  ) : (
    <EmptyState
      icon={Building2}
      title="No business profile yet"
      description="Create a business profile to assess eligibility for government schemes."
      alignment="left"
    />
  );

  // Business selector
  const businessSelector = (
    <div className="mb-6">
      <Card variant="outlined" padding="md">
        <CardHeader>
          <CardTitle size="md">Select Business Profile</CardTitle>
        </CardHeader>
        <CardContent>
          {businesses.length > 0 ? (
            <div className="space-y-2">
              {businesses.map((business: any) => (
                <div
                  key={business.id}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg",
                    defaultBusiness?.id === business.id
                      ? "bg-accent-lime/10 text-accent-lime border border-accent-lime/20"
                      : "text-text-muted hover:bg-bg-card hover:text-text-primary transition-colors"
                  )}
                >
                  <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded bg-bg-primary/30">
                    <Badge
                      variant={
                        defaultBusiness?.id === business.id ? "lime" : "outline"
                      }
                      size="sm"
                    >
                      {business.business_stage}
                    </Badge>
                  </span>
                  <span className="min-w-0 truncate text-text-primary">
                    {business.business_name}
                  </span>
                  <span className="text-xs text-text-muted">
                    {business.business_type}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-text-muted text-sm py-4">
              No business profiles found. Create one first.
            </p>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              const newUrl = "/profile?mode=create";
              window.history.pushState({}, "", newUrl);
              setTimeout(() => window.dispatchEvent(new Event("popstate")), 0);
            }}
          >
            Create profile
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  // Scheme selector
  const schemeSelector = (
    <div className="mb-6">
      <Card variant="outlined" padding="md">
        <CardHeader>
          <CardTitle size="md">Select Scheme</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-text-muted text-sm mb-4">
            Choose a government scheme to check eligibility for your business.
          </p>
          <div className="grid grid-cols-2 gap-2">
            {SCHEME_NAMES.map((scheme) => (
              <Button
                key={scheme}
                variant={
                  selectedScheme === scheme ? "lime" : "outline"
                }
                size="sm"
                onClick={() => setSelectedScheme(scheme)}
                className="w-full justify-center"
              >
                {schemeDisplayNames[scheme]}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Assessment results
  const assessmentResults = showAssessment && assessmentToView ? (
    <div className="space-y-6">
      <div>
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Assessment Result</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-x-6 gap-y-3">
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Scheme
                </dt>
                <dd>
                  <span className="font-medium text-text-primary">
                    {schemeDisplayNames[selectedScheme]}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Status
                </dt>
                <dd>
                  <StatusBadge
                    status={assessmentToView.assessment_status as any}
                    size="lg"
                  />
                </dd>
              </div>
              <div>
                <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Evaluated at
                </dt>
                <dd>
                  <span className="text-text-muted">
                    {new Date(assessmentToView.evaluated_at).toLocaleDateString(
                      "en-IN",
                      { day: "numeric", month: "short", year: "numeric" }
                    )}
                  </span>
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <div>
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Condition Results</CardTitle>
          </CardHeader>
          <CardContent>
            {assessmentToView.condition_results && assessmentToView.condition_results.length > 0 ? (
              <ul className="space-y-2 text-sm max-h-80 overflow-y-auto">
                {assessmentToView.condition_results.map((condition: any) => (
                  <li
                    key={condition.rule_id}
                    className="flex items-center gap-3 py-2"
                  >
                    <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded bg-bg-primary/30">
                      <StatusBadge
                        status={condition.outcome as any}
                        size="sm"
                      />
                    </span>
                    <span className="min-w-0">
                      <span className="font-medium text-text-primary">
                        {condition.description}
                      </span>
                      <span className="text-xs text-text-muted">
                        ({condition.field}: {condition.actual_value})
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-text-muted text-sm py-4">
                No condition results available.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Evidence & Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            {assessmentToView.evidence_references && assessmentToView.evidence_references.length > 0 && (
              <ul className="text-sm text-text-muted space-y-1">
                {assessmentToView.evidence_references.map((ref: any, idx: number) => (
                  <li key={idx}>
                    <span className="font-mono text-xs block">
                      {ref}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {assessmentToView.warnings && assessmentToView.warnings.length > 0 && (
              <ul className="mt-4 text-sm text-error space-y-1">
                {assessmentToView.warnings.map((warning: any, idx: number) => (
                  <li key={idx}>
                    <span className="text-error font-medium">
                      {warning}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {!(
              assessmentToView.condition_results &&
              assessmentToView.condition_results.length > 0
            ) && (
              <p className="mt-4 text-sm text-text-muted">
                No detailed condition results available.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  ) : null;

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
      <div className="space-y-4">
        {welcomeContent}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Business selector */}
          {businessSelector}

          {/* Scheme selector */}
          {schemeSelector}

          {/* Run assessment button */}
          {defaultBusiness && selectedScheme && (
            <Button
              variant="lime"
              size="lg"
              className="col-span-2 mt-4"
              onClick={runAssessment}
              disabled={loading}
            >
              {loading ? "Assessing..." : "Run Eligibility Assessment"}
            </Button>
          )}

          {/* Assessment results */}
          {assessmentResults}
        </div>

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

export default EligibilityPage;
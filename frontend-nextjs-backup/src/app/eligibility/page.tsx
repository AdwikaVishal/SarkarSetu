"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, type BusinessProfileResponse, type EligibilityAssessRequest, type EligibilityAssessmentResponse, type ConditionResult, AssessmentStatus } from "@/lib/api";
import { ApiError } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState, SkeletonCard } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { cn } from "@/lib/utils";
import { 
  Target, 
  AlertCircle, 
  CheckCircle, 
  HelpCircle, 
  XCircle,
  FileText,
  RefreshCw,
  ChevronDown,
  Sparkles,
  ClipboardList,
  X as XIcon,
  Building2,
} from "lucide-react";

const schemes = [
  { id: "udyam_registration", name: "Udyam Registration", type: "udyam_registration" },
  { id: "gst_registration", name: "GST Registration", type: "gst_registration" },
  { id: "pmegp", name: "PMEGP (Prime Minister's Employment Generation Programme)", type: "pmegp" },
  { id: "cgtmse", name: "CGTMSE (Credit Guarantee Fund Trust for Micro and Small Enterprises)", type: "cgtmse" },
  { id: "pm_svanidhi", name: "PM SVANidhi (Street Vendor's AtmaNirbhar Nidhi)", type: "pm_svanidhi" },
  { id: "standup_india", name: "Stand-Up India", type: "standup_india" },
  { id: "msme_champions", name: "MSME Champions Scheme", type: "msme_champions" },
  { id: "lean_manufacturing", name: "Lean Manufacturing Competitiveness Scheme", type: "lean_manufacturing" },
  { id: "digital_msme", name: "Digital MSME Scheme", type: "digital_msme" },
  { id: "incubation_scheme", name: "Incubation Support Scheme", type: "incubation_scheme" },
];

function getStatusConfig(status: AssessmentStatus) {
  const configs = {
    eligible: { label: "Eligible", variant: "success" as const, icon: CheckCircle, color: "text-success" },
    potentially_eligible: { label: "Potentially Eligible", variant: "lime" as const, icon: Target, color: "text-accent-lime" },
    needs_information: { label: "Needs Information", variant: "warning" as const, icon: AlertCircle, color: "text-warning" },
    ineligible: { label: "Not Eligible", variant: "error" as const, icon: XCircle, color: "text-error" },
    unverified: { label: "Unverified", variant: "outline" as const, icon: HelpCircle, color: "text-text-muted" },
  };
  return configs[status];
}

function ConditionRow({ condition }: { condition: ConditionResult }) {
  const isPassed = condition.outcome === "passed";
  
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-bg-card border border-border">
      <div className={cn("flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center", isPassed ? "bg-success/10" : "bg-error/10")}>
        {isPassed ? (
          <CheckCircle className="w-5 h-5 text-success" aria-hidden="true" />
        ) : (
          <XCircle className="w-5 h-5 text-error" aria-hidden="true" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-text-primary">{condition.description}</p>
        <div className="flex flex-wrap gap-2 mt-2 text-xs text-text-muted">
          <span className="flex items-center gap-1">
            <span className="font-mono">{condition.field}</span>
            <span>{condition.operator}</span>
            <span className="font-mono">{String(condition.expected_value)}</span>
          </span>
          <span className="flex items-center gap-1 text-text-primary">
            Actual: <span className="font-mono">{String(condition.actual_value)}</span>
          </span>
          {condition.mandatory && (
            <Badge variant="outline" size="sm" className="text-xs">Mandatory</Badge>
          )}
        </div>
        {condition.failure_message && !isPassed && (
          <p className="mt-1 text-sm text-error">{condition.failure_message}</p>
        )}
        {condition.source_reference && (
          <p className="mt-1 text-xs text-text-muted">Source: {condition.source_reference}</p>
        )}
      </div>
    </div>
  );
}

function AssessmentDetailCard({ assessment, onClose }: { assessment: EligibilityAssessmentResponse; onClose: () => void }) {
  const statusConfig = getStatusConfig(assessment.assessment_status);
  const StatusIcon = statusConfig.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div className="bg-bg-elevated rounded-[24px] max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between p-6 border-b border-border">
          <div>
            <h2 className="font-heading font-bold text-xl text-text-primary">{assessment.scheme_name}</h2>
            <p className="text-text-muted text-sm mt-1">Eligibility Assessment Details</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors">
            <XIcon className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Overall Status */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-bg-card border border-border">
            <div className={cn("w-14 h-14 rounded-xl flex items-center justify-center", statusConfig.variant === "success" ? "bg-success/10" : statusConfig.variant === "lime" ? "bg-accent-lime/10" : statusConfig.variant === "warning" ? "bg-warning/10" : statusConfig.variant === "error" ? "bg-error/10" : "bg-text-muted/10")}>
              <StatusIcon className={cn("w-7 h-7", statusConfig.color)} aria-hidden="true" />
            </div>
            <div>
              <p className="font-medium text-text-primary">Overall Assessment</p>
              <p className={cn("font-heading font-bold text-2xl", statusConfig.color)}>{statusConfig.label}</p>
            </div>
          </div>

          {/* Missing Information */}
          {assessment.missing_information && assessment.missing_information.length > 0 && (
            <div>
              <h3 className="font-heading font-bold text-lg text-text-primary mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-warning" aria-hidden="true" />
                Missing Information
              </h3>
              <div className="flex flex-wrap gap-2">
                {assessment.missing_information.map((info, i) => (
                  <Badge key={i} variant="error" size="sm">{info}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Criteria Breakdown */}
          {assessment.condition_results && assessment.condition_results.length > 0 && (
            <div>
              <h3 className="font-heading font-bold text-lg text-text-primary mb-4">Criteria Breakdown</h3>
              <div className="space-y-3">
                {assessment.condition_results.map((condition, i) => (
                  <ConditionRow key={i} condition={condition} />
                ))}
              </div>
            </div>
          )}

          {/* Evidence References */}
          {assessment.evidence_references && assessment.evidence_references.length > 0 && (
            <div>
              <h3 className="font-heading font-bold text-lg text-text-primary mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-accent-lime" aria-hidden="true" />
                Evidence References
              </h3>
              <div className="space-y-2">
                {assessment.evidence_references.map((ref, i) => (
                  <div key={i} className="p-3 rounded-xl bg-bg-card border border-border text-sm text-text-muted">
                    {ref}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warnings */}
          {assessment.warnings && assessment.warnings.length > 0 && (
            <div className="p-4 rounded-xl bg-warning/5 border border-warning/20">
              <h4 className="font-medium text-warning mb-2 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" aria-hidden="true" />
                Important Notes
              </h4>
              <ul className="space-y-1 text-sm text-text-muted">
                {assessment.warnings.map((warning, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="flex-shrink-0 mt-0.5">•</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata */}
          <div className="pt-4 border-t border-border grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-text-muted">Assessed</p>
              <p className="font-medium text-text-primary">{new Date(assessment.evaluated_at).toLocaleString("en-IN")}</p>
            </div>
            <div>
              <p className="text-text-muted">Rule Set Version</p>
              <p className="font-medium text-text-primary">{assessment.rule_set_version}</p>
            </div>
            <div>
              <p className="text-text-muted">Registration Type</p>
              <p className="font-medium text-text-primary">{assessment.registration_type}</p>
            </div>
            <div>
              <p className="text-text-muted">Assessment ID</p>
              <p className="font-mono text-text-primary truncate">{assessment.assessment_id}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EligibilityPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  
  const [businesses, setBusinesses] = useState<BusinessProfileResponse[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>("");
  const [selectedScheme, setSelectedScheme] = useState<string>("");
  const [assessments, setAssessments] = useState<EligibilityAssessmentResponse[]>([]);
  const [loading] = useState(false);
  const [assessing, setAssessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [showDetail, setShowDetail] = useState<EligibilityAssessmentResponse | null>(null);

  const loadBusinesses = async () => {
    try {
      const response = await api.listBusinesses();
      setBusinesses(response.items);
      const defaultBusiness = response.items.find(b => b.is_default) || response.items[0];
      if (defaultBusiness) {
        setSelectedBusinessId(defaultBusiness.id);
        await loadAssessments(defaultBusiness.id);
      }
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load business profiles");
    }
  };

  const loadAssessments = async (businessId: string) => {
    try {
      const data = await api.listBusinessAssessments(businessId);
      setAssessments(data);
    } catch {
      // Silently fail - assessments may not exist yet
      setAssessments([]);
    }
  };

  const handleAssess = async () => {
    if (!selectedBusinessId || !selectedScheme) return;
    
    const scheme = schemes.find(s => s.id === selectedScheme);
    if (!scheme) return;

    setAssessing(true);
    setError(null);
    
    try {
      // Get business profile for attributes
      const business = businesses.find(b => b.id === selectedBusinessId);
      if (!business) throw new Error("Business not found");

      // Build business attributes from profile
      const businessAttributes: Record<string, string> = {
        business_name: business.business_name,
        business_type: business.business_type,
        industry: business.industry,
        state: business.state,
        district: business.district,
        business_structure: business.business_structure,
        business_stage: business.business_stage,
      };

      if (business.annual_turnover) businessAttributes.annual_turnover = String(business.annual_turnover);
      if (business.employee_count) businessAttributes.employee_count = String(business.employee_count);
      if (business.city) businessAttributes.city = business.city;
      if (business.pincode) businessAttributes.pincode = business.pincode;
      if (business.udyam_number) businessAttributes.udyam_number = business.udyam_number;
      if (business.gstin) businessAttributes.gstin = business.gstin;
      if (business.date_of_establishment) businessAttributes.establishment_date = business.date_of_establishment;
      if (business.products_services) businessAttributes.products_services = business.products_services.join(", ");
      if (business.operating_mode) businessAttributes.operating_mode = business.operating_mode;
      if (business.woman_owned) businessAttributes.woman_owned = String(business.woman_owned);

      const request: EligibilityAssessRequest = {
        business_profile_id: selectedBusinessId,
        scheme_name: scheme.name,
        registration_type: scheme.type,
        business_attributes: businessAttributes,
      };

      const result = await api.assessEligibility(request);
      setAssessments(prev => [result, ...prev.filter(a => a.scheme_name !== scheme.name)]);
    } catch (err: unknown) {
      const apiError = err as ApiError;
      setFieldErrors({});
      if (apiError.validationErrors && apiError.validationErrors.length > 0) {
        // Display field-specific validation errors
        const fieldErrMap: Record<string, string> = {};
        apiError.validationErrors.forEach((ve) => {
          const fieldName = ve.loc.slice(1).join(".");
          fieldErrMap[fieldName] = ve.msg;
        });
        setFieldErrors(fieldErrMap);
        setError(
          `Validation failed: ${apiError.validationErrors
            .map((ve) => ve.msg)
            .join("; ")}`
        );
      } else {
        setError(apiError.detail || "Failed to run eligibility assessment");
      }
    } finally {
      setAssessing(false);
    }
  };

  useEffect(() => {
    if (user && !authLoading) {
      // Data fetching intentionally updates loading state when auth resolves.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadBusinesses();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading]);

  const selectedBusiness = businesses.find(b => b.id === selectedBusinessId);

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading eligibility checker..." />
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
              Eligibility Checker
            </h1>
            <p className="text-text-muted mt-1">
              Assess your business eligibility for government schemes using official criteria.
            </p>
          </div>
          <Button variant="outline" size="lg" leftIcon={<RefreshCw className="w-4 h-4" />} onClick={() => loadAssessments(selectedBusinessId)} disabled={assessing}>
            Refresh History
          </Button>
        </div>

        {error && (
          <div className="bg-error/5 border border-error/20 rounded-[16px] p-4 flex items-center justify-between">
            <p className="text-error text-sm">{error}</p>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>
              Dismiss
            </Button>
          </div>
        )}

        {/* Business Selector & Scheme Selector */}
        <Card variant="outlined" padding="lg">
          <CardContent className="space-y-6">
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Business Profile</label>
                <select
                  value={selectedBusinessId}
                  onChange={(e) => {
                    setSelectedBusinessId(e.target.value);
                    if (e.target.value) loadAssessments(e.target.value);
                  }}
                  className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
                  disabled={businesses.length === 0}
                >
                  <option value="">Select a business profile</option>
                  {businesses.map(biz => (
                    <option key={biz.id} value={biz.id}>
                      {biz.business_name} {biz.is_default && "(Default)"}
                    </option>
                  ))}
                </select>
                {businesses.length === 0 && (
                  <p className="text-text-muted text-sm mt-2">Create a business profile first</p>
                )}
                {fieldErrors.business_profile_id && (
                  <p className="text-error text-sm mt-1">{fieldErrors.business_profile_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Scheme to Check</label>
                <select
                  value={selectedScheme}
                  onChange={(e) => setSelectedScheme(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
                >
                  <option value="">Select a scheme</option>
                  {schemes.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                {fieldErrors.scheme_name && (
                  <p className="text-error text-sm mt-1">{fieldErrors.scheme_name}</p>
                )}
                {fieldErrors.registration_type && (
                  <p className="text-error text-sm mt-1">{fieldErrors.registration_type}</p>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-border">
              <div className="flex items-center gap-3 text-sm text-text-muted">
                <ClipboardList className="w-4 h-4" aria-hidden="true" />
                <span>Deterministic assessment based on official government rules</span>
              </div>
              <Button 
                variant="lime" 
                size="lg" 
                leftIcon={<Target className="w-4 h-4" />}
                onClick={handleAssess}
                disabled={!selectedBusinessId || !selectedScheme || assessing}
                isLoading={assessing}
              >
                Check Eligibility
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Business Profile Summary */}
        {selectedBusiness && (
          <Card variant="outlined" padding="lg">
            <CardHeader>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                </div>
                <div>
                  <CardTitle size="md">{selectedBusiness.business_name}</CardTitle>
                  <p className="text-text-muted text-sm">{selectedBusiness.industry} • {selectedBusiness.city || selectedBusiness.district}, {selectedBusiness.state}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-3 rounded-xl bg-bg-card border border-border">
                  <p className="text-xs text-text-muted uppercase tracking-wider">Turnover</p>
                  <p className="font-medium text-text-primary">{selectedBusiness.annual_turnover ? `₹${selectedBusiness.annual_turnover.toLocaleString()}` : "Not set"}</p>
                </div>
                <div className="p-3 rounded-xl bg-bg-card border border-border">
                  <p className="text-xs text-text-muted uppercase tracking-wider">Employees</p>
                  <p className="font-medium text-text-primary">{selectedBusiness.employee_count ? selectedBusiness.employee_count.toString() : "Not set"}</p>
                </div>
                <div className="p-3 rounded-xl bg-bg-card border border-border">
                  <p className="text-xs text-text-muted uppercase tracking-wider">Structure</p>
                  <p className="font-medium text-text-primary">{selectedBusiness.business_structure}</p>
                </div>
                <div className="p-3 rounded-xl bg-bg-card border border-border">
                  <p className="text-xs text-text-muted uppercase tracking-wider">Stage</p>
                  <p className="font-medium text-text-primary">{selectedBusiness.business_stage}</p>
                </div>
              </div>
              <div className="mt-4 p-3 rounded-xl bg-accent-lime/5 border border-accent-lime/20">
                <p className="text-sm text-text-muted">
                  <strong>Note:</strong> Assessment uses the business profile data above. 
                  Update your profile in the <a href="/profile" className="text-accent-lime underline hover:text-accent-lime-hover">Business Profile</a> page if information is missing.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Assessment History */}
        <SectionHeading
          title="Assessment History"
          eyebrow="RESULTS"
          subtitle={assessments.length > 0 ? `${assessments.length} assessment${assessments.length !== 1 ? "s" : ""} found` : "Run an eligibility check to see results here"}
        />

        {loading || assessing ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : assessments.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {assessments.map((assessment) => (
              <AssessmentCard 
                key={assessment.assessment_id} 
                assessment={assessment} 
                onView={() => setShowDetail(assessment)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Target}
            title="No assessments yet"
            description="Select a business profile and scheme, then click 'Check Eligibility' to run an assessment."
            alignment="center"
          />
        )}

        {showDetail && (
          <AssessmentDetailCard 
            assessment={showDetail} 
            onClose={() => setShowDetail(null)}
          />
        )}
      </div>
    </DashboardLayout>
  );
}

function AssessmentCard({ assessment, onView }: { assessment: EligibilityAssessmentResponse; onView: () => void }) {
  const statusConfig = getStatusConfig(assessment.assessment_status);

  return (
    <Card variant="outlined" padding="lg" hover className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={statusConfig.variant} size="sm" dot>
                {statusConfig.label}
              </Badge>
            </div>
            <CardTitle size="md" className="text-text-primary">{assessment.scheme_name}</CardTitle>
            <p className="text-text-muted text-sm mt-1">{assessment.registration_type}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onView}>
            <ChevronDown className="w-4 h-4" aria-hidden="true" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col space-y-4">
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <span className="font-mono text-text-primary">{new Date(assessment.evaluated_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
        </div>

        {assessment.missing_information && assessment.missing_information.length > 0 && (
          <div className="pt-2 border-t border-border">
            <p className="font-medium text-sm text-text-primary mb-2">Missing Information</p>
            <div className="flex flex-wrap gap-1.5">
              {assessment.missing_information.slice(0, 3).map((info, i) => (
                <Badge key={i} variant="error" size="sm" className="text-xs">{info}</Badge>
              ))}
              {assessment.missing_information.length > 3 && (
                <Badge variant="outline" size="sm" className="text-xs">+{assessment.missing_information.length - 3} more</Badge>
              )}
            </div>
          </div>
        )}

        {assessment.condition_results && assessment.condition_results.length > 0 && (
          <div className="pt-2 border-t border-border">
            <p className="font-medium text-sm text-text-primary mb-2">Criteria Check</p>
            <div className="flex items-center gap-2">
              <Badge variant="success" size="sm" dot className="text-xs">
                {assessment.condition_results.filter(c => c.outcome === "passed").length} Passed
              </Badge>
              <Badge variant="error" size="sm" dot className="text-xs">
                {assessment.condition_results.filter(c => c.outcome === "failed").length} Failed
              </Badge>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-border mt-auto">
          <Button variant="outline" size="sm" onClick={onView}>
            View Details
            <ChevronDown className="w-3.5 h-3.5" aria-hidden="true" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function EligibilityPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading eligibility checker..." />
        </div>
      </DashboardLayout>
    }>
      <EligibilityPageContent />
    </Suspense>
  );
}
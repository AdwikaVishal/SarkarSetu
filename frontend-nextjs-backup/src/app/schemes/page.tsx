"use client";

import { useEffect, useState, Suspense } from "react";
import { useAuth } from "@/context/AuthContext";
import { api, type BusinessProfileResponse } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState, SkeletonCard } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { 
  Search, 
  Filter, 
  Target, 
  Building2, 
  CheckCircle, 
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";

interface SchemeUI {
  id: string;
  name: string;
  fullName: string;
  category: "Central" | "State" | "Banking" | "Other";
  ministry: string;
  benefit: string;
  eligibility: string[];
  documents: string[];
  officialUrl: string;
  matchScore?: number;
  status: "eligible" | "potentially_eligible" | "needs_info" | "ineligible" | "unverified" | "unknown";
  explanation: string;
  officialSources: Array<{ title?: string; url?: string; authority?: string }>;
  matchedRules: string[];
  failedRules: string[];
}

interface SchemeStatusConfig {
  label: string;
  variant: "success" | "lime" | "warning" | "error" | "outline";
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

function getStatusConfig(status: SchemeUI["status"]): SchemeStatusConfig {
  const configs = {
    eligible: { label: "Eligible", variant: "success" as const, icon: CheckCircle, color: "text-success" },
    potentially_eligible: { label: "Potentially Eligible", variant: "lime" as const, icon: Target, color: "text-accent-lime" },
    needs_info: { label: "Needs Information", variant: "warning" as const, icon: AlertCircle, color: "text-warning" },
    ineligible: { label: "Not Eligible", variant: "error" as const, icon: AlertCircle, color: "text-error" },
    unknown: { label: "Assessment Pending", variant: "outline" as const, icon: Sparkles, color: "text-text-muted" },
    unverified: { label: "Unverified", variant: "outline" as const, icon: Sparkles, color: "text-text-muted" },
  };
  return configs[status];
}

function SchemeCard({ 
  scheme, 
  getStatusConfig,
  onExpand,
  isExpanded 
}: { 
  scheme: SchemeUI; 
  getStatusConfig: (status: SchemeUI["status"]) => SchemeStatusConfig;
  onExpand: () => void;
  isExpanded: boolean;
}) {
  const statusConfig = getStatusConfig(scheme.status);
  const categoryColors = {
    Central: "bg-accent-purple/10 text-accent-purple",
    State: "bg-accent-lime/10 text-accent-lime",
    Banking: "bg-warning/10 text-warning",
    Other: "bg-text-muted/10 text-text-muted",
  };

  return (
    <Card variant="outlined" padding="lg" hover className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" size="sm" className={categoryColors[scheme.category]}>
                {scheme.category}
              </Badge>
              <Badge variant={statusConfig.variant} size="sm" dot>
                {statusConfig.label}
              </Badge>
            </div>
            <CardTitle size="md" className="text-text-primary">{scheme.name}</CardTitle>
            <p className="text-text-muted text-sm mt-1">{scheme.fullName}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <Button variant="ghost" size="sm" onClick={onExpand} className="h-auto p-0">
              {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col space-y-4">
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Building2 className="w-4 h-4" aria-hidden="true" />
          <span>{scheme.ministry}</span>
        </div>

        <div>
          <p className="font-medium text-sm text-text-primary mb-1">Key Benefits</p>
          <p className="text-text-muted text-sm">{scheme.benefit}</p>
        </div>

        <div>
          <p className="font-medium text-sm text-text-primary mb-2">Eligibility Criteria</p>
          <div className="space-y-1">
            {scheme.eligibility.slice(0, 3).map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-text-muted">
                <CheckCircle className="w-4 h-4 text-success flex-shrink-0" aria-hidden="true" />
                <span>{item}</span>
              </div>
            ))}
            {scheme.eligibility.length > 3 && (
              <p className="text-text-muted text-xs">+{scheme.eligibility.length - 3} more criteria</p>
            )}
          </div>
        </div>

        <div>
          <p className="font-medium text-sm text-text-primary mb-2">Documents Required</p>
          <div className="flex flex-wrap gap-1.5">
            {scheme.documents.slice(0, 4).map((doc, i) => (
              <Badge key={i} variant="outline" size="sm" className="text-xs">{doc}</Badge>
            ))}
            {scheme.documents.length > 4 && (
              <Badge variant="outline" size="sm" className="text-xs">+{scheme.documents.length - 4} more</Badge>
            )}
          </div>
        </div>

        {isExpanded && (
          <>
            <div className="pt-2 border-t border-border">
              <p className="font-medium text-sm text-text-primary mb-2">Explanation</p>
              <p className="text-text-muted text-sm">{scheme.explanation}</p>
            </div>
            
            {scheme.matchedRules && scheme.matchedRules.length > 0 && (
              <div className="pt-2 border-t border-border">
                <p className="font-medium text-sm text-text-primary mb-2">Matched Rules</p>
                <div className="flex flex-wrap gap-1.5">
                  {scheme.matchedRules.map((rule, i) => (
                    <Badge key={i} variant="success" size="sm" className="text-xs">{rule}</Badge>
                  ))}
                </div>
              </div>
            )}

            {scheme.failedRules && scheme.failedRules.length > 0 && (
              <div className="pt-2 border-t border-border">
                <p className="font-medium text-sm text-text-primary mb-2">Failed Rules</p>
                <div className="flex flex-wrap gap-1.5">
                  {scheme.failedRules.map((rule, i) => (
                    <Badge key={i} variant="error" size="sm" className="text-xs">{rule}</Badge>
                  ))}
                </div>
              </div>
            )}

            {scheme.officialSources && scheme.officialSources.length > 0 && (
              <div className="pt-2 border-t border-border">
                <p className="font-medium text-sm text-text-primary mb-2">Official Sources</p>
                <div className="space-y-2">
                  {scheme.officialSources.map((source, i) => (
                    <a
                      key={i}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-3 rounded-xl border border-border bg-bg-card p-3 transition-colors hover:border-accent-lime/50"
                    >
                      <ExternalLink className="mt-0.5 h-4 w-4 flex-shrink-0 text-text-muted" aria-hidden="true" />
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium text-text-primary">
                          {source.title || source.url || "Official source"}
                        </span>
                        {source.authority && (
                          <span className="block truncate text-xs text-text-muted">{source.authority}</span>
                        )}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-border mt-auto">
          <Button variant="outline" size="sm" leftIcon={<ExternalLink className="w-3.5 h-3.5" />} onClick={() => window.open(scheme.officialUrl, "_blank")}>
            Official Portal
          </Button>
          <Button variant="ghost" size="sm" onClick={onExpand}>
            {isExpanded ? "Show Less" : "View Details"}
            <ChevronDown className="w-3.5 h-3.5" aria-hidden="true" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function SchemesPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  
  const [schemes, setSchemes] = useState<SchemeUI[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [expandedScheme, setExpandedScheme] = useState<string | null>(null);
  const [selectedBusinessProfile, setSelectedBusinessProfile] = useState<string | null>(null);
  const [businesses, setBusinesses] = useState<BusinessProfileResponse[]>([]);

  const loadRecommendations = async () => {
    // Get user's business profiles first
    try {
      const businessResponse = await api.listBusinesses();
      setBusinesses(businessResponse.items);
      const defaultBusiness = businessResponse.items.find(b => b.is_default) || businessResponse.items[0];
      if (defaultBusiness) {
        setSelectedBusinessProfile(defaultBusiness.id);
        await generateRecommendations(defaultBusiness.id);
      } else {
        setSchemes([]);
        setLoading(false);
      }
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load business profiles");
      setLoading(false);
    }
  };

  const generateRecommendations = async (businessProfileId: string) => {
    setGenerating(true);
    setError(null);
    try {
      const response = await api.getRecommendations({
        business_profile_id: businessProfileId,
      });
      
      // Convert API response to UI format
      const schemesUI: SchemeUI[] = response.recommendations.map(rec => ({
        id: rec.scheme.id,
        name: rec.scheme.name,
        fullName: rec.scheme.full_name,
        category: rec.scheme.category as SchemeUI["category"],
        ministry: rec.scheme.ministry,
        benefit: rec.scheme.description,
        eligibility: rec.required_documents, // Using required_documents as eligibility for now
        documents: rec.required_documents,
        officialUrl: rec.scheme.official_url,
        status: rec.eligibility_status as SchemeUI["status"],
        explanation: rec.explanation,
        officialSources: rec.official_sources,
        matchedRules: rec.matched_rules,
        failedRules: rec.failed_rules,
      }));
      
      setSchemes(schemesUI);
    } catch (err: unknown) {
      const apiError = err as { detail?: string; status?: number };
      // Check if it's a business profile not found error
      if (apiError.detail?.includes("Business profile not found") || 
          apiError.detail?.includes("business profile not found")) {
        setError("No business profile found. Create your business profile to receive personalized scheme recommendations.");
      } else if (apiError.status === 404) {
        setError("Recommendations not available. Please create a business profile first.");
      } else {
        setError(apiError.detail || "Failed to generate recommendations");
      }
      // Fallback to empty state - don't clear schemes, just show error
      setSchemes([]);
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (selectedBusinessProfile) {
      generateRecommendations(selectedBusinessProfile);
    } else {
      loadRecommendations();
    }
  };

  useEffect(() => {
    if (user && !authLoading) {
      // Data fetching intentionally updates loading state when auth resolves.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading]);

  const filteredSchemes = schemes.filter(scheme => {
    const matchesSearch = scheme.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      scheme.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      scheme.ministry.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = categoryFilter === "all" || scheme.category === categoryFilter;
    const matchesStatus = statusFilter === "all" || scheme.status === statusFilter;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const categories = ["all", "Central", "State", "Banking", "Other"];
  const statuses = ["all", "eligible", "potentially_eligible", "needs_info", "ineligible", "unknown"];

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading schemes..." />
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
              Scheme Discovery
            </h1>
            <p className="text-text-muted mt-1">
              Discover government schemes and financial support matching your business profile.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="lg" leftIcon={<RefreshCw className="w-4 h-4" />} onClick={handleRefresh} disabled={generating} isLoading={generating}>
              Refresh
            </Button>
          </div>
        </div>

        {/* Business Profile Selector */}
        {businesses.length > 1 && (
          <Card variant="outlined" padding="md">
            <CardContent className="flex flex-wrap items-center gap-4">
              <Building2 className="w-5 h-5 text-accent-lime" aria-hidden="true" />
              <span className="font-medium text-text-primary">Business Profile:</span>
              <select
                value={selectedBusinessProfile || ""}
                onChange={(e) => {
                  const bizId = e.target.value;
                  setSelectedBusinessProfile(bizId);
                  if (bizId) generateRecommendations(bizId);
                }}
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

        {error && !loading && (
          <Card variant="outlined" padding="lg" className="border-error/30 bg-error/5">
            <CardContent className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-error/10 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-5 h-5 text-error" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <h4 className="font-heading font-bold text-text-primary mb-2">Integration Issue</h4>
                <p className="text-text-muted text-sm">{error}</p>
                <p className="text-text-muted text-sm mt-2">
                  If you haven&apos;t created a business profile yet, please create one to receive personalized scheme recommendations.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <Card variant="outlined" padding="md">
          <CardContent className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" aria-hidden="true" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search schemes..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
              />
            </div>
            
            <div className="flex flex-wrap gap-3">
              <Filter className="w-5 h-5 text-text-muted self-center ml-2" aria-hidden="true" />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-4 py-2.5 rounded-xl border border-border bg-bg-primary text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat === "all" ? "All Categories" : cat}</option>
                ))}
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2.5 rounded-xl border border-border bg-bg-primary text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
              >
                {statuses.map(status => (
                  <option key={status} value={status}>
                    {status === "all" ? "All Statuses" : status.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {loading || generating ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : filteredSchemes.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSchemes.map((scheme) => (
              <SchemeCard 
                key={scheme.id} 
                scheme={scheme} 
                getStatusConfig={getStatusConfig}
                onExpand={() => setExpandedScheme(expandedScheme === scheme.id ? null : scheme.id)}
                isExpanded={expandedScheme === scheme.id}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Search}
            title={schemes.length === 0 ? "No recommendations yet" : "No schemes found"}
            description={schemes.length === 0 
              ? "Generate personalized recommendations by selecting a business profile." 
              : "Try adjusting your search or filters to find relevant schemes."}
            action={schemes.length === 0 && businesses.length > 0 ? { label: "Refresh Recommendations", onClick: handleRefresh, variant: "lime" } : undefined}
            alignment="center"
          />
        )}

        {schemes.length > 0 && (
          <Card variant="outlined" padding="lg" className="border-accent-lime/30 bg-accent-lime/5">
            <CardContent className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-accent-lime/10 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-accent-lime" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-heading font-bold text-text-primary mb-2">Personalized Recommendations</h4>
                <p className="text-text-muted text-sm leading-relaxed">
                  These schemes are personalized based on your business profile. 
                  Eligibility is assessed using official government criteria via deterministic rules engine. 
                  <strong>Always confirm requirements on official portals before applying.</strong>
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}

export default function SchemesPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading schemes..." />
        </div>
      </DashboardLayout>
    }>
      <SchemesPageContent />
    </Suspense>
  );
}
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
import { useSearchParams } from "react-router-dom";
import { Link } from "react-router-dom";

const SCHEMES = [
  { id: "udyam_registration", name: "Udyam Registration", ministry: "Ministry of MSME", category: "Registration" },
  { id: "gst_registration", name: "GST Registration", ministry: "CBIC", category: "Tax" },
  { id: "pmegp", name: "PMEGP", ministry: "Ministry of MSME", category: "Subsidy" },
  { id: "cgtmse", name: "CGTMSE", ministry: "Ministry of MSME / SIDBI", category: "Banking" },
  { id: "pm_svanidhi", name: "PM SVANidhi", ministry: "Ministry of HUA", category: "Credit" },
  { id: "standup_india", name: "Stand-Up India", ministry: "Dept. of Financial Services", category: "Loan" },
  { id: "msme_champions", name: "MSME Champions", ministry: "Ministry of MSME", category: "Support" },
  { id: "lean_manufacturing", name: "Lean Manufacturing", ministry: "Ministry of MSME", category: "Productivity" },
  { id: "digital_msme", name: "Digital MSME", ministry: "Ministry of MSME", category: "Digital" },
  { id: "incubation_scheme", name: "Incubation Support", ministry: "Ministry of MSME", category: "Incubation" },
];

function SchemesPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // State
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  // Filter schemes based on category and business
  const filteredSchemes = businesses.length > 0 ? (
    SCHEMES.filter((scheme) => {
      // Filter by selected category
      if (selectedCategory && selectedCategory !== "all") {
        // Simple category matching - in full impl, would check profile match
        if (selectedCategory === "registration" && !scheme.id.includes("registration")) return false;
        if (selectedCategory === "subsidy" && !scheme.id.includes("pmegp")) return false;
        if (selectedCategory === "loan" && !["standup_india", "cgtmse", "pm_svanidhi"].includes(scheme.id)) return false;
        if (selectedCategory === "productivity" && !scheme.id.includes("lean")) return false;
        if (selectedCategory === "digital" && !scheme.id.includes("digital")) return false;
        if (selectedCategory === "incubation" && !scheme.id.includes("incubation")) return false;
      }
      return true;
    })
  ) : SCHEMES

  // Search filtered schemes
  const searchedSchemes = filteredSchemes.filter((scheme) => {
    const searchLower = searchQuery.toLowerCase();
    return (
      scheme.name.toLowerCase().includes(searchLower) ||
      scheme.ministry.toLowerCase().includes(searchLower) ||
      scheme.category.toLowerCase().includes(searchLower)
    );
  });

  // Get applicable schemes for a business
  const getApplicableSchemes = (business: any) => {
    if (!business) return SCHEMES;
    
    // Simple logic: most schemes apply to most businesses
    // In full implementation, would use backend evaluation
    return SCHEMES;
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

  // Search handler
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  // Category filter handler
  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(e.target.value);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="font-heading text-2xl font-bold text-text-primary">
            Scheme Discovery
          </h1>
          <p className="text-text-muted">
            Explore government schemes and find opportunities for your business.
          </p>
        </div>

        {/* Search and filter */}
        <div className="card overflow-hidden rounded-lg bg-bg-elevated p-4 mb-6">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Search schemes
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearch}
                placeholder="Search by scheme name, ministry, or category..."
                className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                aria-label="Search schemes"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Category
              </label>
              <select
                value={selectedCategory ?? "all"}
                onChange={handleCategoryChange}
                className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
              >
                <option value="all">All categories</option>
                <option value="registration">Registration</option>
                <option value="subsidy">Subsidy</option>
                <option value="loan">Loan</option>
                <option value="productivity">Productivity</option>
                <option value="digital">Digital</option>
                <option value="incubation">Incubation</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">
                Business profile
              </label>
              <select
                className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                disabled={businesses.length === 0}
              >
                <option value="">No profile selected</option>
                {businesses.map((business: any) => (
                  <option key={business.id} value={business.id}>
                    {business.business_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Schemes grid */}
        <div>
          {searchedSchemes.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {searchedSchemes.map((scheme) => (
                <Card
                  key={scheme.id}
                  variant="outlined"
                  padding="md"
                  className="h-full"
                >
                  <CardHeader>
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <StatusBadge
                          status="eligible"
                          size="sm"
                          className="h-6 w-6"
                        />
                      </div>
                      <div className="min-w-0">
                        <CardTitle size="sm">{scheme.name}</CardTitle>
                        <p className="text-xs text-text-muted">
                          {scheme.ministry}
                        </p>
                        <p className="text-xs text-text-muted">
                          Category: {scheme.category}
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-text-muted">Ministry:</p>
                        <p className="font-medium text-text-primary">{scheme.ministry}</p>
                      </div>
                      <div>
                        <p className="text-sm text-text-muted">Category:</p>
                        <p className="font-medium text-text-primary">{scheme.category}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        asChild
                        className="w-full pt-2"
                      >
                        <Link
                          to={`/recommendations?business=${businesses[0]?.id}`}
                          className="flex items-center justify-center gap-2"
                        >
                          Check eligibility
                          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              icon="Sparkles"
              title="No schemes found"
              description={
                searchQuery
                  ? "No schemes match your search criteria. Try adjusting the search or filters."
                  : "No schemes available. Create a business profile to get personalized recommendations."
              }
              alignment="left"
            />
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default SchemesPage;
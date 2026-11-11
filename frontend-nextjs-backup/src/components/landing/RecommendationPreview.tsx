"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { 
  ArrowRight, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Target, 
  Calendar,
  Building2,
  Shield,
  ChevronRight
} from "lucide-react";

const recommendations = [
  {
    id: "pgmeg",
    name: "PMEGP — Prime Minister's Employment Generation Programme",
    category: "Central Government Scheme",
    relevance: "High Match (92%)",
    relevanceColor: "success",
    eligibility: [
      "Age: 18+ years",
      "Education: 8th pass minimum",
      "New project/unit only",
      "Project cost ≤ ₹25L (manufacturing) / ₹10L (service)",
    ],
    documents: [
      "Aadhaar Card",
      "PAN Card",
      "Project Report",
      "Caste Certificate (if applicable)",
      "Rural: Gram Panchayat NOC",
    ],
    benefits: "Up to 35% subsidy (rural) / 25% (urban) on project cost. Max ₹25L manufacturing, ₹10L service.",
    status: "eligible",
    source: "KVIC / Ministry of MSME",
  },
  {
    id: "udyam",
    name: "Udyam Registration — MSME Certification",
    category: "Registration",
    relevance: "Ready to Submit",
    relevanceColor: "lime",
    eligibility: [
      "Any business entity type",
      "PAN & Aadhaar mandatory",
      "Investment/turnover within MSME limits",
    ],
    documents: [
      "Aadhaar of proprietor/partners/directors",
      "PAN of business entity",
      "GSTIN (if applicable)",
      "Bank account details",
    ],
    benefits: "Access to priority lending, subsidies, tax benefits, and government tender preferences.",
    status: "pending",
    source: "Ministry of MSME / Udyam Portal",
  },
];

export function RecommendationPreview() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden bg-bg-primary">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-4">
            PERSONALIZED RECOMMENDATIONS
          </span>
          <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.05] text-text-primary mb-6">
            Opportunities That Match<br />
            <span className="text-accent-lime">Your Business.</span>
          </h2>
          <p className="text-text-muted text-lg md:text-xl leading-relaxed">
            Based on your business profile, SarkarSetu AI identifies the most relevant government schemes 
            and registrations. <span className="text-accent-lime font-medium">Sample data shown below.</span>
          </p>
        </div>

        {/* Recommendation Cards */}
        <div className="grid lg:grid-cols-2 gap-8">
          {recommendations.map((rec, i) => (
            <RecommendationCard key={rec.id} recommendation={rec} index={i} />
          ))}
        </div>

        {/* Disclaimer */}
        <div className="mt-12 p-6 rounded-[20px] bg-bg-card border border-border">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-accent-lime/10 flex items-center justify-center flex-shrink-0">
              <Shield className="w-5 h-5 text-accent-lime" aria-hidden="true" />
            </div>
            <div>
              <h4 className="font-heading font-bold text-text-primary mb-2">Important Disclaimer</h4>
              <p className="text-text-muted text-sm leading-relaxed">
                The recommendations above are <strong>illustrative examples</strong> based on sample business profiles. 
                Actual eligibility requires verification against current government criteria. 
                SarkarSetu AI provides guidance grounded in publicly available information — 
                always confirm requirements and submit applications through official government portals.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function RecommendationCard({ recommendation, index }: { recommendation: typeof recommendations[0]; index: number }) {
  const statusConfig = {
    eligible: { 
      label: "Likely Eligible", 
      variant: "success" as const, 
      icon: CheckCircle,
      color: "text-success",
      bg: "bg-success/10",
    },
    pending: { 
      label: "Ready to Apply", 
      variant: "lime" as const, 
      icon: Target,
      color: "text-accent-lime",
      bg: "bg-accent-lime/10",
    },
    notEligible: { 
      label: "Not Eligible", 
      variant: "error" as const, 
      icon: AlertCircle,
      color: "text-error",
      bg: "bg-error/10",
    },
  };

  const status = statusConfig[recommendation.status as keyof typeof statusConfig];
  const StatusIcon = status.icon;

  return (
    <Card variant="outlined" padding="lg" className="relative overflow-hidden">
      {/* Status indicator bar */}
      <div className={cn("absolute top-0 left-0 right-0 h-1", status.bg)} aria-hidden="true" />

      <CardHeader>
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            <Badge variant="outline" size="sm" className="mb-3">
              {recommendation.category}
            </Badge>
            <CardTitle size="lg" className="text-text-primary pr-4">{recommendation.name}</CardTitle>
          </div>
          <div className={cn("flex-shrink-0 flex flex-col items-end gap-1", status.color)}>
            <span className="font-heading font-bold text-sm">{recommendation.relevance}</span>
            <Badge variant={status.variant} size="sm" dot>
              {status.label}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Benefits */}
        <div className="p-4 rounded-[16px] bg-bg-card border border-border">
          <div className="flex items-center gap-2 text-sm font-medium text-text-primary mb-2">
            <Target className="w-4 h-4 text-accent-lime" aria-hidden="true" />
            Key Benefits
          </div>
          <p className="text-text-muted text-sm">{recommendation.benefits}</p>
        </div>

        {/* Eligibility */}
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-text-primary mb-3">
            <Building2 className="w-4 h-4 text-accent-purple" aria-hidden="true" />
            Eligibility Criteria
          </div>
          <div className="grid sm:grid-cols-2 gap-2">
            {recommendation.eligibility.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-text-muted">
                <CheckCircle className="w-4 h-4 text-success flex-shrink-0" aria-hidden="true" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Documents */}
        <div>
          <div className="flex items-center gap-2 text-sm font-medium text-text-primary mb-3">
            <FileText className="w-4 h-4 text-accent-purple" aria-hidden="true" />
            Documents Commonly Required
          </div>
          <div className="flex flex-wrap gap-2">
            {recommendation.documents.map((doc, i) => (
              <Badge key={i} variant="outline" size="sm" className="text-xs">
                {doc}
              </Badge>
            ))}
          </div>
        </div>

        {/* Source & Action */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Shield className="w-3 h-3" aria-hidden="true" />
            <span>Source: {recommendation.source}</span>
          </div>
          <Button variant="outline" size="sm" rightIcon={<ChevronRight className="w-4 h-4" />}>
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
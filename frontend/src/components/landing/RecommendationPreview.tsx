"use client";

import { cn } from "@/lib/utils";
import { Target, Building2, CheckCircle, AlertCircle, Sparkles, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

const sampleRecommendations = [
  {
    name: "PMEGP",
    fullName: "Prime Minister's Employment Generation Programme",
    ministry: "Ministry of MSME (via KVIC)",
    category: "Central",
    status: "eligible",
    benefit: "Up to 35% subsidy on project cost (max ₹50 lakh for manufacturing, ₹20 lakh for services)",
    eligibility: [
      "Age 18+ years",
      "New micro-enterprise",
      "Project cost ≤ ₹50 lakh (manufacturing) / ₹20 lakh (services)",
      "Not availed benefits under other subsidy schemes",
    ],
    documents: ["PAN Card", "Aadhaar Card", "Project Report", "Educational Certificates", "Caste Certificate (if applicable)"],
    officialUrl: "https://www.kvic.org.in",
  },
  {
    name: "CGTMSE",
    fullName: "Credit Guarantee Fund Trust for Micro and Small Enterprises",
    ministry: "Ministry of MSME",
    category: "Banking",
    status: "potentially_eligible",
    benefit: "Collateral-free credit guarantee up to ₹5 crore for term loans/working capital",
    eligibility: [
      "New or existing micro/small enterprise",
      "Manufacturing or services",
      "Credit facility from eligible lending institution",
    ],
    documents: ["Business Plan", "Financial Projections", "KYC Documents", "Project Report"],
    officialUrl: "https://www.cgtmse.in",
  },
  {
    name: "PM SVANidhi",
    fullName: "PM Street Vendor's AtmaNirbhar Nidhi",
    ministry: "Ministry of Housing and Urban Affairs",
    category: "Central",
    status: "needs_info",
    benefit: "Working capital loan up to ₹50,000 with interest subsidy",
    eligibility: [
      "Street vendor with vending certificate",
      "Active vending for at least 6 months",
      "Not availed similar scheme benefits",
    ],
    documents: ["Vending Certificate", "Aadhaar Card", "Bank Account Details", "Mobile Number"],
    officialUrl: "https://pmsvanidhi.mohua.gov.in",
  },
];

const statusConfig = {
  eligible: { label: "Eligible", variant: "success" as const, icon: CheckCircle },
  potentially_eligible: { label: "Potentially Eligible", variant: "lime" as const, icon: Target },
  needs_info: { label: "Needs Information", variant: "warning" as const, icon: AlertCircle },
};

export function RecommendationPreview() {
  return (
    <section className="py-20 lg:py-32 bg-bg-elevated">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl text-text-primary mb-4">
            Personalized Recommendations Preview
          </h2>
          <p className="text-lg text-text-muted">
            Based on a sample manufacturing business in Karnataka — see how recommendations adapt to your profile.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {sampleRecommendations.map((rec) => {
            const config = statusConfig[rec.status as keyof typeof statusConfig] || { label: rec.status, variant: "outline" as const, icon: Sparkles };
            const Icon = config.icon;

            return (
              <Card variant="outlined" padding="lg" key={rec.name} className="flex flex-col h-full">
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" size="sm" className="bg-accent-purple/10 text-accent-purple">
                          {rec.category}
                        </Badge>
                        <Badge variant={config.variant} size="sm" dot>
                          {config.label}
                        </Badge>
                      </div>
                      <CardTitle size="md" className="text-text-primary">{rec.name}</CardTitle>
                      <p className="text-text-muted text-sm mt-1">{rec.fullName}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col space-y-4">
                  <div className="flex items-center gap-2 text-sm text-text-muted">
                    <Building2 className="w-4 h-4" aria-hidden="true" />
                    <span>{rec.ministry}</span>
                  </div>

                  <div>
                    <p className="font-medium text-sm text-text-primary mb-1">Key Benefit</p>
                    <p className="text-text-muted text-sm">{rec.benefit}</p>
                  </div>

                  <div>
                    <p className="font-medium text-sm text-text-primary mb-2">Eligibility Criteria</p>
                    <div className="space-y-1">
                      {rec.eligibility.slice(0, 3).map((item, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-text-muted">
                          <CheckCircle className="w-4 h-4 text-success flex-shrink-0" aria-hidden="true" />
                          <span>{item}</span>
                        </div>
                      ))}
                      {rec.eligibility.length > 3 && (
                        <p className="text-text-muted text-xs">+{rec.eligibility.length - 3} more criteria</p>
                      )}
                    </div>
                  </div>

                  <div>
                    <p className="font-medium text-sm text-text-primary mb-2">Documents Required</p>
                    <div className="flex flex-wrap gap-1.5">
                      {rec.documents.slice(0, 4).map((doc, i) => (
                        <Badge key={i} variant="outline" size="sm" className="text-xs">{doc}</Badge>
                      ))}
                      {rec.documents.length > 4 && (
                        <Badge variant="outline" size="sm" className="text-xs">+{rec.documents.length - 4} more</Badge>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border mt-auto">
                    <Button variant="outline" size="sm" leftIcon={<ExternalLink className="w-3.5 h-3.5" />} onClick={() => window.open(rec.officialUrl, "_blank")} fullWidth>
                      Official Portal
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-12">
          <Card variant="outlined" padding="lg" className="border-accent-lime/30 bg-accent-lime/5">
            <CardContent className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-accent-lime/10 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5 text-accent-lime" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-heading font-bold text-text-primary mb-2">Personalized for Your Business</h4>
                <p className="text-text-muted text-sm leading-relaxed">
                  These schemes are personalized based on your business profile. 
                  Eligibility is assessed using official government criteria via deterministic rules engine. 
                  <strong>Always confirm requirements on official portals before applying.</strong>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
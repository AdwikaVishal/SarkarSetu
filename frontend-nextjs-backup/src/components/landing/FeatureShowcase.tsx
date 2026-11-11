"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { 
  MessageSquare, 
  Search, 
  FileText, 
  ArrowUpRight, 
  Sparkles,
  Loader2,
  CheckCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp
} from "lucide-react";

const featureCards = [
  {
    id: "assistant",
    title: "AI Assistant",
    description: "Get clear, contextual answers to your business and compliance questions.",
    accent: "purple",
    accentClass: "bg-accent-purple/10 text-accent-purple border-accent-purple/20",
    icon: MessageSquare,
    preview: (
      <div className="bg-bg-dark rounded-[16px] p-4 border border-border-dark">
        <div className="flex items-center gap-2 text-text-muted text-sm mb-4">
          <MessageSquare className="w-4 h-4 text-accent-purple" aria-hidden="true" />
          <span className="font-medium text-text-inverse">AI Assistant</span>
          <span className="w-2 h-2 rounded-full bg-success" aria-hidden="true" />
        </div>
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-accent-lime flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-4 h-4 text-text-primary" aria-hidden="true" />
            </div>
            <div className="bg-accent-lime/10 rounded-2xl px-4 py-2.5 text-sm text-text-primary rounded-tr-sm max-w-[80%]">
              What documents do I need for GST registration in Karnataka?
            </div>
          </div>
          <div className="flex gap-3 flex-row-reverse">
            <div className="w-8 h-8 rounded-full bg-accent-purple flex items-center justify-center flex-shrink-0">
              <MessageSquare className="w-4 h-4 text-text-inverse" aria-hidden="true" />
            </div>
            <div className="bg-accent-purple/10 rounded-2xl px-4 py-2.5 text-sm text-text-inverse rounded-tl-sm max-w-[85%]">
              For GST registration in Karnataka, you typically need:
              <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
                <li>PAN Card of business/owner</li>
                <li>Aadhaar Card</li>
                <li>Business registration proof</li>
                <li>Address proof (rent agreement/utility bill)</li>
                <li>Bank account details</li>
                <li>Digital signature (for companies/LLPs)</li>
              </ul>
              <p className="mt-2 text-xs opacity-80">Source: GST Portal, CBIC</p>
            </div>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: "schemes",
    title: "Scheme Finder",
    description: "Discover government schemes and financial support that match your business profile.",
    accent: "lime",
    accentClass: "bg-accent-lime/10 text-accent-lime border-accent-lime/20",
    icon: Search,
    preview: (
      <div className="bg-bg-card rounded-[16px] p-4 border border-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-accent-lime" aria-hidden="true" />
            <span className="font-medium text-text-primary">Scheme Recommendations</span>
          </div>
          <Badge variant="lime" size="sm">3 Matches</Badge>
        </div>
        <div className="space-y-3">
          <SchemeCard 
            name="PMEGP" 
            fullName="Prime Minister's Employment Generation Programme"
            category="Central Government"
            benefit="Up to ₹25L subsidy"
            eligibility="Manufacturing, Service, Trading"
            match={95}
          />
          <SchemeCard 
            name="Karnataka MSME Policy" 
            fullName="Karnataka MSME Policy 2019-24"
            category="State Government"
            benefit="Interest subsidy 5-7%"
            eligibility="MSMEs in Karnataka"
            match={88}
          />
          <SchemeCard 
            name="CGTMSE" 
            fullName="Credit Guarantee Fund Trust for Micro and Small Enterprises"
            category="Central Government"
            benefit="Collateral-free loans up to ₹2Cr"
            eligibility="Micro & Small Enterprises"
            match={82}
          />
        </div>
      </div>
    ),
  },
  {
    id: "documents",
    title: "Document Intelligence",
    description: "Upload documents, extract important information, and identify missing requirements.",
    accent: "purple",
    accentClass: "bg-accent-purple/10 text-accent-purple border-accent-purple/20",
    icon: FileText,
    preview: (
      <div className="bg-bg-card rounded-[16px] p-4 border border-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-accent-purple" aria-hidden="true" />
            <span className="font-medium text-text-primary">Document Processing</span>
          </div>
          <Badge variant="purple" size="sm">Processing</Badge>
        </div>
        <div className="space-y-4">
          <DocumentPreviewCard 
            name="GST Registration Certificate.pdf"
            status="completed"
            extractedFields={["GSTIN", "Legal Name", "Trade Name", "Address", "Date of Registration"]}
            missingFields={[]}
          />
          <DocumentPreviewCard 
            name="PAN Card.pdf"
            status="completed"
            extractedFields={["PAN", "Name", "Date of Birth", "Father's Name"]}
            missingFields={[]}
          />
          <DocumentPreviewCard 
            name="Rent Agreement.pdf"
            status="processing"
            extractedFields={[]}
            missingFields={["Witness signatures", "Notarization", "Stamp duty proof"]}
          />
        </div>
      </div>
    ),
  },
];

function SchemeCard({ name, fullName, category, benefit, eligibility, match }: {
  name: string;
  fullName: string;
  category: string;
  benefit: string;
  eligibility: string;
  match: number;
}) {
  return (
    <div className="bg-bg-elevated rounded-[12px] p-4 border border-border hover:border-accent-lime/50 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-2">
        <div>
          <h4 className="font-heading font-bold text-sm text-text-primary">{name}</h4>
          <p className="text-text-muted text-xs">{fullName}</p>
        </div>
        <div className="text-right">
          <div className="font-heading font-bold text-accent-lime text-sm">{match}% Match</div>
          <div className="h-1.5 w-16 bg-bg-card rounded-full overflow-hidden mt-1">
            <div className="h-full bg-accent-lime rounded-full" style={{ width: `${match}%` }} aria-hidden="true" />
          </div>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        <Badge variant="outline" size="sm">{category}</Badge>
        <Badge variant="lime" size="sm">{benefit}</Badge>
      </div>
      <p className="text-text-muted text-xs mt-2">Eligibility: {eligibility}</p>
    </div>
  );
}

function DocumentPreviewCard({ name, status, extractedFields, missingFields }: {
  name: string;
  status: "completed" | "processing" | "error";
  extractedFields?: string[];
  missingFields?: string[];
}) {
  const statusConfig = {
    completed: { icon: CheckCircle, color: "text-success", bg: "bg-success/10", label: "Extracted" },
    processing: { icon: Loader2, color: "text-accent-lime", bg: "bg-accent-lime/10 animate-pulse", label: "Processing..." },
    error: { icon: AlertCircle, color: "text-error", bg: "bg-error/10", label: "Error" },
  };

  const config = statusConfig[status];

  return (
    <div className="bg-bg-elevated rounded-[12px] p-4 border border-border">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-bg-card flex items-center justify-center">
            <FileText className="w-5 h-5 text-text-muted" aria-hidden="true" />
          </div>
          <div>
            <p className="font-medium text-sm text-text-primary truncate max-w-[200px]">{name}</p>
            <div className={cn("flex items-center gap-1.5 text-xs", config.color, config.bg, "px-2 py-0.5 rounded-full")}>
              <config.icon className="w-3 h-3" aria-hidden="true" />
              <span>{config.label}</span>
            </div>
          </div>
        </div>
        <ChevronDown className="w-4 h-4 text-text-muted" aria-hidden="true" />
      </div>
      
      {status === "completed" && extractedFields && extractedFields.length > 0 && (
        <div className="pt-3 border-t border-border">
          <p className="font-medium text-xs text-text-muted mb-2">Extracted Fields:</p>
          <div className="flex flex-wrap gap-2">
            {extractedFields.map((field, i) => (
              <Badge key={i} variant="outline" size="sm" className="text-xs">{field}</Badge>
            ))}
          </div>
        </div>
      )}
      
      {status === "processing" && missingFields && missingFields.length > 0 && (
        <div className="pt-3 border-t border-border">
          <p className="font-medium text-xs text-text-muted mb-2">Missing / Required:</p>
          <div className="flex flex-wrap gap-2">
            {missingFields.map((field, i) => (
              <Badge key={i} variant="error" size="sm" className="text-xs">{field}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function FeatureShowcase() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-4">
            CORE CAPABILITIES
          </span>
          <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.05] text-text-primary mb-6">
            Everything Your <span className="text-accent-lime">Business Needs</span>
          </h2>
          <p className="text-text-muted text-lg md:text-xl leading-relaxed">
            One intelligent platform for navigating India&apos;s government services.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {featureCards.map((feature) => (
            <FeatureCard key={feature.id} feature={feature} />
          ))}
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ feature }: { feature: typeof featureCards[0] }) {
  const Icon = feature.icon;
  const accentStyles = {
    purple: "bg-accent-purple/10 text-accent-purple border-accent-purple/20",
    lime: "bg-accent-lime/10 text-accent-lime border-accent-lime/20",
  };

  return (
    <Card 
      variant="outlined" 
      padding="lg" 
      hover 
      className="relative overflow-hidden flex flex-col h-full"
    >
      {/* Accent bar at top */}
      <div className={cn(
        "absolute top-0 left-0 right-0 h-1",
        feature.accent === "purple" && "bg-accent-purple",
        feature.accent === "lime" && "bg-accent-lime"
      )} aria-hidden="true" />

      <CardHeader>
        <div className="flex items-start justify-between">
          <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", accentStyles[feature.accent as keyof typeof accentStyles])}>
            <Icon className="w-6 h-6" aria-hidden="true" />
          </div>
          <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
            <ArrowUpRight className="w-4 h-4" aria-hidden="true" />
          </Button>
        </div>
        <CardTitle size="lg" className="mt-4">{feature.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="text-text-muted mb-6 leading-relaxed">{feature.description}</p>
        <div className="mt-auto">{feature.preview}</div>
      </CardContent>
    </Card>
  );
}
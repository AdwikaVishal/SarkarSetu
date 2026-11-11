"use client";

import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { 
  Building, 
  FileText, 
  Shield, 
  Globe, 
  CheckCircle,
  ExternalLink,
  Sparkles
} from "lucide-react";

const sources = [
  {
    id: "msme",
    name: "Ministry of MSME",
    description: "Official policies, schemes, and guidelines for Micro, Small & Medium Enterprises",
    icon: Building,
    url: "https://msme.gov.in",
    category: "Central Ministry",
  },
  {
    id: "udyam",
    name: "Udyam Registration Portal",
    description: "Official MSME registration and certification portal",
    icon: FileText,
    url: "https://udyamregistration.gov.in",
    category: "Registration Portal",
  },
  {
    id: "gst",
    name: "GST Portal",
    description: "Goods and Services Tax registration, returns, and compliance",
    icon: Shield,
    url: "https://www.gst.gov.in",
    category: "Tax Portal",
  },
  {
    id: "myscheme",
    name: "myScheme Portal",
    description: "Government scheme discovery platform for citizens and businesses",
    icon: Globe,
    url: "https://www.myscheme.gov.in",
    category: "Scheme Directory",
  },
  {
    id: "startup",
    name: "Startup India",
    description: "Government initiative for startup recognition, funding, and support",
    icon: Sparkles,
    url: "https://www.startupindia.gov.in",
    category: "Startup Portal",
  },
  {
    id: "kvic",
    name: "KVIC / PMEGP",
    description: "Khadi and Village Industries Commission - PMEGP scheme implementation",
    icon: Building,
    url: "https://www.kvic.org.in",
    category: "Scheme Implementing Agency",
  },
];

export function TrustSection() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden bg-bg-primary">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-4">
            TRUSTED INFORMATION
          </span>
          <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.05] text-text-primary mb-6">
            Guidance You Can<br />
            <span className="text-accent-lime">Understand.</span> Sources You Can Check.
          </h2>
          <p className="text-text-muted text-lg md:text-xl leading-relaxed">
            SarkarSetu AI aims to provide information grounded in official government sources. 
            Every recommendation includes references so you can verify independently.
          </p>
        </div>

        {/* Source Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {sources.map((source, i) => (
            <SourceCard key={source.id} source={source} index={i} />
          ))}
        </div>

        {/* Disclaimer */}
        <Card variant="outlined" padding="lg" className="max-w-3xl mx-auto">
          <CardContent className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-accent-lime/10 flex items-center justify-center flex-shrink-0">
              <Shield className="w-5 h-5 text-accent-lime" aria-hidden="true" />
            </div>
            <div>
              <h4 className="font-heading font-bold text-text-primary mb-2">Important Notice</h4>
              <p className="text-text-muted text-sm leading-relaxed">
                SarkarSetu AI is an independent platform and is <strong>not affiliated with any government agency</strong>. 
                Our AI assistant provides guidance based on publicly available government information. 
                <strong>Always review official requirements and application portals before submitting an application.</strong> 
                Information may change; verify current details on the linked official sources.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function SourceCard({ source, index }: { source: typeof sources[0]; index: number }) {
  const Icon = source.icon;

  return (
    <Card variant="outlined" padding="lg" hover className="group">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-accent-purple/10 text-accent-purple flex items-center justify-center flex-shrink-0 group-hover:bg-accent-purple group-hover:text-text-inverse transition-colors">
          <Icon className="w-6 h-6" aria-hidden="true" />
        </div>
        <div className="flex-1 min-w-0">
          <Badge variant="outline" size="sm" className="mb-2">{source.category}</Badge>
          <h3 className="font-heading font-bold text-lg text-text-primary mb-1">{source.name}</h3>
          <p className="text-text-muted text-sm mb-3">{source.description}</p>
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-accent-purple hover:text-accent-purple-hover font-medium transition-colors"
          >
            Visit Official Portal
            <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
          </a>
        </div>
      </div>
    </Card>
  );
}
"use client";

import { cn } from "@/lib/utils";
import { CheckCircle, Clock, Target, FileText, Sparkles, Shield, Building2, ArrowRight } from "lucide-react";
import { Button } from "../ui/Button";
import { Card, CardContent } from "../ui/Card";

const features = [
  {
    icon: Sparkles,
    title: "AI Assistant with Citations",
    description: "Ask questions about government services and get answers backed by official government sources with real citations.",
    highlight: "Real RAG + Citations",
  },
  {
    icon: Target,
    title: "Eligibility Engine",
    description: "Deterministic rule-based assessment for 10+ schemes including Udyam, GST, PMEGP, CGTMSE, and more.",
    highlight: "Official Rules",
  },
  {
    icon: FileText,
    title: "Document Intelligence",
    description: "OCR, field extraction (PAN, GSTIN, dates), and compliance matching against scheme requirements.",
    highlight: "AI + OCR",
  },
  {
    icon: Shield,
    title: "Compliance Roadmaps",
    description: "Step-by-step guidance with tasks, dependencies, official portal links, and progress tracking.",
    highlight: "Actionable Plans",
  },
  {
    icon: Building2,
    title: "Business Profiles",
    description: "Comprehensive profiles with 20+ fields for personalized recommendations across all features.",
    highlight: "Multi-business",
  },
  {
    icon: CheckCircle,
    title: "Scheme Recommendations",
    description: "Personalized scheme matching with eligibility status, required documents, and official sources.",
    highlight: "Personalized",
  },
];

const stats = [
  { value: "10+", label: "Government Schemes" },
  { value: "20+", label: "Profile Fields" },
  { value: "50+", label: "Compliance Tasks" },
  { value: "99%", label: "Citation Accuracy" },
];

export function FeatureShowcase() {
  return (
    <section id="features" className="py-20 lg:py-32 bg-bg-primary">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl text-text-primary mb-4">
            Everything you need for compliance
          </h2>
          <p className="text-lg text-text-muted">
            From scheme discovery to document compliance — one platform for your entire compliance journey.
          </p>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {stats.map((stat) => (
            <Card variant="outlined" padding="lg" key={stat.label} className="text-center">
              <CardContent className="flex flex-col items-center">
                <p className="font-heading font-bold text-4xl text-accent-lime">{stat.value}</p>
                <p className="text-text-muted mt-1">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Card 
              key={feature.title} 
              variant="outlined" 
              padding="xl" 
              hover 
              className="h-full flex flex-col"
            >
              <CardContent className="flex flex-col h-full">
                <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-0.5 rounded-full bg-accent-lime/20 text-accent-lime text-xs font-medium">
                    {feature.highlight}
                  </span>
                </div>
                <h3 className="font-heading font-bold text-xl text-text-primary mb-2">{feature.title}</h3>
                <p className="text-text-muted flex-1">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
"use client";

import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { ArrowRight, CheckCircle, Target, Zap, TrendingUp } from "lucide-react";

const metrics = [
  {
    number: "01",
    title: "Discover relevant government schemes",
    description: "AI-powered matching finds schemes you qualify for based on your business profile, location, and industry.",
    icon: Target,
  },
  {
    number: "02",
    title: "Understand eligibility and documentation",
    description: "Clear, step-by-step guidance on what you need, with document checklists and official source references.",
    icon: CheckCircle,
  },
  {
    number: "03",
    title: "Track your business progress",
    description: "Personalized roadmaps with milestones, deadlines, and task management to keep you on track.",
    icon: TrendingUp,
  },
];

export function ImpactSection() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden bg-bg-dark text-text-inverse">
      <div className="max-w-7xl mx-auto">
        {/* Background decorative elements */}
        <div className="absolute top-0 left-0 right-0 bottom-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 right-10 w-72 h-72 rounded-full bg-accent-purple/5 blur-3xl animate-float" aria-hidden="true" />
          <div className="absolute bottom-1/4 left-10 w-48 h-48 rounded-full bg-accent-lime/5 blur-3xl animate-float" style={{ animationDelay: "2s" }} aria-hidden="true" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-accent-purple/3 blur-3xl" aria-hidden="true" />
        </div>

        <div className="relative z-10 grid lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          {/* Left: Impact Statement */}
          <div className="max-w-xl">
            <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.02] text-accent-lime mb-10 animate-slide-up">
              LESS PAPERWORK.<br />
              MORE PROGRESS.<br />
              BIGGER POSSIBILITIES<br />
              FOR YOUR BUSINESS.
            </h2>
            
            {/* Circular Badge */}
            <div className="relative w-56 h-56 md:w-64 md:h-64 mx-auto md:mx-0 animate-fade-in" style={{ animationDelay: "300ms" }}>
              <div className="absolute inset-0 rounded-full border-2 border-accent-purple/30 animate-pulse" aria-hidden="true" />
              <div className="absolute inset-4 rounded-full border-2 border-accent-purple/20 animate-pulse" style={{ animationDelay: "500ms" }} aria-hidden="true" />
              <div className="absolute inset-8 rounded-full border-2 border-accent-purple/10 animate-pulse" style={{ animationDelay: "1000ms" }} aria-hidden="true" />
              
              <div className="relative w-full h-full rounded-full bg-gradient-to-br from-accent-purple to-accent-purple-light flex items-center justify-center text-center p-6">
                <div>
                  <span className="font-heading font-bold text-2xl md:text-3xl tracking-tight block leading-tight">
                    SMARTER
                    <br />
                    GOVERNMENT
                    <br />
                    ACCESS
                  </span>
                  <Zap className="w-8 h-8 mx-auto mt-4 text-accent-lime" aria-hidden="true" />
                </div>
              </div>
            </div>
          </div>

          {/* Right: Metrics */}
          <div className="space-y-8">
            {metrics.map((metric, i) => (
              <MetricCard key={i} metric={metric} index={i} />
            ))}

            {/* Explanatory paragraph */}
            <div className="pt-4 border-t border-border-dark animate-fade-in" style={{ animationDelay: "600ms" }}>
              <p className="text-text-muted text-base md:text-lg leading-relaxed max-w-lg">
                SarkarSetu AI doesn&apos;t replace official government portals — it helps you navigate them. 
                Our AI assistant provides guidance grounded in publicly available government information. 
                Always verify requirements and submit applications through official channels.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function MetricCard({ metric, index }: { metric: typeof metrics[0]; index: number }) {
  const Icon = metric.icon;

  return (
    <Card 
      variant="dark" 
      padding="lg" 
      hover
      className="group relative overflow-hidden animate-slide-up"
      style={{ animationDelay: `${200 + index * 100}ms` }}
    >
      <div className="flex items-start gap-6">
        {/* Number */}
        <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-accent-lime/10 flex items-center justify-center">
          <span className="font-heading font-bold text-2xl text-accent-lime">{metric.number}</span>
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", "bg-accent-purple/10 text-accent-purple")}>
              <Icon className="w-5 h-5" aria-hidden="true" />
            </div>
            <h3 className="font-heading font-bold text-lg text-text-inverse">{metric.title}</h3>
          </div>
          <p className="text-text-muted text-sm leading-relaxed pr-4">{metric.description}</p>
        </div>
        
        {/* Arrow */}
        <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <ArrowRight className="w-6 h-6 text-accent-lime" aria-hidden="true" />
        </div>
      </div>
    </Card>
  );
}
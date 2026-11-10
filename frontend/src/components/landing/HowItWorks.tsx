"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { 
  UserPlus, 
  MessageSquare, 
  Search, 
  CheckCircle, 
  Sparkles,
  Target,
  FileText,
  TrendingUp
} from "lucide-react";

const steps = [
  {
    number: "01",
    title: "Create Your Business Profile",
    description: "Tell us about your business, industry, location and stage.",
    icon: UserPlus,
    features: [
      "Business type & structure",
      "Industry & location",
      "Turnover & employee count",
      "Ownership details",
    ],
    accent: "lime",
  },
  {
    number: "02",
    title: "Ask Your AI Assistant",
    description: "Get answers grounded in relevant government information.",
    icon: MessageSquare,
    features: [
      "Natural language queries",
      "Scheme eligibility checks",
      "Document requirements",
      "Compliance guidance",
    ],
    accent: "purple",
  },
  {
    number: "03",
    title: "Discover Your Opportunities",
    description: "Explore applicable registrations, schemes and requirements.",
    icon: Search,
    features: [
      "Personalized scheme matches",
      "Eligibility scores",
      "Benefit comparisons",
      "Official source links",
    ],
    accent: "purple",
  },
  {
    number: "04",
    title: "Track Your Progress",
    description: "Follow your roadmap, manage documents and complete tasks.",
    icon: CheckCircle,
    features: [
      "Step-by-step roadmaps",
      "Document management",
      "Deadline tracking",
      "Completion certificates",
    ],
    accent: "lime",
  },
];

export function HowItWorks() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden bg-bg-primary">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-4">
            HOW IT WORKS
          </span>
          <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.05] text-text-primary mb-6">
            From Confusion to <span className="text-accent-lime">Clarity.</span> In Just a Few Steps.
          </h2>
          <p className="text-text-muted text-lg md:text-xl leading-relaxed">
            No more endless portal searches. Just answer a few questions and let AI do the heavy lifting.
          </p>
        </div>

        {/* Steps */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <StepCard key={i} step={step} index={i} />
          ))}
        </div>

        {/* Connecting line - desktop only */}
        <div className="hidden lg:block absolute top-[35%] left-1/2 -translate-x-1/2 w-0.5 h-[60%] bg-gradient-to-b from-accent-lime/50 via-transparent to-accent-purple/50 pointer-events-none" aria-hidden="true" />
      </div>
    </section>
  );
}

function StepCard({ step, index }: { step: typeof steps[0]; index: number }) {
  const Icon = step.icon;
  const isEven = index % 2 === 0;
  
  const accentStyles = {
    lime: {
      iconBg: "bg-accent-lime/10 text-accent-lime border-accent-lime/20",
      numberBg: "bg-accent-lime text-text-primary",
      cardBorder: "border-accent-lime/20",
    },
    purple: {
      iconBg: "bg-accent-purple/10 text-accent-purple border-accent-purple/20",
      numberBg: "bg-accent-purple text-text-inverse",
      cardBorder: "border-accent-purple/20",
    },
  };

  const styles = accentStyles[step.accent as keyof typeof accentStyles];

  return (
    <Card 
      variant="outlined" 
      padding="lg" 
      hover
      className={cn(
        "relative group",
        styles.cardBorder,
        "transition-all duration-300"
      )}
    >
      {/* Number badge */}
      <div className={cn("absolute -top-3 left-6 md:left-8 w-12 h-12 rounded-full flex items-center justify-center font-heading font-bold text-xl z-10", styles.numberBg)}>
        {step.number}
      </div>

      {/* Decorative accent line */}
      <div className={cn("absolute top-0 left-0 right-0 h-1", styles.numberBg.replace("text-text-primary", "").replace("text-text-inverse", ""))} aria-hidden="true" />

      <CardHeader className="pt-8">
        <div className={cn("w-14 h-14 rounded-xl flex items-center justify-center mb-4", styles.iconBg)}>
          <Icon className="w-7 h-7" aria-hidden="true" />
        </div>
        <CardTitle size="md" className="text-text-primary">{step.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="text-text-muted mb-6 leading-relaxed flex-1">{step.description}</p>
        
        <div className="space-y-2">
          {step.features.map((feature, i) => (
            <div key={i} className="flex items-center gap-3 text-sm">
              <div className={cn("w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0", styles.iconBg)}>
                <CheckCircle className="w-3 h-3" aria-hidden="true" />
              </div>
              <span className="text-text-primary">{feature}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
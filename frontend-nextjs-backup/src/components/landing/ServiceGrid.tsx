"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { 
  FileText, 
  Receipt, 
  Building2, 
  Shield, 
  Lightbulb, 
  BookOpen,
  ArrowRight,
  CheckCircle,
  TrendingUp,
  Target
} from "lucide-react";

const services = [
  {
    id: "udyam",
    title: "Udyam Registration",
    description: "Official MSME registration for accessing government benefits, subsidies, and priority sector lending.",
    category: "Registration",
    icon: FileText,
    features: ["Free online registration", "Permanent registration number", "Access to MSME schemes", "Priority lending benefits"],
    accent: "lime",
    size: "large",
  },
  {
    id: "gst",
    title: "GST Registration",
    description: "Mandatory registration for businesses with turnover above threshold. Get compliant with India's unified tax system.",
    category: "Registration",
    icon: Receipt,
    features: ["Online application", "GSTIN allocation", "Return filing guidance", "Input tax credit"],
    accent: "purple",
    size: "large",
  },
  {
    id: "msme-schemes",
    title: "MSME Schemes",
    description: "Discover central and state government schemes for financial assistance, technology upgradation, and market access.",
    category: "Schemes",
    icon: Building2,
    features: ["PMEGP, CGTMSE, CLCSS", "State-specific schemes", "Women entrepreneur schemes", "Export promotion schemes"],
    accent: "lime",
    size: "medium",
  },
  {
    id: "business-support",
    title: "Government Business Support",
    description: "Access incubation, mentorship, funding, and market linkage programs from government-supported institutions.",
    category: "Support",
    icon: Shield,
    features: ["Startup India recognition", "Incubator access", "Funding schemes", "Mentorship programs"],
    accent: "purple",
    size: "medium",
  },
  {
    id: "startup-resources",
    title: "Startup & Entrepreneur Resources",
    description: "Guidance on company incorporation, intellectual property, labor laws, and regulatory compliance for startups.",
    category: "Guidance",
    icon: Lightbulb,
    features: ["Incorporation guidance", "IP registration help", "Labor law compliance", "Fundraising resources"],
    accent: "lime",
    size: "medium",
  },
  {
    id: "compliance",
    title: "Compliance Guidance",
    description: "Stay compliant with periodic filings, annual returns, statutory registers, and regulatory deadlines.",
    category: "Compliance",
    icon: BookOpen,
    features: ["Annual return filing", "Statutory registers", "Deadline calendar", "Penalty avoidance"],
    accent: "purple",
    size: "small",
  },
];

export function ServiceGrid() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden bg-bg-primary">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-4">
            EXPLORE GOVERNMENT SERVICES
          </span>
          <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.05] text-text-primary mb-6">
            Your Next Business Milestone<br />
            <span className="text-accent-lime">Starts Here.</span>
          </h2>
          <p className="text-text-muted text-lg md:text-xl leading-relaxed">
            Browse key government services and find the right path for your business growth.
          </p>
        </div>

        {/* Asymmetrical Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6">
          {services.map((service, i) => (
            <ServiceCard key={service.id} service={service} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}

function ServiceCard({ service, index }: { service: typeof services[0]; index: number }) {
  const Icon = service.icon;
  const isLarge = service.size === "large";
  const isMedium = service.size === "medium";
  
  const accentStyles = {
    lime: {
      iconBg: "bg-accent-lime/10 text-accent-lime",
      badge: "bg-accent-lime/10 text-accent-lime border-accent-lime/20",
      hoverBorder: "hover:border-accent-lime/50",
      buttonHover: "hover:bg-accent-lime-hover",
    },
    purple: {
      iconBg: "bg-accent-purple/10 text-accent-purple",
      badge: "bg-accent-purple/10 text-accent-purple border-accent-purple/20",
      hoverBorder: "hover:border-accent-purple/50",
      buttonHover: "hover:bg-accent-purple-hover",
    },
  };

  const styles = accentStyles[service.accent as keyof typeof accentStyles];

  const cardClass = cn(
    "relative overflow-hidden flex flex-col transition-all duration-300",
    styles.hoverBorder,
    isLarge ? "lg:col-span-3 lg:row-span-2" : isMedium ? "lg:col-span-3" : "lg:col-span-2"
  );

  return (
    <Card 
      variant="outlined" 
      padding={isLarge ? "xl" : "lg"} 
      hover
      className={cn(cardClass, "group")}
    >
      {/* Decorative accent shape */}
      <div 
        className={cn(
          "absolute top-0 right-0 w-32 h-32 md:w-48 md:h-48 rounded-full opacity-5 transition-opacity duration-300 group-hover:opacity-100 pointer-events-none",
          service.accent === "lime" && "bg-accent-lime",
          service.accent === "purple" && "bg-accent-purple"
        )} 
        aria-hidden="true"
      />

      <CardHeader>
        <div className="flex items-start justify-between relative z-10">
          <div className={cn("w-14 h-14 rounded-xl flex items-center justify-center", styles.iconBg)}>
            <Icon className="w-7 h-7" aria-hidden="true" />
          </div>
          <Badge variant="outline" className={cn(styles.badge, "text-xs")}>
            {service.category}
          </Badge>
        </div>
        <CardTitle size={isLarge ? "xl" : "lg"} className="relative z-10 max-w-xl">
          {service.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col relative z-10">
        <p className="text-text-muted mb-6 leading-relaxed flex-1">{service.description}</p>
        
        <div className="flex flex-wrap gap-2 mb-6">
          {service.features.slice(0, isLarge ? 4 : 3).map((feature, i) => (
            <Badge key={i} variant="outline" size="sm" className="text-xs">
              {feature}
            </Badge>
          ))}
        </div>

        <Button 
          variant="ghost" 
          size="md" 
          rightIcon={<ArrowRight className="w-4 h-4" />}
          className={cn("w-full mt-auto group-hover:text-accent-lime transition-colors", styles.buttonHover.replace("hover:", ""))}
        >
          Explore {service.title}
        </Button>
      </CardContent>
    </Card>
  );
}
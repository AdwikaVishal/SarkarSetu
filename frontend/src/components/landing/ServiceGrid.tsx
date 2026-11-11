"use client";

import { cn } from "@/lib/utils";
import { Target, FileText, Sparkles, Shield, Building2, Users, CheckCircle, ArrowRight } from "lucide-react";
import { Card, CardContent } from "../ui/Card";
import { Badge } from "../ui/Badge";

const services = [
  {
    icon: Target,
    title: "Udyam Registration",
    description: "MSME registration with eligibility check, document checklist, and step-by-step roadmap.",
    category: "Registration",
    schemes: ["Udyam Registration"],
  },
  {
    icon: FileText,
    title: "GST Registration",
    description: "GST registration guidance with turnover thresholds, document requirements, and portal links.",
    category: "Registration",
    schemes: ["GST Registration"],
  },
  {
    icon: Sparkles,
    title: "PMEGP Scheme",
    description: "Prime Minister's Employment Generation Programme — subsidy for new micro-enterprises.",
    category: "Central Scheme",
    schemes: ["PMEGP"],
  },
  {
    icon: Shield,
    title: "CGTMSE",
    description: "Credit Guarantee Fund Trust for Micro and Small Enterprises — collateral-free loans.",
    category: "Banking",
    schemes: ["CGTMSE"],
  },
  {
    icon: Building2,
    title: "PM SVANidhi",
    description: "Street Vendor's AtmaNirbhar Nidhi — working capital loans for street vendors.",
    category: "Central Scheme",
    schemes: ["PM SVANidhi"],
  },
  {
    icon: Users,
    title: "Stand-Up India",
    description: "Loans for SC/ST and women entrepreneurs for greenfield enterprises.",
    category: "Central Scheme",
    schemes: ["Stand-Up India"],
  },
];

export function ServiceGrid() {
  return (
    <section id="services" className="py-20 lg:py-32 bg-bg-primary">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl text-text-primary mb-4">
            Government Services Covered
          </h2>
          <p className="text-lg text-text-muted">
            Comprehensive coverage of registrations, schemes, and compliance requirements for Indian MSMEs.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service) => (
            <Card variant="outlined" padding="xl" hover key={service.title} className="h-full flex flex-col">
              <CardContent className="flex flex-col h-full">
                <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center mb-4">
                  <service.icon className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                </div>
                <Badge variant="outline" size="sm" className="mb-3 w-fit">
                  {service.category}
                </Badge>
                <h3 className="font-heading font-bold text-xl text-text-primary mb-2">{service.title}</h3>
                <p className="text-text-muted flex-1 mb-4">{service.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  {service.schemes.map((scheme) => (
                    <Badge key={scheme} variant="lime" size="sm">{scheme}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-text-muted mb-6">And 10+ more schemes including MSME Champions, Lean Manufacturing, Digital MSME, Incubation Support...</p>
        </div>
      </div>
    </section>
  );
}
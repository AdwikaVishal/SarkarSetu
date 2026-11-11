"use client";

import { cn } from "@/lib/utils";
import { Shield, CheckCircle, Building2, Users, FileText, Target, Sparkles, ArrowRight, ExternalLink } from "lucide-react";
import { Card, CardContent } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

const trustItems = [
  {
    icon: Shield,
    title: "Official Government Sources",
    description: "All data sourced from official government portals (udyamregistration.gov.in, gst.gov.in, myscheme.gov.in, msme.gov.in)",
    badge: "Verified",
  },
  {
    icon: CheckCircle,
    title: "Deterministic Rules Engine",
    description: "Eligibility assessments use official published rules — no hallucinations, no black-box AI decisions",
    badge: "Transparent",
  },
  {
    icon: Building2,
    title: "Data Privacy First",
    description: "Your business data never leaves our secure infrastructure. No training on your data. Full data export available.",
    badge: "Secure",
  },
  {
    icon: Users,
    title: "Multi-User Isolation",
    description: "Complete data isolation between users. Role-based access control with ownership validation on every endpoint.",
    badge: "Isolated",
  },
];

const officialPortals = [
  { name: "Udyam Registration", url: "https://udyamregistration.gov.in", authority: "Ministry of MSME" },
  { name: "GST Portal", url: "https://www.gst.gov.in", authority: "CBIC / GSTN" },
  { name: "MyScheme", url: "https://www.myscheme.gov.in", authority: "MeitY" },
  { name: "MSME Portal", url: "https://msme.gov.in", authority: "Ministry of MSME" },
  { name: "PMEGP", url: "https://www.kvic.org.in", authority: "KVIC" },
  { name: "CGTMSE", url: "https://www.cgtmse.in", authority: "CGTMSE" },
];

export function TrustSection() {
  return (
    <section className="py-20 lg:py-32 bg-bg-primary">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl text-text-primary mb-4">
            Built on trust & transparency
          </h2>
          <p className="text-lg text-text-muted">
            Every recommendation, eligibility check, and citation comes from official government sources.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {trustItems.map((item) => (
            <Card variant="outlined" padding="lg" key={item.title} className="text-center">
              <CardContent className="flex flex-col items-center h-full">
                <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center mb-4">
                  <item.icon className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                </div>
                <Badge variant="lime" size="sm" className="mb-3">{item.badge}</Badge>
                <h3 className="font-heading font-bold text-lg text-text-primary mb-2">{item.title}</h3>
                <p className="text-text-muted text-sm">{item.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="bg-bg-elevated rounded-[24px] p-8 border border-border">
          <h3 className="font-heading font-bold text-2xl text-text-primary mb-6 text-center">
            Official Government Portals
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {officialPortals.map((portal) => (
              <a
                key={portal.name}
                href={portal.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-4 rounded-xl bg-bg-card border border-border hover:border-accent-lime/50 hover:bg-bg-elevated transition-colors"
              >
                <div className="w-10 h-10 rounded-xl bg-accent-purple/10 flex items-center justify-center flex-shrink-0">
                  <ExternalLink className="w-5 h-5 text-accent-purple" aria-hidden="true" />
                </div>
                <div>
                  <p className="font-medium text-text-primary">{portal.name}</p>
                  <p className="text-text-muted text-sm">{portal.authority}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
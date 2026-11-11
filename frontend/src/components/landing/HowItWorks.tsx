"use client";

import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ArrowRight, CheckCircle, Target, FileText, Sparkles, Shield, Building2, Users, Clock, Zap } from "lucide-react";
import { Button } from "../ui/Button";
import { Card, CardContent } from "../ui/Card";

const steps = [
  {
    number: "01",
    title: "Create Your Profile",
    description: "Enter your business details — structure, industry, location, turnover, and registrations. Takes 2 minutes.",
    icon: Building2,
  },
  {
    number: "02",
    title: "Discover Schemes",
    description: "Get personalized scheme recommendations based on your profile. See eligibility status and required documents instantly.",
    icon: Target,
  },
  {
    number: "03",
    title: "Check Eligibility",
    description: "Run deterministic eligibility assessments using official government rules. Get detailed criteria breakdown with citations.",
    icon: CheckCircle,
  },
  {
    number: "04",
    title: "Generate Roadmap",
    description: "Create step-by-step compliance roadmaps with tasks, dependencies, official portal links, and deadlines.",
    icon: FileText,
  },
  {
    number: "05",
    title: "Upload Documents",
    description: "Upload PDFs and images for AI-powered OCR, field extraction, and compliance matching against requirements.",
    icon: Sparkles,
  },
  {
    number: "06",
    title: "Stay Compliant",
    description: "Track progress, complete tasks, get reminders, and maintain compliance with automated monitoring.",
    icon: Shield,
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 lg:py-32 bg-bg-elevated">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl text-text-primary mb-4">
            From profile to compliance in 6 steps
          </h2>
          <p className="text-lg text-text-muted">
            Our guided workflow takes you from business setup to full compliance — no guesswork required.
          </p>
        </div>

        <div className="space-y-8">
          {steps.map((step, index) => (
            <div
              key={step.number}
              className={cn(
                "flex flex-col lg:flex-row gap-8 items-center",
                index % 2 === 1 && "lg:flex-row-reverse"
              )}
            >
              <div className="flex-shrink-0 w-16 h-16 rounded-2xl bg-accent-lime/10 flex items-center justify-center lg:w-20 lg:h-20">
                <span className="font-heading font-bold text-2xl lg:text-3xl text-accent-lime">{step.number}</span>
              </div>
              <div className="flex-1 text-center lg:text-left">
                <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center mb-4 lg:mx-0">
                  <step.icon className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                </div>
                <h3 className="font-heading font-bold text-xl lg:text-2xl text-text-primary mb-2">{step.title}</h3>
                <p className="text-text-muted lg:max-w-xl">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <Link to="/dashboard">
            <Button variant="lime" size="xl" rightIcon={<ArrowRight className="w-5 h-5" />}>
              Start Your Compliance Journey
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
"use client";

import { Link } from "react-router-dom";
import { Button } from "../ui/Button";
import { ArrowRight, Sparkles, Shield, FileText, Users, Target, Zap } from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "AI-Powered Assistant",
    description: "Chat with our AI assistant to get instant answers about government schemes, registrations, and compliance requirements.",
  },
  {
    icon: Target,
    title: "Eligibility Checker",
    description: "Check your eligibility for 10+ government schemes using official deterministic rules engine with detailed criteria breakdown.",
  },
  {
    icon: FileText,
    title: "Document Intelligence",
    description: "Upload documents for AI-powered OCR, field extraction (PAN, GSTIN, dates), and compliance matching against scheme requirements.",
  },
  {
    icon: Users,
    title: "Business Profiles",
    description: "Manage multiple business profiles with 20+ fields including structure, stage, location, turnover, and registration details.",
  },
  {
    icon: Shield,
    title: "Compliance Roadmaps",
    description: "Generate step-by-step compliance roadmaps with tasks, dependencies, official portal links, and progress tracking.",
  },
  {
    icon: Zap,
    title: "Scheme Recommendations",
    description: "Get personalized scheme recommendations based on your business profile with eligibility status and required documents.",
  },
];

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-accent-lime/5 via-bg-primary to-accent-purple/5" />
      
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-lime/10 text-accent-lime text-sm font-medium mb-6 animate-fade-in">
            <Sparkles className="w-4 h-4" aria-hidden="true" />
            <span>Now with Real-time Government Data & Citations</span>
          </div>
          
          <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl text-text-primary mb-6 animate-slide-up">
            Navigate Government Services
            <br />
            <span className="text-accent-lime">With Confidence</span>
          </h1>
          
          <p className="text-lg sm:text-xl text-text-muted mb-10 max-w-3xl mx-auto animate-slide-up">
            India's first AI-powered platform for MSMEs to discover schemes, check eligibility, 
            manage compliance, and handle documents — all with official government citations.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up">
            <Link to="/dashboard">
              <Button variant="lime" size="xl" rightIcon={<ArrowRight className="w-5 h-5" />}>
                Get Started Free
              </Button>
            </Link>
            <Link to="/schemes">
              <Button variant="outline" size="xl">
                Explore Schemes
              </Button>
            </Link>
          </div>
          
          <div className="mt-12 flex items-center justify-center gap-8 text-sm text-text-muted animate-fade-in">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-accent-lime" aria-hidden="true" />
              <span>Official Sources</span>
            </div>
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-accent-lime" aria-hidden="true" />
              <span>Deterministic Rules</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-accent-lime" aria-hidden="true" />
              <span>Real-time Data</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Floating elements */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce">
        <svg className="w-6 h-6 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
}
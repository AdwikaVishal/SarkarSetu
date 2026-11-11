"use client";

import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/landing/Hero";
import { FeatureShowcase } from "@/components/landing/FeatureShowcase";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { TrustSection } from "@/components/landing/TrustSection";
import { DocumentPreview } from "@/components/landing/DocumentPreview";
import { ServiceGrid } from "@/components/landing/ServiceGrid";
import { RecommendationPreview } from "@/components/landing/RecommendationPreview";
import { FinalCTA } from "@/components/landing/FinalCTA";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Navbar />
      <main className="flex-1 pt-16">
        <Hero />
        <FeatureShowcase />
        <HowItWorks />
        <TrustSection />
        <DocumentPreview />
        <ServiceGrid />
        <RecommendationPreview />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
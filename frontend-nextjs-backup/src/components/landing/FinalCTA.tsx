"use client";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { ArrowRight, Sparkles, Shield, CheckCircle, TrendingUp } from "lucide-react";

export function FinalCTA() {
  return (
    <section className="relative py-20 md:py-32 lg:py-40 px-6 md:px-8 overflow-hidden bg-bg-dark text-text-inverse">
      <div className="max-w-7xl mx-auto">
        {/* Background decorative elements */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-10 w-64 h-64 rounded-full bg-accent-lime/5 blur-3xl animate-float" aria-hidden="true" />
          <div className="absolute bottom-1/4 right-10 w-48 h-48 rounded-full bg-accent-purple/5 blur-3xl animate-float" style={{ animationDelay: "2s" }} aria-hidden="true" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-accent-lime/3 blur-3xl" aria-hidden="true" />
          
          {/* Floating shapes */}
          <div className="absolute top-20 right-20 w-24 h-24 rounded-full border border-accent-lime/20 animate-float" aria-hidden="true" />
          <div className="absolute bottom-20 left-20 w-16 h-16 rounded-full border border-accent-purple/20 animate-float" style={{ animationDelay: "1s" }} aria-hidden="true" />
          <div className="absolute top-1/3 right-1/3 w-8 h-8 rounded-full bg-accent-lime/20 animate-float" style={{ animationDelay: "3s" }} aria-hidden="true" />
        </div>

        <div className="relative z-10 text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-lime/10 text-accent-lime border border-accent-lime/30 font-medium text-sm mb-8 animate-slide-up">
            <Sparkles className="w-4 h-4" aria-hidden="true" />
            Ready to simplify your government compliance?
          </div>

          {/* Main Heading */}
          <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.02] mb-8 animate-slide-up" style={{ animationDelay: "100ms" }}>
            YOUR BUSINESS DESERVES<br />
            A <span className="text-accent-lime">SIMPLER WAY FORWARD.</span>
          </h2>

          {/* Supporting Text */}
          <p className="text-text-muted text-lg md:text-xl leading-relaxed mb-12 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: "200ms" }}>
            Start with your business profile. Discover what applies to you. 
            Move forward with clarity.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-slide-up" style={{ animationDelay: "300ms" }}>
            <Button size="xl" variant="lime" rightIcon={<ArrowRight className="w-5 h-5" />} className="w-full sm:w-auto">
              Start Your Journey
            </Button>
            <Button size="xl" variant="outline" className="w-full sm:w-auto border-border-dark/50 hover:border-accent-lime hover:text-accent-lime">
              Already have an account? Log in
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm animate-fade-in" style={{ animationDelay: "400ms" }}>
            <TrustIndicator icon={CheckCircle} label="No credit card required" />
            <TrustIndicator icon={Shield} label="Data encrypted & secure" />
            <TrustIndicator icon={TrendingUp} label="Cancel anytime" />
          </div>
        </div>
      </div>
    </section>
  );
}

function TrustIndicator({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="flex items-center gap-2 text-text-muted">
      <Icon className="w-4 h-4 text-accent-lime" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
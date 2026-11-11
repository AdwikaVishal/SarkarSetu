"use client";

import { Link } from "react-router-dom";
import { ArrowRight, Sparkles, Shield, Target, CheckCircle } from "lucide-react";
import { Button } from "../ui/Button";

export function FinalCTA() {
  return (
    <section className="py-20 lg:py-32 bg-bg-primary">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-accent-lime/10 via-accent-purple/10 to-accent-lime/10 rounded-[32px] blur-2xl" />
          
          <div className="relative p-8 lg:p-16 rounded-[32px] bg-bg-elevated border border-border">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-lime/10 text-accent-lime text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" aria-hidden="true" />
              <span>Ready to simplify your compliance?</span>
            </div>
            
            <h2 className="font-heading font-bold text-3xl sm:text-4xl lg:text-5xl text-text-primary mb-6">
              Join thousands of Indian entrepreneurs
              <br />
              <span className="text-accent-lime">navigating government services with confidence</span>
            </h2>
            
            <p className="text-lg text-text-muted mb-10 max-w-2xl mx-auto">
              Create your free account and get personalized scheme recommendations, 
              compliance roadmaps, and AI-powered document intelligence — all backed by official government sources.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
              <Link to="/dashboard">
                <Button variant="lime" size="xl" rightIcon={<ArrowRight className="w-5 h-5" />}>
                  Get Started Free
                </Button>
              </Link>
              <Link to="/schemes">
                <Button variant="outline" size="xl">
                  Explore Schemes First
                </Button>
              </Link>
            </div>
            
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-text-muted">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-success" aria-hidden="true" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-success" aria-hidden="true" />
                <span>Cancel anytime</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-success" aria-hidden="true" />
                <span>Data export available</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-12 grid sm:grid-cols-3 gap-6 text-center">
          <div className="p-4">
            <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center mx-auto mb-3">
              <Target className="w-6 h-6 text-accent-lime" aria-hidden="true" />
            </div>
            <h4 className="font-heading font-bold text-lg text-text-primary mb-1">Official Sources</h4>
            <p className="text-text-muted text-sm">All data from government portals</p>
          </div>
          <div className="p-4">
            <div className="w-12 h-12 rounded-xl bg-accent-purple/10 flex items-center justify-center mx-auto mb-3">
              <Shield className="w-6 h-6 text-accent-purple" aria-hidden="true" />
            </div>
            <h4 className="font-heading font-bold text-lg text-text-primary mb-1">Deterministic Rules</h4>
            <p className="text-text-muted text-sm">No AI hallucinations</p>
          </div>
          <div className="p-4">
            <div className="w-12 h-12 rounded-xl bg-warning/10 flex items-center justify-center mx-auto mb-3">
              <Sparkles className="w-6 h-6 text-warning" aria-hidden="true" />
            </div>
            <h4 className="font-heading font-bold text-lg text-text-primary mb-1">Real Citations</h4>
            <p className="text-text-muted text-sm">Verify every recommendation</p>
          </div>
        </div>
      </div>
    </section>
  );
}
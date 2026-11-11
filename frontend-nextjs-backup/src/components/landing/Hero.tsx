"use client";

import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { ArrowRight, CheckCircle, Sparkles, MessageSquare, FileText, Shield, TrendingUp } from "lucide-react";

const features = [
  { icon: CheckCircle, label: "Business Profile", value: "85% Complete", color: "lime" },
  { icon: FileText, label: "Udyam Registration", value: "Ready to Submit", color: "purple" },
  { icon: Shield, label: "GST Readiness", value: "Documents Pending", color: "warning" },
  { icon: TrendingUp, label: "Eligible Schemes", value: "12 Found", color: "success" },
];

const chatPreview = [
  { role: "user", content: "What schemes apply to my manufacturing business in Karnataka?" },
  { role: "assistant", content: "Based on your profile, here are 3 relevant schemes:\n\n1. **PMEGP** - Up to ₹25L subsidy for manufacturing\n2. **Karnataka MSME Policy** - Interest subsidy & tax benefits\n3. **Credit Guarantee Scheme** - Collateral-free loans\n\nWould you like details on any of these?" },
];

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center pt-16 md:pt-20 pb-20 md:pb-32 px-6 md:px-8 overflow-hidden">
      <div className="max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Content */}
          <div className="relative z-10 animate-slide-up">
            <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-6">
              YOUR BUSINESS. GOVERNMENT SERVICES. SIMPLIFIED.
            </span>
            
            <h1 className="font-heading font-bold tracking-tight text-5xl md:text-6xl lg:text-7xl leading-[1.02] text-text-primary mb-8">
              Build Your <span className="text-accent-lime">Business.</span><br />
              We&apos;ll Handle the<br />
              <span className="text-accent-lime">GOVERNMENT COMPLEXITY.</span>
            </h1>

            <p className="text-text-muted text-lg md:text-xl leading-relaxed max-w-xl mb-10">
              From business registration to government schemes, SarkarSetu AI helps Indian entrepreneurs 
              discover opportunities, understand requirements, and complete essential compliance tasks — all in one place.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Button size="xl" variant="lime" rightIcon={<ArrowRight className="w-5 h-5" />} className="w-full sm:w-auto">
                Explore SarkarSetu
              </Button>
              <Button size="xl" variant="outline" className="w-full sm:w-auto">
                See How It Works
              </Button>
            </div>

            <p className="text-text-muted text-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent-lime" aria-hidden="true" />
              Built for India&apos;s entrepreneurs, startups and MSMEs.
            </p>
          </div>

          {/* Right: Visual Preview */}
          <div className="relative z-10 animate-fade-in" style={{ animationDelay: "200ms" }}>
            <div className="relative">
              {/* Floating decorative shapes */}
              <div className="absolute -top-6 -right-6 w-48 h-48 rounded-full bg-accent-lime/10 blur-3xl animate-float" aria-hidden="true" />
              <div className="absolute bottom-20 -left-10 w-32 h-32 rounded-full bg-accent-purple/10 blur-3xl animate-float" style={{ animationDelay: "2s" }} aria-hidden="true" />
              <div className="absolute top-1/2 -right-20 w-24 h-24 rounded-full bg-accent-lime/5 blur-3xl animate-float" style={{ animationDelay: "4s" }} aria-hidden="true" />

              {/* Main Dashboard Preview */}
              <div className="relative bg-bg-elevated rounded-[28px] border border-border shadow-xl p-6 md:p-8">
                {/* Top bar */}
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-error" aria-hidden="true" />
                    <div className="w-3 h-3 rounded-full bg-warning" aria-hidden="true" />
                    <div className="w-3 h-3 rounded-full bg-success" aria-hidden="true" />
                  </div>
                  <div className="text-text-muted text-sm font-mono">dashboard.sarkarsetu.ai</div>
                </div>

                {/* Business Profile Card */}
                <div className="bg-bg-card rounded-[20px] p-6 mb-6 border border-border">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                      </div>
                      <div>
                        <h3 className="font-heading font-bold text-lg">Kumar Textiles Pvt Ltd</h3>
                        <p className="text-text-muted text-sm">Manufacturing • Bengaluru, Karnataka</p>
                      </div>
                    </div>
                    <Badge variant="lime" size="sm">85% Complete</Badge>
                  </div>
                  <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                    <div className="h-full bg-accent-lime rounded-full transition-all duration-1000" style={{ width: "85%" }} aria-hidden="true" />
                  </div>
                </div>

                {/* Feature Grid */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {features.map((feature, i) => (
                    <div
                      key={i}
                      className="bg-bg-card rounded-[16px] p-4 border border-border hover:border-accent-lime/50 transition-colors"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <feature.icon 
                          className={cn("w-5 h-5", 
                            feature.color === "lime" && "text-accent-lime",
                            feature.color === "purple" && "text-accent-purple",
                            feature.color === "warning" && "text-warning",
                            feature.color === "success" && "text-success"
                          )} 
                          aria-hidden="true" 
                        />
                        <span className="font-medium text-sm text-text-primary">{feature.label}</span>
                      </div>
                      <span className="text-text-muted text-sm">{feature.value}</span>
                    </div>
                  ))}
                </div>

                {/* AI Chat Preview */}
                <div className="bg-bg-dark rounded-[20px] p-4 border border-border-dark">
                  <div className="flex items-center gap-2 text-text-muted text-sm mb-4">
                    <MessageSquare className="w-4 h-4 text-accent-purple" aria-hidden="true" />
                    <span className="font-medium text-text-inverse">AI Assistant</span>
                    <span className="w-2 h-2 rounded-full bg-success" aria-hidden="true" />
                  </div>
                  <div className="space-y-3 max-h-48 overflow-y-auto">
                    {chatPreview.map((msg, i) => (
                      <div
                        key={i}
                        className={cn(
                          "flex gap-3",
                          msg.role === "assistant" && "flex-row-reverse"
                        )}
                      >
                        <div
                          className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                            msg.role === "user" ? "bg-accent-lime" : "bg-accent-purple"
                          )}
                        >
                          {msg.role === "user" ? (
                            <Sparkles className="w-4 h-4 text-text-primary" aria-hidden="true" />
                          ) : (
                            <MessageSquare className="w-4 h-4 text-text-inverse" aria-hidden="true" />
                          )}
                        </div>
                        <div
                          className={cn(
                            "max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                            msg.role === "user"
                              ? "bg-accent-lime/10 text-text-primary rounded-tr-sm"
                              : "bg-accent-purple/10 text-text-inverse rounded-tl-sm"
                          )}
                        >
                          {msg.content.split("\n").map((line, li) => (
                            <p key={li} className="whitespace-pre-wrap">{line}</p>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex items-center gap-2 border-t border-border-dark/50 pt-3">
                    <input
                      type="text"
                      placeholder="Ask about schemes, compliance..."
                      className="flex-1 bg-bg-card border border-border-dark rounded-full px-4 py-2 text-sm text-text-inverse placeholder-text-muted focus:outline-none focus:border-accent-lime"
                      readOnly
                      aria-label="Chat input preview"
                    />
                    <button className="w-8 h-8 rounded-full bg-accent-purple flex items-center justify-center" aria-label="Send">
                      <ArrowRight className="w-4 h-4 text-text-inverse" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Floating badges */}
              <div className="absolute -bottom-6 -left-6 animate-float" style={{ animationDelay: "1s" }}>
                <div className="bg-bg-elevated rounded-[16px] p-4 border border-border shadow-xl flex items-center gap-3 min-w-[200px]">
                  <div className="w-10 h-10 rounded-xl bg-accent-purple/10 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-accent-purple" aria-hidden="true" />
                  </div>
                  <div>
                    <p className="font-heading font-bold text-sm">AI Assistant</p>
                    <p className="text-text-muted text-xs">Ready to help</p>
                  </div>
                </div>
              </div>

              <div className="absolute -top-4 right-4 animate-float" style={{ animationDelay: "3s" }}>
                <div className="bg-bg-elevated rounded-[16px] p-4 border border-border shadow-xl flex items-center gap-3 min-w-[180px]">
                  <div className="w-10 h-10 rounded-xl bg-accent-lime/10 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-accent-lime" aria-hidden="true" />
                  </div>
                  <div>
                    <p className="font-heading font-bold text-sm">Udyam Ready</p>
                    <p className="text-text-muted text-xs">Submit this week</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
"use client";

import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Building2, X, Mail, Globe } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    Product: [
      { name: "Features", href: "/#features" },
      { name: "Schemes", href: "/schemes" },
      { name: "Eligibility Checker", href: "/eligibility" },
      { name: "Documents", href: "/documents" },
      { name: "Roadmaps", href: "/roadmap" },
      { name: "AI Assistant", href: "/assistant" },
    ],
    Resources: [
      { name: "Documentation", href: "/docs" },
      { name: "API Reference", href: "/api-docs" },
      { name: "Blog", href: "/blog" },
      { name: "Help Center", href: "/help" },
      { name: "Community", href: "/community" },
    ],
    Company: [
      { name: "About", href: "/about" },
      { name: "Careers", href: "/careers" },
      { name: "Press", href: "/press" },
      { name: "Contact", href: "/contact" },
      { name: "Partners", href: "/partners" },
    ],
    Legal: [
      { name: "Privacy Policy", href: "/privacy" },
      { name: "Terms of Service", href: "/terms" },
      { name: "Cookie Policy", href: "/cookies" },
      { name: "Security", href: "/security" },
    ],
  };

  const socialLinks = [
    { name: "X", href: "https://twitter.com/sarkarsetu", icon: X },
    { name: "LinkedIn", href: "https://linkedin.com/company/sarkarsetu", icon: Mail },
    { name: "GitHub", href: "https://github.com/sarkarsetu", icon: Globe },
  ];

  return (
    <footer className="bg-bg-elevated border-t border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
          <div className="col-span-2 lg:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-4" aria-label="SarkarSetu Home">
              <div className="w-8 h-8 rounded-xl bg-accent-lime flex items-center justify-center">
                <Building2 className="w-5 h-5 text-text-primary" aria-hidden="true" />
              </div>
              <span className="font-heading font-bold text-xl text-text-primary">SarkarSetu</span>
            </Link>
            <p className="text-text-muted text-sm mb-6">
              Empowering Indian entrepreneurs and MSMEs to navigate government services, 
              business registrations, schemes, and compliance with confidence.
            </p>
            <div className="flex gap-4">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors"
                  aria-label={social.name}
                >
                  <social.icon className="w-5 h-5" aria-hidden="true" />
                </a>
              ))}
            </div>
          </div>

          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="font-heading font-semibold text-text-primary mb-4">{category}</h4>
              <ul className="space-y-3" role="list">
                {links.map((link) => (
                  <li key={link.name}>
                    <Link
                      to={link.href}
                      className="text-sm text-text-muted hover:text-text-primary transition-colors"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 pt-8 border-t border-border">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <p className="text-sm text-text-muted">
              &copy; {currentYear} SarkarSetu. All rights reserved.
            </p>
            <p className="text-sm text-text-muted">
              Made with care for Indian entrepreneurs
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
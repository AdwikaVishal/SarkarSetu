"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Menu, X, Sparkles, ArrowRight } from "lucide-react";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/features", label: "Features" },
  { href: "/how-it-works", label: "How It Works" },
  { href: "/schemes", label: "Government Schemes" },
  { href: "/about", label: "About" },
];

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setIsMobileMenuOpen(false);
    }, 0);
    return () => clearTimeout(timeoutId);
  }, [pathname]);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled
          ? "bg-bg-primary/90 backdrop-blur-md border-b border-border shadow-sm"
          : "bg-transparent"
      )}
    >
      <nav
        className="max-w-7xl mx-auto px-6 md:px-8"
        aria-label="Main navigation"
      >
        <div className="flex h-16 md:h-20 items-center justify-between">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 text-text-primary hover:opacity-80 transition-opacity"
            aria-label="SarkarSetu AI Home"
          >
            <div className="w-10 h-10 rounded-xl bg-accent-lime flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-text-primary" aria-hidden="true" />
            </div>
            <span className="font-heading font-bold text-xl tracking-tight hidden sm:block">
              SarkarSetu AI
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <div className="flex items-center gap-6">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "font-medium text-sm transition-colors relative",
                    pathname === link.href
                      ? "text-text-primary"
                      : "text-text-muted hover:text-text-primary"
                  )}
                >
                  {link.label}
                  {pathname === link.href && (
                    <span
                      className="absolute bottom-[-6px] left-0 right-0 h-0.5 bg-accent-lime rounded-full"
                    />
                  )}
                </Link>
              ))}
            </div>
            <div className="flex items-center gap-3 ml-4">
              <Link 
                href="/login" 
                className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-full text-text-primary hover:bg-bg-card transition-colors"
              >
                Log in
              </Link>
              <Link 
                href="/register" 
                className="inline-flex items-center justify-center gap-2 px-6 py-3 text-base font-medium rounded-full bg-accent-lime text-text-primary hover:bg-accent-lime-hover active:bg-accent-lime-hover focus-visible:ring-2 focus-visible:ring-accent-lime focus-visible:ring-offset-2 shadow-lg shadow-lime/30"
              >
                Get Started
                <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </Link>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-lg text-text-primary hover:bg-bg-card transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-menu"
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        <div
          id="mobile-menu"
          className={cn(
            "md:hidden overflow-hidden transition-all duration-300 ease-out",
            isMobileMenuOpen
              ? "max-h-96 opacity-100 pb-6"
              : "max-h-0 opacity-0"
          )}
        >
          <div className="flex flex-col gap-4 pt-4 border-t border-border">
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "px-4 py-3 rounded-xl text-base font-medium transition-colors",
                    pathname === link.href
                      ? "bg-accent-lime/10 text-text-primary"
                      : "text-text-muted hover:bg-bg-card hover:text-text-primary"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
            <div className="flex flex-col gap-3 pt-4 border-t border-border">
              <Link 
                href="/login" 
                className="inline-flex items-center justify-center w-full px-6 py-4 text-lg font-medium rounded-full border-2 border-text-primary text-text-primary hover:bg-text-primary hover:text-bg-primary transition-colors"
              >
                Log in
              </Link>
              <Link 
                href="/register" 
                className="inline-flex items-center justify-center gap-2 w-full px-6 py-4 text-lg font-medium rounded-full bg-accent-lime text-text-primary hover:bg-accent-lime-hover active:bg-accent-lime-hover focus-visible:ring-2 focus-visible:ring-accent-lime focus-visible:ring-offset-2 shadow-lg shadow-lime/30"
              >
                Get Started
                <ArrowRight className="w-4 h-4" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
}
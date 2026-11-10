"use client";

import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { cn } from "@/lib/utils";
import { Home, Search, Sparkles } from "lucide-react";

export default function NotFound() {
  return (
    <PageContainer>
      <Navbar />
      <main id="main-content" className="flex-1 flex items-center justify-center px-4 py-20">
        <div className="text-center max-w-md">
          <div className="w-24 h-24 rounded-full bg-accent-lime/10 flex items-center justify-center mx-auto mb-8">
            <Sparkles className="w-12 h-12 text-accent-lime" aria-hidden="true" />
          </div>
          <h1 className="font-heading font-bold text-5xl md:text-7xl text-text-primary mb-4">404</h1>
          <h2 className="font-heading font-bold text-2xl md:text-3xl text-text-primary mb-4">Page Not Found</h2>
          <p className="text-text-muted mb-8">
            Sorry, we couldn&apos;t find the page you&apos;re looking for. It might have been moved or doesn&apos;t exist.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/" 
              className="inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-medium rounded-full bg-accent-lime text-text-primary hover:bg-accent-lime-hover active:bg-accent-lime-hover focus-visible:ring-2 focus-visible:ring-accent-lime focus-visible:ring-offset-2 shadow-lg shadow-lime/30"
            >
              <Home className="w-4 h-4" aria-hidden="true" />
              Go Home
            </Link>
            <Link 
              href="/features" 
              className="inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-medium rounded-full border-2 border-text-primary text-text-primary hover:bg-text-primary hover:text-bg-primary transition-colors"
            >
              <Search className="w-4 h-4" aria-hidden="true" />
              Explore Features
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </PageContainer>
  );
}
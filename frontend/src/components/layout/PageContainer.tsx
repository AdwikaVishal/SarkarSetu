"use client";

import { type ReactNode } from "react";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";
import { cn } from "@/lib/utils";

interface PageContainerProps {
  children: ReactNode;
  className?: string;
  showNavbar?: boolean;
  showFooter?: boolean;
}

export function PageContainer({
  children,
  className,
  showNavbar = true,
  showFooter = true,
}: PageContainerProps) {
  return (
    <div className={cn("flex flex-col min-h-screen", className)}>
      {showNavbar && <Navbar />}
      <main className="flex-1 pt-16 md:pt-20" id="main-content">
        {children}
      </main>
      {showFooter && <Footer />}
    </div>
  );
}
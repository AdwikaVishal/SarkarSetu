"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Eye,
  Download,
  Sparkles,
  Shield,
  Search,
  ArrowRight
} from "lucide-react";

const features = [
  { icon: FileText, title: "PDF Upload & Parsing", description: "Drag-and-drop PDF upload with automatic text extraction and structure detection." },
  { icon: Search, title: "OCR for Scanned Documents", description: "Extract text from scanned PDFs and images using advanced OCR technology." },
  { icon: Sparkles, title: "AI-Powered Field Extraction", description: "Automatically identify and extract key fields like GSTIN, PAN, dates, amounts, and addresses." },
  { icon: Shield, title: "Document Matching", description: "Match uploaded documents against scheme requirements and identify missing information." },
  { icon: AlertCircle, title: "Missing Info Indicators", description: "Clear visual indicators for incomplete documents, expired certificates, or mismatched data." },
  { icon: CheckCircle, title: "Verification Status", description: "Track document verification status with clear pending/verified/expired labels." },
];

const processingSteps = [
  { step: 1, title: "Upload", description: "Drag & drop or select PDF files", status: "completed" },
  { step: 2, title: "Extract", description: "OCR & text extraction in progress", status: "current" },
  { step: 3, title: "Analyze", description: "AI field extraction & classification", status: "pending" },
  { step: 4, title: "Match", description: "Match against requirements", status: "pending" },
  { step: 5, title: "Report", description: "Generate extraction report", status: "pending" },
];

const extractedData = [
  { label: "GSTIN", value: "29ABCDE1234F1Z5", status: "verified", source: "GST Portal" },
  { label: "Legal Name", value: "Kumar Textiles Private Limited", status: "verified", source: "MCA" },
  { label: "Trade Name", value: "Kumar Textiles", status: "verified", source: "GST Portal" },
  { label: "Address", value: "Plot 45, Industrial Area, Bengaluru - 560001", status: "verified", source: "GST Portal" },
  { label: "Registration Date", value: "15 March 2023", status: "verified", source: "GST Portal" },
  { label: "Business Type", value: "Manufacturer", status: "verified", source: "GST Portal" },
  { label: "PAN", value: "ABCDE1234F", status: "pending", source: "Document" },
  { label: "Authorized Signatory", value: "Rajesh Kumar", status: "pending", source: "Document" },
];

export function DocumentPreview() {
  return (
    <section className="relative py-20 md:py-32 px-6 md:px-8 overflow-hidden bg-bg-primary">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          {/* Left: Features */}
          <div className="space-y-8">
            <div className="animate-slide-up">
              <span className="inline-block font-heading font-medium text-sm uppercase tracking-widest text-accent-lime mb-4">
                DOCUMENT INTELLIGENCE
              </span>
              <h2 className="font-heading font-bold tracking-tight text-4xl md:text-5xl lg:text-6xl leading-[1.05] text-text-primary mb-6">
                Your Documents.<br />
                <span className="text-accent-lime">Understood.</span>
              </h2>
              <p className="text-text-muted text-lg md:text-xl leading-relaxed mb-10">
                Upload business documents and let SarkarSetu AI help extract details, 
                identify missing information, and organize what you need.
              </p>

              <div className="flex flex-wrap gap-3">
                <Button variant="lime" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Try Document Upload
                </Button>
                <Button variant="outline">
                  View Supported Formats
                </Button>
              </div>
            </div>

            {/* Features Grid */}
            <div className="grid sm:grid-cols-2 gap-4 animate-fade-in" style={{ animationDelay: "200ms" }}>
              {features.map((feature, i) => (
                <div key={i} className="bg-bg-card rounded-[16px] p-5 border border-border hover:border-accent-lime/50 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-accent-purple/10 text-accent-purple flex items-center justify-center mb-4">
                    <feature.icon className="w-5 h-5" aria-hidden="true" />
                  </div>
                  <h4 className="font-heading font-bold text-text-primary mb-1">{feature.title}</h4>
                  <p className="text-text-muted text-sm">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Document Upload Preview */}
          <div className="relative animate-fade-in" style={{ animationDelay: "300ms" }}>
            <Card variant="elevated" padding="none" className="overflow-hidden">
              {/* Upload Zone */}
              <div className="p-8 border-b border-border">
                <div className="relative">
                  {/* Dashed border area */}
                  <div className="relative rounded-[20px] border-2 border-dashed border-border p-12 text-center bg-bg-card/50">
                    <div className="w-16 h-16 rounded-full bg-accent-lime/10 flex items-center justify-center mx-auto mb-4">
                      <Upload className="w-8 h-8 text-accent-lime" aria-hidden="true" />
                    </div>
                    <h3 className="font-heading font-bold text-xl text-text-primary mb-2">Drop PDF files here</h3>
                    <p className="text-text-muted mb-6">or click to browse</p>
                    <Button variant="outline" size="lg" leftIcon={<Upload className="w-4 h-4" />}>
                      Select Files
                    </Button>
                    <p className="text-text-muted text-xs mt-4">Supports: PDF, JPG, PNG • Max 10MB per file</p>
                  </div>
                </div>
              </div>

              {/* Processing Steps */}
              <div className="px-8 py-6 border-b border-border bg-bg-card/30">
                <h4 className="font-heading font-bold text-text-primary mb-4">Processing Pipeline</h4>
                <div className="flex items-center gap-2 overflow-x-auto pb-2">
                  {processingSteps.map((step, i) => (
                    <ProcessingStep key={i} step={step} isLast={i === processingSteps.length - 1} />
                  ))}
                </div>
              </div>

              {/* Uploaded Files */}
              <div className="p-8 space-y-4">
                <h4 className="font-heading font-bold text-text-primary mb-4">Uploaded Documents</h4>
                <div className="space-y-3">
                  <DocumentFileCard 
                    name="GST_Registration_Certificate.pdf"
                    size="245 KB"
                    status="completed"
                    extractedCount={8}
                    onView={() => {}}
                  />
                  <DocumentFileCard 
                    name="PAN_Card.pdf"
                    size="180 KB"
                    status="completed"
                    extractedCount={4}
                    onView={() => {}}
                  />
                  <DocumentFileCard 
                    name="Rent_Agreement.pdf"
                    size="2.1 MB"
                    status="processing"
                    extractedCount={0}
                    onView={() => {}}
                  />
                </div>
              </div>

              {/* Extracted Data Preview */}
              <div className="px-8 pb-8">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-heading font-bold text-text-primary">Extracted Information (Sample)</h4>
                  <Badge variant="outline" size="sm">8 fields extracted</Badge>
                </div>
                <div className="bg-bg-card rounded-[16px] border border-border overflow-hidden max-h-64 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-bg-elevated border-b border-border">
                        <th className="px-4 py-3 text-left font-medium text-text-muted">Field</th>
                        <th className="px-4 py-3 text-left font-medium text-text-muted">Extracted Value</th>
                        <th className="px-4 py-3 text-left font-medium text-text-muted">Status</th>
                        <th className="px-4 py-3 text-left font-medium text-text-muted">Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {extractedData.map((item, i) => (
                        <tr key={i} className="border-b border-border/50 hover:bg-bg-elevated/50">
                          <td className="px-4 py-3 font-medium text-text-primary">{item.label}</td>
                          <td className="px-4 py-3 text-text-muted font-mono">{item.value}</td>
                          <td className="px-4 py-3">
                            <Badge 
                              variant={item.status === "verified" ? "success" : "lime"} 
                              size="sm" 
                              dot
                            >
                              {item.status === "verified" ? "Verified" : "From Document"}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-text-muted text-xs">{item.source}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}

function ProcessingStep({ step, isLast }: { step: typeof processingSteps[0]; isLast: boolean }) {
  const statusConfig: Record<"completed" | "current" | "pending", { icon: React.ComponentType<{ className?: string }>; color: string; bg: string; border: string }> = {
    completed: { icon: CheckCircle, color: "text-success", bg: "bg-success", border: "border-success" },
    current: { icon: Loader2, color: "text-accent-lime", bg: "bg-accent-lime", border: "border-accent-lime animate-pulse" },
    pending: { icon: AlertCircle, color: "text-text-muted", bg: "bg-text-muted/20", border: "border-text-muted/20" },
  };

  const config = statusConfig[step.status as "completed" | "current" | "pending"];

  return (
    <div className="flex items-center flex-shrink-0">
      <div className="relative flex items-center">
        <div className={cn("w-10 h-10 rounded-full flex items-center justify-center border-2", config.border)}>
          {step.status === "current" ? (
            <config.icon className={cn("w-5 h-5", config.color)} aria-hidden="true" />
          ) : (
            <config.icon className={cn("w-5 h-5", config.color)} aria-hidden="true" />
          )}
        </div>
        {!isLast && (
          <div className="absolute right-[-14px] left-[6px] top-1/2 h-0.5 bg-border" aria-hidden="true" />
        )}
      </div>
      <div className="ml-3 hidden sm:block min-w-[100px]">
        <p className={cn("font-medium text-xs", step.status === "current" ? "text-text-primary" : "text-text-muted")}>
          {step.title}
        </p>
        <p className="text-xs text-text-muted">{step.description}</p>
      </div>
    </div>
  );
}

function DocumentFileCard({ name, size, status, extractedCount, onView }: {
  name: string;
  size: string;
  status: "completed" | "processing" | "error";
  extractedCount: number;
  onView: () => void;
}) {
  const statusConfig = {
    completed: { icon: CheckCircle, color: "text-success", bg: "bg-success/10", label: "Completed" },
    processing: { icon: Loader2, color: "text-accent-lime", bg: "bg-accent-lime/10 animate-pulse", label: "Processing..." },
    error: { icon: AlertCircle, color: "text-error", bg: "bg-error/10", label: "Error" },
  };

  const config = statusConfig[status];

  return (
    <div className="bg-bg-card rounded-[12px] p-4 border border-border flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <div className="w-12 h-12 rounded-xl bg-bg-elevated flex items-center justify-center flex-shrink-0">
          <FileText className="w-6 h-6 text-text-muted" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="font-medium text-sm text-text-primary truncate">{name}</p>
          <p className="text-text-muted text-xs">{size}</p>
        </div>
        {extractedCount > 0 && (
          <Badge variant="outline" size="sm" className="ml-2">
            {extractedCount} fields
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className={cn("flex items-center gap-1.5 text-xs font-medium", config.color, config.bg, "px-2 py-1 rounded-full")}>
          <config.icon className="w-3 h-3" aria-hidden="true" />
          <span>{config.label}</span>
        </div>
        <Button variant="ghost" size="sm" onClick={onView}>
          <Eye className="w-4 h-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
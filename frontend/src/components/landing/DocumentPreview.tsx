"use client";

import { cn } from "@/lib/utils";
import { FileText, Search, Sparkles, Shield, CheckCircle, ArrowRight, ExternalLink } from "lucide-react";
import { Button } from "../ui/Button";
import { Card, CardContent } from "../ui/Card";
import { Badge } from "../ui/Badge";

const extractedFields = [
  { field: "GSTIN", value: "29ABCDE1234F1Z5", verified: true, source: "OCR + Validation" },
  { field: "PAN", value: "ABCDE1234F", verified: true, source: "OCR + Validation" },
  { field: "Business Name", value: "Kumar Textiles Pvt Ltd", verified: true, source: "Text Extraction" },
  { field: "Address", value: "123 Industrial Area, Bengaluru", verified: false, source: "OCR (needs review)" },
  { field: "Date of Establishment", value: "2020-01-15", verified: true, source: "Text Extraction" },
  { field: "Authorized Signatory", value: "Rajesh Kumar", verified: false, source: "OCR (low confidence)" },
];

const matchingResults = [
  { name: "PAN Card", status: "available", mandatory: true },
  { name: "GST Registration Certificate", status: "available", mandatory: true },
  { name: "Aadhaar Card", status: "missing", mandatory: true },
  { name: "Business Address Proof", status: "incomplete", mandatory: true },
  { name: "Bank Statement", status: "available", mandatory: false },
];

export function DocumentPreview() {
  return (
    <section className="py-20 lg:py-32 bg-bg-elevated">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl text-text-primary mb-4">
            Document Intelligence in Action
          </h2>
          <p className="text-lg text-text-muted">
            See how AI extracts, validates, and matches your documents against compliance requirements.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Document Upload & Extraction */}
          <Card variant="outlined" padding="xl">
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-heading font-bold text-xl text-text-primary mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-accent-lime" aria-hidden="true" />
                  Extracted Fields
                </h3>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Field</th>
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Extracted Value</th>
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Status</th>
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {extractedFields.map((field) => (
                      <tr key={field.field} className="border-b border-border/50">
                        <td className="px-4 py-3 font-medium text-text-primary">{field.field}</td>
                        <td className="px-4 py-3 text-text-muted font-mono">{field.value}</td>
                        <td className="px-4 py-3">
                          <Badge 
                            variant={field.verified ? "success" : "warning"} 
                            size="sm" 
                            dot
                          >
                            {field.verified ? "Verified" : "Needs Review"}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-text-muted text-xs">{field.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Compliance Matching */}
          <Card variant="outlined" padding="xl">
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-heading font-bold text-xl text-text-primary mb-4 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-accent-lime" aria-hidden="true" />
                  Udyam Registration Matching
                </h3>
                <Badge variant="lime" size="sm">85% Coverage</Badge>
              </div>
              
              <div className="space-y-3">
                {matchingResults.map((doc) => (
                  <div key={doc.name} className="flex items-center justify-between p-3 rounded-xl bg-bg-card border border-border">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-bg-elevated flex items-center justify-center">
                        <FileText className="w-4 h-4 text-text-muted" aria-hidden="true" />
                      </div>
                      <div>
                        <p className="font-medium text-sm text-text-primary">{doc.name}</p>
                        <p className="text-xs text-text-muted">{doc.mandatory ? "Mandatory" : "Optional"}</p>
                      </div>
                    </div>
                    <Badge 
                      variant={doc.status === "available" ? "success" : doc.status === "missing" ? "error" : "warning"} 
                      size="sm"
                    >
                      {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 grid sm:grid-cols-3 gap-6">
          <Card variant="outlined" padding="lg" className="text-center">
            <CardContent>
              <div className="w-12 h-12 rounded-xl bg-accent-purple/10 flex items-center justify-center mx-auto mb-4">
                <Search className="w-6 h-6 text-accent-purple" aria-hidden="true" />
              </div>
              <h4 className="font-heading font-bold text-lg text-text-primary mb-2">Text Extraction</h4>
              <p className="text-text-muted text-sm">PyMuPDF + pdfplumber for high-accuracy text extraction</p>
            </CardContent>
          </Card>
          
          <Card variant="outlined" padding="lg" className="text-center">
            <CardContent>
              <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-accent-lime" aria-hidden="true" />
              </div>
              <h4 className="font-heading font-bold text-lg text-text-primary mb-2">Field Detection</h4>
              <p className="text-text-muted text-sm">AI identifies PAN, GSTIN, dates, amounts, addresses</p>
            </CardContent>
          </Card>
          
          <Card variant="outlined" padding="lg" className="text-center">
            <CardContent>
              <div className="w-12 h-12 rounded-xl bg-warning/10 flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-warning" aria-hidden="true" />
              </div>
              <h4 className="font-heading font-bold text-lg text-text-primary mb-2">Compliance Check</h4>
              <p className="text-text-muted text-sm">Match against Udyam, GST, and scheme requirements</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
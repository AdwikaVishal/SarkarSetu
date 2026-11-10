"use client";

import { useEffect, useState, Suspense } from "react";
import { useAuth } from "@/context/AuthContext";
import { api, type DocumentMatchingResponse } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState, SkeletonCard } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { FileUploader } from "@/components/ui/FileUploader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api";
import { 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Eye, 
  Download, 
  Trash2,
  Search,
  Sparkles,
  Shield,
  X,
  RefreshCw,
  AlertTriangle,
  Building2,
} from "lucide-react";

interface DocumentUI {
  id: string;
  name: string;
  size: number;
  type: string;
  status: "uploading" | "processing" | "completed" | "error" | "pending";
  progress: number;
  extractedFields?: Record<string, { value: string; verified: boolean; source: string }>;
  missingFields?: string[];
  error?: string;
  uploadedAt: Date;
  businessProfileId?: string;
  documentType?: string;
  extractedData?: Record<string, unknown> | null;
}

interface StatusConfigType {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
}

function getStatusConfig(status: DocumentUI["status"]): StatusConfigType {
  const configs = {
    uploading: { label: "Uploading...", icon: Loader2, color: "text-accent-lime", bg: "bg-accent-lime/10" },
    processing: { label: "Processing...", icon: Loader2, color: "text-accent-purple", bg: "bg-accent-purple/10 animate-pulse" },
    completed: { label: "Completed", icon: CheckCircle, color: "text-success", bg: "bg-success/10" },
    error: { label: "Error", icon: AlertCircle, color: "text-error", bg: "bg-error/10" },
    pending: { label: "Pending", icon: Loader2, color: "text-text-muted", bg: "bg-text-muted/10" },
  };
  return configs[status];
}

function DocumentFileCard({ 
  document, 
  formatFileSize, 
  getStatusConfig, 
  onView, 
  onDelete,
  onRetry
}: { 
  document: DocumentUI; 
  formatFileSize: (bytes: number) => string;
  getStatusConfig: (status: DocumentUI["status"]) => StatusConfigType;
  onView: () => void;
  onDelete: () => void;
  onRetry?: () => void;
}) {
  const statusConfig = getStatusConfig(document.status);
  const config = statusConfig;
  const extractedCount = document.extractedFields ? Object.keys(document.extractedFields).length : 0;

  return (
    <div className="bg-bg-card rounded-[12px] p-4 border border-border flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <div className="w-12 h-12 rounded-xl bg-bg-elevated flex items-center justify-center flex-shrink-0">
          <FileText className="w-6 h-6 text-text-muted" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="font-medium text-sm text-text-primary truncate">{document.name}</p>
          <p className="text-text-muted text-xs">{formatFileSize(document.size)}</p>
        </div>
        {extractedCount > 0 && (
          <Badge variant="outline" size="sm" className="ml-2">
            {extractedCount} fields
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className={cn("flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full", config.color, config.bg)}>
          <config.icon className="w-3 h-3" aria-hidden="true" />
          <span>{config.label}</span>
        </div>
        <Button variant="ghost" size="sm" onClick={onView}>
          <Eye className="w-4 h-4" aria-hidden="true" />
        </Button>
        {document.status === "error" && onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry}>
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={onDelete}>
          <Trash2 className="w-4 h-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}

function DocumentDetailModal({ 
  document, 
  onClose, 
  formatFileSize, 
  getStatusConfig,
  matchingData,
  onLoadMatching,
  loadingMatching,
} : { 
  document: DocumentUI; 
  onClose: () => void;
  formatFileSize: (bytes: number) => string;
  getStatusConfig: (status: DocumentUI["status"]) => StatusConfigType;
  matchingData: DocumentMatchingResponse | null;
  onLoadMatching?: (service: string) => void;
  loadingMatching?: boolean;
}) {
  const statusConfig = getStatusConfig(document.status);
  const StatusIcon = statusConfig.icon;

  const services = [
    { id: "udyam_registration", name: "Udyam Registration" },
    { id: "gst_registration", name: "GST Registration" },
    { id: "msme_scheme", name: "MSME Schemes" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div className="bg-bg-elevated rounded-[24px] max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between p-6 border-b border-border">
          <div>
            <h2 className="font-heading font-bold text-xl text-text-primary">{document.name}</h2>
            <p className="text-text-muted text-sm mt-1">{formatFileSize(document.size)} • {document.uploadedAt.toLocaleDateString("en-IN")}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors">
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center gap-4 p-4 rounded-xl bg-bg-card border border-border">
            <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center", statusConfig.bg)}>
              <StatusIcon className={cn("w-6 h-6", statusConfig.color)} aria-hidden="true" />
            </div>
            <div>
              <p className="font-medium text-text-primary">{statusConfig.label}</p>
              {document.status === "uploading" || document.status === "processing" ? (
                <div className="mt-2 flex items-center gap-3">
                  <div className="flex-1 h-2 bg-bg-elevated rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-accent-lime rounded-full transition-all duration-300" 
                      style={{ width: `${document.progress}%` }} 
                      aria-hidden="true"
                    />
                  </div>
                  <span className="text-sm font-bold text-accent-lime">{document.progress}%</span>
                </div>
              ) : null}
            </div>
          </div>

          {document.extractedFields && Object.keys(document.extractedFields).length > 0 && (
            <div>
              <h3 className="font-heading font-bold text-lg text-text-primary mb-4">Extracted Information</h3>
              <div className="overflow-x-auto rounded-xl border border-border bg-bg-card">
                <table className="w-full min-w-[36rem] text-sm">
                  <thead>
                    <tr className="bg-bg-elevated border-b border-border">
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Field</th>
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Extracted Value</th>
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Status</th>
                      <th className="px-4 py-3 text-left font-medium text-text-muted">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(document.extractedFields).map(([field, data]) => (
                      <tr key={field} className="border-b border-border/50 hover:bg-bg-elevated/50">
                        <td className="px-4 py-3 font-medium text-text-primary">{field}</td>
                        <td className="px-4 py-3 text-text-muted font-mono">{data.value}</td>
                        <td className="px-4 py-3">
                          <StatusBadge 
                            status={data.verified ? "success" : "needs_information"} 
                            size="sm" 
                            dot
                          />
                        </td>
                        <td className="px-4 py-3 text-text-muted text-xs">{data.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {document.missingFields && document.missingFields.length > 0 && (
            <div>
              <h3 className="font-heading font-bold text-lg text-text-primary mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-warning" aria-hidden="true" />
                Missing / Required Fields
              </h3>
              <div className="flex flex-wrap gap-2">
                {document.missingFields.map((field, i) => (
                  <Badge key={i} variant="error" size="sm">{field}</Badge>
                ))}
              </div>
            </div>
          )}

          {document.error && (
            <div className="p-4 rounded-xl bg-error/5 border border-error/20">
              <p className="text-error text-sm">{document.error}</p>
            </div>
          )}

          {/* Document Matching Section */}
          <div>
            <h3 className="font-heading font-bold text-lg text-text-primary mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-accent-lime" aria-hidden="true" />
              Compliance Matching
              {document.status !== "completed" && (
                <Badge variant="outline" size="sm" className="ml-2">
                  Complete processing first
                </Badge>
              )}
            </h3>
            <div className="space-y-3">
              {services.map((service) => (
                <div key={service.id} className="p-4 rounded-xl bg-bg-card border border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-accent-lime/10 flex items-center justify-center">
                        <Shield className="w-5 h-5 text-accent-lime" aria-hidden="true" />
                      </div>
                      <div>
                        <p className="font-medium text-text-primary">{service.name}</p>
                        <p className="text-text-muted text-sm">Check document completeness</p>
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => onLoadMatching?.(service.id)}
                      disabled={loadingMatching || document.status !== "completed"}
                      leftIcon={loadingMatching ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                    >
                      {matchingData && matchingData.service === service.id ? "View Results" : "Check Match"}
                    </Button>
                  </div>
                  
                  {matchingData && matchingData.service === service.id && (
                    <div className="mt-4 p-4 bg-bg-elevated rounded-xl border border-border/50">
                      <div className="flex items-center justify-between mb-3">
                        <StatusBadge 
                          status={matchingData.overall_status === "complete" ? "eligible" : matchingData.overall_status === "needs_review" ? "needs_information" : "ineligible"} 
                          size="md"
                        />
                        <span className="text-sm text-text-muted">
                          Coverage: {Math.round(matchingData.checklist_coverage * 100)}%
                        </span>
                      </div>
                      
                      {matchingData.available_documents.length > 0 && (
                        <div className="mb-3">
                          <p className="font-medium text-sm text-text-primary mb-2">Available Documents</p>
                          <div className="flex flex-wrap gap-2">
                            {matchingData.available_documents.map((doc, i) => (
                              <Badge key={i} variant="success" size="sm" className="text-xs">
                                {doc.name}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {matchingData.missing_documents.length > 0 && (
                        <div className="mb-3">
                          <p className="font-medium text-sm text-text-primary mb-2">Missing Documents</p>
                          <div className="flex flex-wrap gap-2">
                            {matchingData.missing_documents.map((doc, i) => (
                              <Badge key={i} variant="error" size="sm" className="text-xs">
                                {doc.name}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {matchingData.incomplete_extraction.length > 0 && (
                        <div className="mb-3">
                          <p className="font-medium text-sm text-warning mb-2">Incomplete Extraction</p>
                          <div className="flex flex-wrap gap-2">
                            {matchingData.incomplete_extraction.map((doc, i) => (
                              <Badge key={i} variant="warning" size="sm" className="text-xs">
                                {doc.name} - {doc.reason || "Incomplete"}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {document.error && (
            <div className="p-4 rounded-xl bg-error/5 border border-error/20">
              <p className="text-error text-sm">{document.error}</p>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
            <Button variant="ghost" onClick={onClose}>Close</Button>
            <Button variant="outline" leftIcon={<Download className="w-4 h-4" />} disabled>Download</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: React.ComponentType<{ className?: string }>; title: string; description: string }) {
  return (
    <Card variant="outlined" padding="lg" hover>
      <CardContent className="flex flex-col h-full">
        <div className="w-12 h-12 rounded-xl bg-accent-purple/10 flex items-center justify-center mb-4">
          <Icon className="w-6 h-6 text-accent-purple" aria-hidden="true" />
        </div>
        <h4 className="font-heading font-bold text-text-primary mb-2">{title}</h4>
        <p className="text-text-muted text-sm flex-1">{description}</p>
      </CardContent>
    </Card>
  );
}

function DocumentsPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  
  const [documents, setDocuments] = useState<DocumentUI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentUI | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [matchingData, setMatchingData] = useState<DocumentMatchingResponse | null>(null);
  const [loadingMatching, setLoadingMatching] = useState(false);
  const [backendUnavailable, setBackendUnavailable] = useState(false);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await api.listDocuments();
      // Convert API response to UI format
      const docs: DocumentUI[] = response.items.map(doc => ({
        id: doc.id,
        name: doc.original_filename,
        size: doc.file_size,
        type: doc.content_type,
        status: doc.processing_status as DocumentUI["status"],
        progress: doc.processing_status === "completed" ? 100 : doc.processing_status === "processing" ? 50 : 0,
        uploadedAt: new Date(doc.created_at),
        businessProfileId: doc.business_profile_id || undefined,
        documentType: doc.document_type || undefined,
        extractedData: doc.extracted_data,
        extractedFields: doc.extracted_data?.normalized_fields ? 
          Object.fromEntries(
            (doc.extracted_data.normalized_fields as Array<{ field_type: string; value: string; verified: boolean; provenance: string }>).map((f) => [
              f.field_type, 
              { value: f.value, verified: f.verified, source: f.provenance }
            ])
          ) : undefined,
      }));
      setDocuments(docs);
      setBackendUnavailable(false);
    } catch (err: unknown) {
      const apiError = err as { detail?: string; status?: number };
      if (apiError.status === 404 || apiError.detail?.includes("not found") || apiError.detail?.includes("router")) {
        setBackendUnavailable(true);
        setDocuments([]);
      } else {
        setError(apiError.detail || "Failed to load documents");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (files: File[]) => {
    for (const file of files) {
      if (!file.type.includes("pdf") && !file.type.includes("image")) {
        setError(`${file.name}: Only PDF and image files are supported`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError(`${file.name}: File size must be less than 10MB`);
        continue;
      }

      try {
        const response = await api.uploadDocument(file);
        // Add the new document to the list
        const newDoc: DocumentUI = {
          id: response.document_id,
          name: response.filename,
          size: file.size,
          type: file.type,
          status: response.status as DocumentUI["status"],
          progress: response.status === "completed" ? 100 : 0,
          uploadedAt: new Date(),
          error: response.status === "error" ? response.message : undefined,
        };
        setDocuments(prev => [newDoc, ...prev]);
      } catch (err: unknown) {
        if (err instanceof ApiError) {
          if (err.status === 404) {
            setBackendUnavailable(true);
            setError("Document upload API not available. Backend router not implemented.");
          } else {
            setError(err.detail || `Failed to upload ${file.name}`);
          }
        } else if (err instanceof Error) {
          setError(err.message || `Failed to upload ${file.name}`);
        } else {
          setError(`Failed to upload ${file.name}`);
        }
      }
    }
    // Refresh documents after upload
    loadDocuments();
  };

  const deleteDocument = async (docId: string) => {
    try {
      await api.deleteDocument(docId);
      setDocuments(prev => prev.filter(doc => doc.id !== docId));
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to delete document");
    }
  };

  const handleViewDocument = (doc: DocumentUI) => {
    setSelectedDocument(doc);
    setMatchingData(null);
    setShowDetail(true);
  };

  const handleRetryDocument = async () => {
    loadDocuments();
  };

  const handleLoadMatching = async (service: string) => {
    if (!selectedDocument) return;
    setLoadingMatching(true);
    try {
      const data = await api.getDocumentMatching(selectedDocument.id, service);
      setMatchingData(data);
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load matching results");
    } finally {
      setLoadingMatching(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  useEffect(() => {
    if (user && !authLoading) {
      // Data fetching intentionally updates loading state when auth resolves.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadDocuments();
    }
  }, [user, authLoading]);

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading documents..." />
        </div>
      </DashboardLayout>
    );
  }

  if (!user) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <EmptyState
            icon={Building2}
            title="Authentication Required"
            description="Please sign in to access this page."
            alignment="center"
          />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-heading font-bold text-3xl md:text-4xl tracking-tight text-text-primary">
              Document Centre
            </h1>
            <p className="text-text-muted mt-1">
              Upload business documents for AI-powered extraction and compliance checking.
            </p>
          </div>
        </div>

        {backendUnavailable && (
          <Card variant="outlined" padding="lg" className="border-warning/30 bg-warning/5">
            <CardContent className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-warning/10 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-5 h-5 text-warning" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-heading font-bold text-text-primary mb-2">Backend Document API Not Available</h4>
                <p className="text-text-muted text-sm leading-relaxed">
                  The document upload and processing endpoints are not yet implemented in the backend. 
                  The frontend is ready and will work once the backend router is added.
                  <br /><br />
                  <strong>Required backend endpoints:</strong>
                  <ul className="list-disc list-inside mt-2 text-sm space-y-1">
                    <li><code>POST /api/v1/documents/upload</code> - Upload PDF/document</li>
                    <li><code>GET /api/v1/documents</code> - List user documents</li>
                    <li><code>GET /api/v1/documents/&#123;id&#125;</code> - Get document details</li>
                    <li><code>GET /api/v1/documents/&#123;id&#125;/matching</code> - Compliance matching</li>
                    <li><code>DELETE /api/v1/documents/&#123;id&#125;</code> - Delete document</li>
                  </ul>
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {error && (
          <div className="bg-error/5 border border-error/20 rounded-[16px] p-4 flex items-center justify-between">
            <p className="text-error text-sm">{error}</p>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}

        {!backendUnavailable && (
          <FileUploader
            accept=".pdf,.jpg,.jpeg,.png"
            maxSize={10 * 1024 * 1024}
            maxFiles={5}
            multiple={true}
            onUpload={handleUpload}
            onError={setError}
            disabled={backendUnavailable}
          />
        )}

        <SectionHeading
          title="Your Documents"
          eyebrow="UPLOADED FILES"
          subtitle={documents.length > 0 ? `${documents.length} document${documents.length !== 1 ? "s" : ""} uploaded` : "No documents uploaded yet"}
        />

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : documents.length > 0 ? (
          <div className="space-y-4">
            {documents.map((doc) => (
              <DocumentFileCard 
                key={doc.id} 
                document={doc} 
                formatFileSize={formatFileSize}
                getStatusConfig={getStatusConfig}
                onView={() => handleViewDocument(doc)}
                onDelete={() => deleteDocument(doc.id)}
                onRetry={doc.status === "error" ? () => handleRetryDocument() : undefined}
              />
            ))}
          </div>
        ) : !backendUnavailable ? (
          <EmptyState
            icon={FileText}
            title="No documents yet"
            description="Upload your first document to get started with AI-powered extraction and compliance checking."
            alignment="center"
          />
        ) : null}

        {!backendUnavailable && (
          <>
            <SectionHeading
              title="What You Get"
              eyebrow="FEATURES"
              subtitle="AI-powered document intelligence for your business compliance"
            />
      
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <FeatureCard 
                icon={Search} 
                title="Text Extraction" 
                description="Automatic OCR and text extraction from PDFs and scanned documents." 
              />
              <FeatureCard 
                icon={Sparkles} 
                title="Field Detection" 
                description="AI identifies key fields like GSTIN, PAN, dates, amounts, and addresses." 
              />
              <FeatureCard 
                icon={Shield} 
                title="Compliance Check" 
                description="Match documents against scheme requirements and identify missing info." 
              />
            </div>
          </>
        )}
      </div>

      {showDetail && selectedDocument && (
        <DocumentDetailModal 
          document={selectedDocument} 
          onClose={() => { setShowDetail(false); setSelectedDocument(null); setMatchingData(null); }}
          formatFileSize={formatFileSize}
          getStatusConfig={getStatusConfig}
          matchingData={matchingData}
          onLoadMatching={handleLoadMatching}
          loadingMatching={loadingMatching}
        />
      )}
    </DashboardLayout>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading documents..." />
        </div>
      </DashboardLayout>
    }>
      <DocumentsPageContent />
    </Suspense>
  );
}
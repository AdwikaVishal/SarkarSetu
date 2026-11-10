"use client";

import { useState, useCallback, useRef, DragEvent, ChangeEvent } from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { Card } from "./Card";
import { Upload, X, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

export interface FileUploaderProps {
  accept?: string;
  maxSize?: number; // in bytes
  maxFiles?: number;
  multiple?: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onError?: (error: string) => void;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode;
  showFileList?: boolean;
}

interface QueuedFile {
  file: File;
  id: string;
  status: "pending" | "uploading" | "completed" | "error";
  progress: number;
  error?: string | null;
}

export function FileUploader({
  accept = ".pdf,.jpg,.jpeg,.png",
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  multiple = true,
  onUpload,
  onError,
  disabled = false,
  className,
  children,
  showFileList = true,
}: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Utility function for formatting file sizes
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

const validateFile = (file: File, accept: string): string | null => {
    if (!file.type.match(accept.replace(/\*/g, ".*").replace(/\./g, "\\.").replace(/,/g, "|"))) {
      // Simple check for common types
      const allowedTypes = accept.split(",").map(t => t.trim().replace(".", ""));
      const isAllowed = allowedTypes.some(t => 
        file.type.includes(t) || file.name.toLowerCase().endsWith(t)
      );
      if (!isAllowed) {
        return `File type not allowed. Accepted: ${accept}`;
      }
    }
    if (file.size > maxSize) {
      return `File size exceeds ${formatFileSize(maxSize)} limit`;
    }
    return null;
  };

  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    if (queuedFiles.length + fileArray.length > maxFiles) {
      onError?.(`Maximum ${maxFiles} files allowed`);
      return;
    }

    const newFiles: QueuedFile[] = fileArray.map((file) => {
      const validationError = validateFile(file, accept);
      return {
        file,
        id: Math.random().toString(36).substring(2, 9),
        status: validationError ? "error" : "pending",
        progress: 0,
        error: validationError,
      };
    });

    setQueuedFiles((prev) => [...prev, ...newFiles]);
  }, [queuedFiles.length, maxFiles, maxSize, accept, onError, validateFile]);

  const removeFile = useCallback((id: string) => {
    setQueuedFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const clearCompleted = useCallback(() => {
    setQueuedFiles((prev) => prev.filter((f) => f.status !== "completed"));
  }, []);

  const handleUpload = useCallback(async () => {
    const pendingFiles = queuedFiles.filter((f) => f.status === "pending");
    if (pendingFiles.length === 0) return;

    setIsUploading(true);
    
    try {
      // Update status to uploading
      setQueuedFiles((prev) => 
        prev.map((f) => f.status === "pending" ? { ...f, status: "uploading" as const, progress: 0 } : f)
      );

      // Upload all files
      await onUpload(pendingFiles.map((f) => f.file));

      // Mark all as completed
      setQueuedFiles((prev) => 
        prev.map((f) => f.status === "uploading" ? { ...f, status: "completed" as const, progress: 100 } : f)
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed";
      setQueuedFiles((prev) => 
        prev.map((f) => f.status === "uploading" ? { ...f, status: "error" as const, error: errorMessage } : f)
      );
      onError?.(errorMessage);
    } finally {
      setIsUploading(false);
    }
  }, [queuedFiles, onUpload, onError]);

  const handleDrag = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files.length > 0 && !disabled) {
      addFiles(e.dataTransfer.files);
    }
  }, [addFiles, disabled]);

  const handleFileSelect = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0 && !disabled) {
      addFiles(e.target.files);
    }
    // Reset input value to allow selecting same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [addFiles, disabled]);

  const pendingCount = queuedFiles.filter((f) => f.status === "pending").length;
  const completedCount = queuedFiles.filter((f) => f.status === "completed").length;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop Zone */}
      <Card
        variant="outlined"
        padding="xl"
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          dragActive ? "border-accent-lime bg-accent-lime/5" : "border-border hover:border-accent-lime/50",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          id="file-upload"
          multiple={multiple}
          accept={accept}
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        
        <div className="text-center">
          <div className={cn(
            "w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 transition-colors",
            dragActive ? "bg-accent-lime/20 text-accent-lime" : "bg-accent-purple/10 text-accent-purple"
          )}>
            <Upload className="w-8 h-8" aria-hidden="true" />
          </div>
          <h3 className="font-heading font-bold text-xl text-text-primary mb-2">
            {dragActive ? "Drop files here" : "Drag & drop files here"}
          </h3>
          <p className="text-text-muted mb-4">or click to browse</p>
          <Button 
            variant="outline" 
            size="lg" 
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isUploading}
          >
            Select Files
          </Button>
          <p className="text-text-muted text-xs mt-4">
            Accepts: {accept} • Max {formatFileSize(maxSize)} per file • Max {maxFiles} files
          </p>
        </div>
      </Card>

      {/* File List */}
      {showFileList && queuedFiles.length > 0 && (
        <Card variant="outlined" padding="md">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-heading font-semibold text-text-primary">
                Files ({queuedFiles.length})
              </h4>
              <div className="flex items-center gap-2">
                {completedCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={clearCompleted}>
                    <X className="w-3.5 h-3.5" /> Clear completed
                  </Button>
                )}
                {pendingCount > 0 && (
                  <Button 
                    variant="lime" 
                    size="sm" 
                    leftIcon={<Upload className="w-3.5 h-3.5" />}
                    onClick={handleUpload}
                    disabled={isUploading}
                    isLoading={isUploading}
                  >
                    Upload {pendingCount}
                  </Button>
                )}
              </div>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {queuedFiles.map((queuedFile) => (
                <FileQueueItem
                  key={queuedFile.id}
                  queuedFile={queuedFile}
                  formatFileSize={formatFileSize}
                  onRemove={removeFile}
                />
              ))}
            </div>
          </div>
        </Card>
      )}

      {children}
    </div>
  );
}

interface FileQueueItemProps {
  queuedFile: QueuedFile;
  formatFileSize: (bytes: number) => string;
  onRemove: (id: string) => void;
}

function FileQueueItem({ queuedFile, formatFileSize, onRemove }: FileQueueItemProps) {
  const { file, status, progress, error, id } = queuedFile;

  const getStatusConfig = () => {
    switch (status) {
      case "pending":
        return { icon: FileText, color: "text-text-muted", bg: "bg-text-muted/10", label: "Pending" };
      case "uploading":
        return { icon: Loader2, color: "text-accent-lime", bg: "bg-accent-lime/10 animate-pulse", label: "Uploading..." };
      case "completed":
        return { icon: CheckCircle, color: "text-success", bg: "bg-success/10", label: "Completed" };
      case "error":
        return { icon: AlertCircle, color: "text-error", bg: "bg-error/10", label: "Error" };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-bg-card border border-border">
      <div className="w-10 h-10 rounded-lg bg-bg-elevated flex items-center justify-center flex-shrink-0">
        <FileText className="w-5 h-5 text-text-muted" aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-text-primary truncate">{file.name}</p>
        <p className="text-text-muted text-xs">{formatFileSize(file.size)}</p>
        {status === "uploading" && (
          <div className="mt-1 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
              <div 
                className="h-full bg-accent-lime rounded-full transition-all duration-300" 
                style={{ width: `${progress}%` }} 
                aria-hidden="true"
              />
            </div>
            <span className="text-xs font-bold text-accent-lime">{progress}%</span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className={cn("flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full", config.bg, config.color)}>
          <Icon className="w-3 h-3" aria-hidden="true" />
          <span>{config.label}</span>
        </span>
        {status === "error" && error && (
          <span className="text-xs text-error truncate max-w-[150px]">{error}</span>
        )}
        <button
          onClick={() => onRemove(id)}
          className="p-1.5 rounded-lg text-text-muted hover:text-error hover:bg-error/10 transition-colors"
          aria-label="Remove file"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
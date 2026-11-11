"use client";

import { useState, useCallback, useRef } from "react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { Upload, FileText, AlertCircle, CheckCircle, X } from "lucide-react";

interface FileUploaderProps {
  accept?: string;
  maxSize?: number;
  maxFiles?: number;
  multiple?: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onError?: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

export function FileUploader({
  accept = ".pdf,.jpg,.jpeg,.png",
  maxSize = 10 * 1024 * 1024,
  maxFiles = 5,
  multiple = true,
  onUpload,
  onError,
  disabled = false,
  className,
}: FileUploaderProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (!file.type.includes("pdf") && !file.type.includes("image")) {
      return "Only PDF and image files are supported";
    }
    if (file.size > maxSize) {
      return `File size must be less than ${maxSize / (1024 * 1024)}MB`;
    }
    return null;
  };

  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    if (fileArray.length > maxFiles) {
      onError?.(`Maximum ${maxFiles} files allowed`);
      return;
    }

    const validFiles: File[] = [];
    for (const file of fileArray) {
      const error = validateFile(file);
      if (error) {
        onError?.(`${file.name}: ${error}`);
      } else {
        validFiles.push(file);
      }
    }

    setSelectedFiles(prev => [...prev, ...validFiles].slice(0, maxFiles));
  }, [maxFiles, maxSize, onError]);

  const clickFileInput = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled, fileInputRef]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleClick = () => {
    clickFileInput();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || uploading) return;
    
    setUploading(true);
    try {
      await onUpload(selectedFiles);
      setSelectedFiles([]);
    } catch (err) {
      onError?.(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
        className={cn(
          "relative rounded-[16px] border-2 border-dashed transition-all duration-200 cursor-pointer",
          isDragActive 
            ? "border-accent-lime bg-accent-lime/5" 
            : "border-border hover:border-accent-lime/50 hover:bg-bg-card",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        role="button"
        tabIndex={0}
        aria-label="File upload area"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={disabled}
          aria-hidden="true"
        />
        
        <div className="p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-accent-lime/10 flex items-center justify-center mx-auto mb-4">
            <Upload className="w-8 h-8 text-accent-lime" aria-hidden="true" />
          </div>
          <p className="font-medium text-text-primary mb-1">
            {isDragActive ? "Drop files here" : "Drag & drop files here, or click to browse"}
          </p>
          <p className="text-text-muted text-sm">
            {multiple ? `Up to ${maxFiles} files` : "Single file"} • PDF, JPG, PNG • Max {maxSize / (1024 * 1024)}MB each
          </p>
        </div>
      </div>

      {selectedFiles.length > 0 && (
        <div className="space-y-3">
          <p className="font-medium text-text-primary">Selected Files ({selectedFiles.length}/{maxFiles})</p>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center gap-3 p-3 rounded-xl bg-bg-card border border-border">
                <div className="w-10 h-10 rounded-xl bg-bg-elevated flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-text-muted" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-text-primary truncate">{file.name}</p>
                  <p className="text-text-muted text-xs">{formatFileSize(file.size)}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  disabled={uploading}
                  aria-label={`Remove ${file.name}`}
                >
                  <X className="w-4 h-4 text-error" aria-hidden="true" />
                </Button>
              </div>
            ))}
          </div>
          
          <div className="flex justify-end">
            <Button
              variant="lime"
              size="lg"
              leftIcon={<Upload className="w-4 h-4" />}
              onClick={handleUpload}
              disabled={uploading || selectedFiles.length === 0}
              isLoading={uploading}
            >
              {uploading ? "Uploading..." : `Upload ${selectedFiles.length} File${selectedFiles.length !== 1 ? "s" : ""}`}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
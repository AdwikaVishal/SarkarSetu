"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { StatusBadge, toStatusType } from "@/components/ui/StatusBadge";
import { ArrowRight, Search, Target, Users, Building2 } from "lucide-react";

const ENTITY_TYPES = [
  "scheme",
  "business_type",
  "location",
  "registration",
  "document",
  "deadline",
  "authority",
];

function IntentPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  const [text, setText] = useState("");
  const [classification, setClassification] = useState<{
    intent: string;
    confidence: number;
    entities: Record<string, unknown>;
  } | null>(null);
  const [analysis, setAnalysis] = useState<{
    intent: string;
    confidence: number;
    entities: Record<string, unknown>;
    sentiment: "positive" | "negative" | "neutral";
    urgency: "low" | "medium" | "high";
  } | null>(null);
  const [extractedEntities, setExtractedEntities] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClassify = async () => {
    if (!text.trim()) {
      setError("Please enter text to analyze");
      return;
    }

    setError(null);
    setClassification(null);

    try {
      const result = await api.classifyIntent({ text });

      setClassification({
        intent: result.intent,
        confidence: result.confidence,
        entities: result.entities ?? {},
      });
    } catch (err: unknown) {
      const detail =
        typeof err === "object" && err !== null && "detail" in err
          ? String((err as { detail?: unknown }).detail)
          : "Failed to classify intent";
      setError(detail);
    }
  };

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError("Please enter text to analyze");
      return;
    }

    setError(null);
    setAnalysis(null);

    try {
      const result = await api.analyzeIntent({ text });

      setAnalysis({
        intent: result.intent,
        confidence: result.confidence,
        entities: result.entities ?? {},
        sentiment: result.sentiment,
        urgency: result.urgency,
      });
    } catch (err: unknown) {
      const detail =
        typeof err === "object" && err !== null && "detail" in err
          ? String((err as { detail?: unknown }).detail)
          : "Failed to analyze intent";
      setError(detail);
    }
  };

  const handleExtract = async () => {
    if (!text.trim()) {
      setError("Please enter text to analyze");
      return;
    }

    setError(null);
    setExtractedEntities(null);

    try {
      const result = await api.extractEntities({ text });
      setExtractedEntities(result.entities ?? {});
    } catch (err: unknown) {
      const detail =
        typeof err === "object" && err !== null && "detail" in err
          ? String((err as { detail?: unknown }).detail)
          : "Failed to extract entities";
      setError(detail);
    }
  };

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-bg-primary flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-lime border-t-transparent" />
        </div>
      </DashboardLayout>
    );
  }

  if (!isAuthenticated) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-bg-primary flex items-center justify-center">
          <div className="text-center p-8">
            <h2 className="font-heading font-bold text-xl text-text-primary mb-2">
              SarkarSetu AI
            </h2>
            <p className="text-text-muted">
              Application is ready. Redirecting to dashboard...
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const confidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return { label: "High", variant: "success" as const };
    if (confidence >= 0.5) return { label: "Medium", variant: "lime" as const };
    return { label: "Low", variant: "warning" as const };
  };

  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Intent Classification</CardTitle>
          </CardHeader>
          <CardContent>
            {classification ? (
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Primary intent
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="lime" size="sm">
                    {classification.intent}
                  </Badge>
                  <span className="text-sm text-text-primary">
                    {classification.confidence.toFixed(2)}
                  </span>
                  <Badge variant={confidenceBadge(classification.confidence).variant} size="sm">
                    {confidenceBadge(classification.confidence).label}
                  </Badge>
                </div>
                <div className="mt-3 text-xs font-medium uppercase tracking-wide text-text-muted">
                  Entities
                </div>
                <div className="mt-1 flex flex-wrap gap-2">
                  {Object.entries(classification.entities).map(([key, value]) => (
                    <Badge key={key} variant="outline" size="sm">
                      {key}: {String(value)}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Full Intent Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            {analysis ? (
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-text-muted">
                  Primary intent
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="purple" size="sm">
                    {analysis.intent}
                  </Badge>
                  <span className="text-sm text-text-primary">
                    {analysis.confidence.toFixed(2)}
                  </span>
                  <Badge variant={confidenceBadge(analysis.confidence).variant} size="sm">
                    {confidenceBadge(analysis.confidence).label}
                  </Badge>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-text-muted">Sentiment</span>
                    <span className="ml-2 text-text-primary capitalize">{analysis.sentiment}</span>
                  </div>
                  <div>
                    <span className="text-text-muted">Urgency</span>
                    <span className="ml-2 text-text-primary capitalize">{analysis.urgency}</span>
                  </div>
                </div>
                <div className="mt-3 text-xs font-medium uppercase tracking-wide text-text-muted">
                  Entities
                </div>
                <div className="mt-1 flex flex-wrap gap-2">
                  {Object.entries(analysis.entities).map(([key, value]) => (
                    <Badge key={key} variant="outline" size="sm">
                      {key}: {String(value)}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Entity Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {ENTITY_TYPES.map((entityType) => (
                <Badge key={entityType} variant="outline" size="sm">
                  {entityType}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card variant="outlined" padding="md" lg:col-span-3>
          <CardHeader>
            <CardTitle size="md">Analyze Message</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Enter a message to analyze intent and extract entities..."
              className="w-full px-3 py-3 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent resize-none min-h-[120px]"
              aria-label="Message input"
              rows={3}
            />
            <div className="mt-4 flex gap-2">
              <Button variant="lime" size="sm" onClick={handleClassify} disabled={authLoading}>
                Classify intent
              </Button>
              <Button variant="purple" size="sm" onClick={handleAnalyze} disabled={authLoading}>
                Full analysis
              </Button>
              <Button variant="error" size="sm" onClick={handleExtract} disabled={authLoading}>
                Extract entities
              </Button>
              <Button variant="outline" size="sm" onClick={() => setText("")} className="px-3 py-1">
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default IntentPage;
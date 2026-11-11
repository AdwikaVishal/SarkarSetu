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
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CitationCard } from "@/components/ui/CitationCard";

function AIToolsPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // AI Health state
  const [aiHealth, setAiHealth] = useState<{ enabled: boolean; available: boolean; model: string } | null>(null);
  const [aiHealthLoading, setAiHealthLoading] = useState(true);

  // Tool 1: Free-text generation
  const [tool1Prompt, setTool1Prompt] = useState("");
  const [tool1Output, setTool1Output] = useState<string | null>(null);
  const [tool1Loading, setTool1Loading] = useState(false);
  const [tool1Model, setTool1Model] = useState<string | null>(null);

  // Tool 2: JSON generation
  const [tool2Prompt, setTool2Prompt] = useState("");
  const [tool2Output, setTool2Output] = useState<any | null>(null);
  const [tool2Loading, setTool2Loading] = useState(false);
  const [tool2Valid, setTool2Valid] = useState<boolean | null>(null);
  const [tool2SchemaError, setTool2SchemaError] = useState<string | null>(null);

  // Tool 3: Structured generation
  const [tool3Prompt, setTool3Prompt] = useState("");
  const [tool3Schema, setTool3Schema] = useState<string>(
    "{\"type\":\"object\",\"properties\":{\"name\":\"string\",\"value\":\"string\"}}"
  );
  const [tool3Output, setTool3Output] = useState<any | null>(null);
  const [tool3Valid, setTool3Valid] = useState<boolean | null>(null);
  const [tool3SchemaError, setTool3SchemaError] = useState<string | null>(null);
  const [tool3Loading, setTool3Loading] = useState(false);

  // Tool: AI Health
  const loadAiHealth = async () => {
    try {
      const result = await api.aiHealth();
      setAiHealth({
        enabled: result.enabled,
        available: result.available,
        model: result.model,
      });
      setAiHealthLoading(false);
    } catch (err: any) {
      setAiHealth({ enabled: false, available: false, model: "Unknown" });
      setAiHealthLoading(false);
    }
  };

  // Load AI health
  useEffect(() => {
    loadAiHealth();
  }, []);
  useEffect(() => {
    if (!authLoading) loadAiHealth();
  }, [authLoading]);

  // Tool 1: Generate
  const handleTool1Generate = async () => {
    if (!tool1Prompt.trim()) return;

    setTool1Loading(true);
    setTool1Output(null);

    try {
      const result = await api.aiGenerate({
        prompt: tool1Prompt,
        temperature: 0.7,
        max_output_tokens: 500,
      });

      setTool1Output(result.text);
      setTool1Model(result.model);
    } catch (err: any) {
      setTool1Output(`Error: ${err.detail || "AI generation failed"}`);
    } finally {
      setTool1Loading(false);
    }
  };

  // Tool 2: JSON
  const handleTool2Generate = async () => {
    if (!tool2Prompt.trim()) return;

    setTool2Loading(true);
    setTool2Output(null);
    setTool2Valid(null);

    try {
      const result = await api.aiJson({
        prompt: tool2Prompt,
        temperature: 0.7,
        max_output_tokens: 500,
      });

      // Use result.data directly (already parsed by backend)
      setTool2Output(result.data as any);
      setTool2Valid(true);
    } catch (err: any) {
      setTool2Output(null);
      setTool2Valid(false);
    } finally {
      setTool2Loading(false);
    }
  };

  // Tool 3: Structured
  const handleTool3Generate = async () => {
    if (!tool3Prompt.trim()) return;

    setTool3SchemaError(null);
    setTool3Loading(true);
    setTool3Output(null);
    setTool3Valid(null);

    try {
      const result = await api.aiStructured({
        prompt: tool3Prompt,
        response_schema: tool3Schema,
        temperature: 0.7,
        max_output_tokens: 500,
      });

      // Use result.data directly (already parsed by backend)
      setTool3Output(result.data as any);
      setTool3Valid(true);
    } catch (err: any) {
      setTool3Output(null);
      setTool3Valid(false);
    } finally {
      setTool3Loading(false);
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

  // Tool 1 UI
  const tool1Content = (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">Free-text Generation</CardTitle>
      </CardHeader>
      <CardContent>
        <textarea
          value={tool1Prompt}
          onChange={(e) => setTool1Prompt(e.target.value)}
          placeholder="Enter your prompt..."
          className="w-full px-3 py-3 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent resize-none min-h-[120px]"
          aria-label="Prompt input"
          rows={3}
        />
        <div className="mt-4 flex gap-2">
          <Button
            variant="lime"
            size="sm"
            onClick={handleTool1Generate}
            disabled={tool1Loading}
          >
            {tool1Loading ? "Generating..." : "Generate"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setTool1Prompt("")}
            className="px-3 py-1"
          >
            Clear
          </Button>
        </div>
        {tool1Output && (
          <div className="mt-4 p-3 rounded-xl bg-bg-primary/30 border border-accent-lime/30">
            <h4 className="font-medium text-text-primary mb-2">Output:</h4>
            <p className="text-text-primary whitespace-pre-wrap">{tool1Output}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );

  // Tool 2 UI
  const tool2Content = (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">JSON Generation</CardTitle>
      </CardHeader>
      <CardContent>
        <textarea
          value={tool2Prompt}
          onChange={(e) => setTool2Prompt(e.target.value)}
          placeholder="Enter your prompt for JSON output..."
          className="w-full px-3 py-3 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent resize-none min-h-[120px]"
          aria-label="Prompt input"
          rows={3}
        />
        <div className="mt-4 flex gap-2">
          <Button
            variant="lime"
            size="sm"
            onClick={handleTool2Generate}
            disabled={tool2Loading}
          >
            {tool2Loading ? "Generating..." : "Generate JSON"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setTool2Prompt("")}
            className="px-3 py-1"
          >
            Clear
          </Button>
        </div>
        {tool2Output !== null && (
          <div className="mt-4">
            <div className="mt-2">
              <StatusBadge
                status={tool2Valid ? "success" : "error"}
                size="sm"
              />
            </div>
            {tool2Valid === true && tool2Output && (
              <pre className="mt-3 rounded-xl bg-bg-primary/50 p-4 overflow-x-auto">
                <code className="text-sm text-text-primary">
                  {JSON.stringify(tool2Output, null, 2)}
                </code>
              </pre>
            )}
            {tool2Valid === false && (
              <pre className="mt-3 rounded-xl bg-bg-primary/50 p-4 overflow-x-auto text-error">
                <code className="text-sm text-error">
                  {typeof tool2Output === "string" ? tool2Output : "Not valid JSON"}
                </code>
              </pre>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );

  // Tool 3 UI
  const tool3Content = (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">Structured Output</CardTitle>
      </CardHeader>
      <CardContent>
        <textarea
          value={tool3Prompt}
          onChange={(e) => setTool3Prompt(e.target.value)}
          placeholder="Enter your prompt for structured output..."
          className="w-full px-3 py-3 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent resize-none min-h-[120px]"
          aria-label="Prompt input"
          rows={3}
        />
        <div className="grid grid-cols-2 gap-3 mt-3">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Response schema
            </label>
            <textarea
              value={tool3Schema}
              onChange={(e) => setTool3Schema(e.target.value)}
              placeholder='e.g., {"type":"object","properties":{"name":"string"}}'
              className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent resize-none"
              aria-label="Schema input"
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Validation
            </label>
            <StatusBadge
              status={tool3Valid !== null ? (tool3Valid ? "success" : "error") : "pending"}
              size="sm"
            />
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <Button
            variant="lime"
            size="sm"
            onClick={handleTool3Generate}
            disabled={tool3Valid !== null && !tool3Valid}
          >
            {tool3Loading || (tool3Valid !== null && !tool3Valid) ? "Generating..." : "Generate Structured"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setTool3Prompt("")}
            className="px-3 py-1"
          >
            Clear
          </Button>
        </div>
        {tool3Output !== null && (
          <div className="mt-4">
            <div className="mt-2">
              <StatusBadge
                status={tool3Valid !== null ? (tool3Valid ? "success" : "error") : "pending"}
                size="sm"
              />
            </div>
            {tool3Valid === true && tool3Output && (
              <pre className="mt-3 rounded-xl bg-bg-primary/50 p-4 overflow-x-auto">
                <code className="text-sm text-text-primary">
                  {JSON.stringify(tool3Output, null, 2)}
                </code>
              </pre>
            )}
            {tool3Valid === false && tool3SchemaError && (
              <pre className="mt-3 rounded-xl bg-bg-primary/50 p-4 overflow-x-auto text-error">
                <code className="text-sm text-error">
                  {tool3SchemaError}
                </code>
              </pre>
            )}
            {!tool3Valid && !tool3SchemaError && (
              <p className="mt-2 text-sm text-text-muted">Schema validation pending...</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );

  // AI Health status
  const aiHealthContent = aiHealth ? (
    <Card variant="outlined" padding="md">
      <CardHeader>
        <CardTitle size="md">AI Service Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
<StatusBadge
              status={aiHealth.enabled && aiHealth.available ? "success" : "error"}
              size="sm"
/>
          <div>
            <p className="text-sm text-text-muted">Model:</p>
            <p className="font-medium text-text-primary">{aiHealth.model}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  ) : (
    <SkeletonCard />
  );

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

  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Tool 1: Free-text */}
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Free-text Generation</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Already defined above */}
          </CardContent>
        </Card>

        {/* Tool 2: JSON */}
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">JSON Generation</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Already defined above */}
          </CardContent>
        </Card>

        {/* Tool 3: Structured */}
        <Card variant="outlined" padding="md">
          <CardHeader>
            <CardTitle size="md">Structured Output</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Already defined above */}
          </CardContent>
        </Card>

        {/* AI Health */}
        <Card variant="outlined" padding="md" lg:col-span-3>
          <CardHeader>
            <CardTitle size="md">AI Service Health</CardTitle>
          </CardHeader>
          <CardContent>
            {aiHealthContent}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default AIToolsPage;
"use client";

import { useEffect, useState, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, type ChatMessageRequest, type ChatMessageResponse, type ConversationResponse, type RetrievalSourceResponse } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState, EmptyState } from "@/components/ui/EmptyState";
import { CitationList } from "@/components/ui/CitationCard";
import { cn } from "@/lib/utils";
import { 
  Send, 
  MessageSquare, 
  Sparkles, 
  Loader2, 
  X, 
  Plus, 
  Trash2,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Building2,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  intent?: string;
  clarificationRequired?: boolean;
  clarificationQuestion?: string;
  responseType?: string;
  citations?: RetrievalSourceResponse[];
  provider?: string | null;
  fallbackUsed?: boolean;
  confidence?: number | null;
}

function AssistantPageContent() {
  const { user, isLoading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const initialConversationId = searchParams.get("conversation");
  
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(initialConversationId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<{ message: string; retryable: boolean } | null>(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [showCitations, setShowCitations] = useState(false);
  const [selectedMessageCitations, setSelectedMessageCitations] = useState<RetrievalSourceResponse[] | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [lastUserMessage, setLastUserMessage] = useState<string | null>(null);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
      if (convs.length > 0 && !currentConversationId) {
        setCurrentConversationId(convs[0].id);
        loadConversation(convs[0].id);
      }
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load conversations");
    }
  };

  const loadConversation = async (conversationId: string) => {
    setCurrentConversationId(conversationId);
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getMessages(conversationId, 50, 0);
      const chatMessages: ChatMessage[] = response.items.map(msg => {
        const metadata = msg.message_metadata as Record<string, unknown> | undefined;
        return {
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          intent: msg.intent || undefined,
          clarificationRequired: metadata?.clarification_required as boolean | undefined,
          clarificationQuestion: metadata?.clarification_question as string | undefined,
          responseType: metadata?.response_type as string | undefined,
          provider: metadata?.provider as string | undefined,
          fallbackUsed: metadata?.fallback_used as boolean | undefined,
          confidence: metadata?.confidence_score as number | undefined,
          metadata,
        };
      });
      setMessages(chatMessages);
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load conversation");
    } finally {
      setIsLoading(false);
    }
  };

  const createNewConversation = async () => {
    setIsLoading(true);
    try {
      const conv = await api.createConversation({ 
        title: "New Conversation",
        business_profile_id: undefined,
      });
      setConversations(prev => [conv, ...prev]);
      setCurrentConversationId(conv.id);
      setMessages([]);
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to create conversation");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = input.trim();
    setInput("");
    setLastUserMessage(userMessage);
    setIsLoading(true);
    setError(null);

    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const request: ChatMessageRequest = {
        message: userMessage,
        conversation_id: currentConversationId || undefined,
        business_profile_id: undefined,
      };

      const response: ChatMessageResponse = await api.sendMessage(request);
      
      if (!currentConversationId && response.conversation_id) {
        setCurrentConversationId(response.conversation_id);
        loadConversations();
      }

      const assistantMessage: ChatMessage = {
        id: response.assistant_message_id,
        role: "assistant",
        content: response.assistant_response,
        timestamp: new Date(),
        intent: response.intent?.primary_intent,
        clarificationRequired: response.clarification_required,
        clarificationQuestion: response.clarification_question || undefined,
        responseType: response.response_type,
        provider: response.provider || undefined,
        fallbackUsed: response.fallback_used || undefined,
        confidence: response.confidence || undefined,
      };
      setMessages(prev => [...prev, assistantMessage]);
      } catch (err: unknown) {
      // Keep the user's message - don't remove it on failure.
      const apiError = err as { status?: number; detail?: string };
      let errorMessage: string;
      let isRetryable = false;

      if (apiError.status === 503 || apiError.status === 429) {
        errorMessage =
          "The AI service is temporarily busy. Your message has been saved in this chat. Please try again shortly.";
        isRetryable = true;
      } else if (apiError.status === 401) {
        errorMessage = "Your session has expired. Please log in again.";
      } else if (apiError.status === 403) {
        errorMessage = "You don't have permission to perform this action.";
      } else if (apiError.status === 404) {
        errorMessage = "The requested resource was not found.";
      } else if (apiError.status === 422) {
        errorMessage = "Invalid request. Please check your input and try again.";
      } else if (apiError.status && apiError.status >= 500) {
        errorMessage =
          "The server encountered an error. Please try again later.";
      } else if (err instanceof NetworkError) {
        errorMessage =
          "Unable to connect to the server. Please check your connection and try again.";
        isRetryable = true;
      } else {
        errorMessage =
          apiError.detail || "Failed to send message. Please try again.";
      }

      setError({ message: errorMessage, retryable: isRetryable });
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, currentConversationId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (user && !authLoading) {
      // Data fetching intentionally updates loading state when auth resolves.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadConversations();
      if (initialConversationId) {
        loadConversation(initialConversationId);
      }
    }
    // Loaders are recreated each render; only re-run when auth/conversation changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading, initialConversationId]);

  const removeConversation = async (conversationId: string) => {
    try {
      await api.deleteConversation(conversationId);
      setConversations((prev) => prev.filter((conv) => conv.id !== conversationId));
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null);
        setMessages([]);
      }
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to delete conversation");
    }
  };

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading assistant..." />
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

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100dvh-8rem)] min-h-[520px] flex-col">
        <div className="mb-4 flex flex-shrink-0 items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="rounded-lg p-2 text-text-primary hover:bg-bg-card lg:hidden"
              aria-label={showSidebar ? "Hide conversations" : "Show conversations"}
            >
              {showSidebar ? <ChevronLeft className="w-6 h-6" /> : <ChevronRight className="w-6 h-6" />}
            </button>
            <div className="min-w-0">
              <h1 className="font-heading font-bold text-2xl md:text-3xl text-text-primary">AI Assistant</h1>
              <p className="truncate text-text-muted text-sm">
                {currentConversation?.title || "Start a new conversation"}
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={createNewConversation} aria-label="New chat">
            <span className="hidden sm:inline">New Chat</span>
          </Button>
        </div>

        <div className="relative flex min-h-0 flex-1 overflow-hidden rounded-xl border border-border bg-bg-elevated">
          <aside className={cn(
            "absolute inset-y-0 left-0 z-10 w-72 max-w-[85%] flex-col border-r border-border bg-bg-elevated lg:static lg:z-auto lg:flex lg:w-80 lg:max-w-none lg:flex-shrink-0",
            showSidebar ? "flex" : "hidden"
          )}>
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h2 className="font-heading font-semibold text-text-primary">Conversations</h2>
              <Button variant="ghost" size="sm" onClick={createNewConversation} aria-label="New conversation">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            
            <div className="flex-1 overflow-y-auto">
              <ul className="p-2 space-y-1" role="list">
                {conversations.map((conv) => (
                  <li key={conv.id} className="relative">
                    <button
                      onClick={() => loadConversation(conv.id)}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-xl p-3 pr-11 text-left transition-colors",
                        conv.id === currentConversationId
                          ? "bg-accent-lime/10 text-text-primary border border-accent-lime/20"
                          : "text-text-muted hover:bg-bg-card hover:text-text-primary"
                      )}
                    >
                      <MessageSquare className={cn("w-5 h-5 flex-shrink-0", conv.id === currentConversationId && "text-accent-lime")} aria-hidden="true" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium">{conv.title || "Untitled Conversation"}</span>
                        <span className="block truncate text-xs text-text-muted">
                          {new Date(conv.updated_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </span>
                    </button>
                    <button
                      onClick={() => removeConversation(conv.id)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-text-muted transition-colors hover:bg-error/10 hover:text-error"
                      aria-label={`Delete conversation ${conv.title || ""}`}
                    >
                      <Trash2 className="w-4 h-4" aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </aside>

          <div className="flex min-h-0 min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 space-y-6 overflow-y-auto p-4" role="log" aria-live="polite" aria-label="Chat messages">
              {messages.length === 0 && !isLoading && (
                <WelcomeMessage 
                  onSuggestedClick={(q) => {
                    setInput(q);
                    sendMessage();
                  }}
                />
              )}
              
              {messages.map((message) => (
                <MessageBubble 
                  key={message.id} 
                  message={message} 
                  onViewCitations={message.citations ? () => {
                    setSelectedMessageCitations(message.citations!);
                    setShowCitations(true);
                  } : undefined}
                />
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 text-text-muted text-sm">
                    <Loader2 className="w-4 h-4 animate-spin text-accent-lime" aria-hidden="true" />
                    <span>AI is thinking...</span>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {error && (
              <div className="px-4 pb-4">
                <ErrorState
                  title="Error"
                  message={error.message}
                  onRetry={() => {
                    setError(null);
                    if (error.retryable && lastUserMessage) {
                      setInput(lastUserMessage);
                      sendMessage();
                    }
                  }}
                  retryLabel={error.retryable ? "Retry" : "Dismiss"}
                  alignment="center"
                />
              </div>
            )}

            <div className="flex-shrink-0 border-t border-border bg-bg-primary/50 p-4">
              <div className="max-w-3xl mx-auto">
                <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex items-end gap-3">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about schemes, compliance, registrations..."
                    className="flex-1 min-h-[48px] max-h-48 px-4 py-3 rounded-xl border border-border bg-bg-elevated text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent resize-none transition-colors"
                    disabled={isLoading}
                    rows={1}
                    aria-label="Message input"
                  />
                  <Button
                    type="submit"
                    variant="lime"
                    size="lg"
                    disabled={!input.trim() || isLoading}
                    aria-label="Send message"
                  >
                    <Send className="w-5 h-5" aria-hidden="true" />
                  </Button>
                </form>
                <p className="text-xs text-text-muted text-center mt-2">
                  Press Enter to send, Shift+Enter for new line
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showCitations && selectedMessageCitations && (
        <CitationModal
          citations={selectedMessageCitations}
          onClose={() => { setShowCitations(false); setSelectedMessageCitations(null); }}
        />
      )}
    </DashboardLayout>
  );
}

function WelcomeMessage({ onSuggestedClick }: { onSuggestedClick: (question: string) => void }) {
  const suggestedQuestions = [
    "What schemes apply to my manufacturing business in Karnataka?",
    "What documents do I need for GST registration?",
    "How do I register for Udyam?",
    "What is PMEGP and am I eligible?",
    "Explain MSME classification criteria",
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center px-4">
      <div className="w-16 h-16 rounded-full bg-accent-purple/10 flex items-center justify-center mb-6">
        <MessageSquare className="w-8 h-8 text-accent-purple" aria-hidden="true" />
      </div>
      <h2 className="font-heading font-bold text-2xl text-text-primary mb-2">How can I help you?</h2>
      <p className="text-text-muted mb-8 max-w-md">
        Ask me anything about government services, business registrations, schemes, or compliance requirements.
      </p>
      <div className="flex flex-wrap gap-2 justify-center w-full max-w-md">
        {suggestedQuestions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSuggestedClick(q)}
            className="w-full sm:w-auto text-left px-4 py-3 rounded-xl bg-bg-card border border-border text-text-primary text-sm hover:border-accent-lime/50 hover:bg-bg-elevated transition-all text-start"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message, onViewCitations }: { message: ChatMessage; onViewCitations?: () => void }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isUser ? "bg-accent-lime" : "bg-accent-purple"
      )}>
        {isUser ? (
          <Sparkles className="w-4 h-4 text-text-primary" aria-hidden="true" />
        ) : (
          <MessageSquare className="w-4 h-4 text-text-inverse" aria-hidden="true" />
        )}
      </div>
      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-3",
        isUser
          ? "bg-accent-lime/10 text-text-primary rounded-tr-sm"
          : "bg-accent-purple/10 text-text-primary rounded-tl-sm"
      )}>
        <div className="prose prose-sm max-w-none text-inherit">
          {message.content.split("\n").map((line, i) => (
            <p key={i} className="whitespace-pre-wrap">{line}</p>
          ))}
        </div>
        
        {(message.intent || message.clarificationRequired) && (
          <div className="mt-3 pt-3 border-t border-border/50 flex flex-wrap items-center gap-2 text-xs">
            {message.intent && (
              <Badge variant="outline" size="sm">
                Intent: {message.intent}
              </Badge>
            )}
            {message.clarificationRequired && (
              <Badge variant="lime" size="sm" dot>
                Clarification needed
              </Badge>
            )}
            {message.clarificationQuestion && (
              <p className="text-text-muted">{message.clarificationQuestion}</p>
            )}
            {message.fallbackUsed && (
              <Badge variant="outline" size="sm" className="text-text-muted">
                Local knowledge base
              </Badge>
            )}
          </div>
        )}
        
        <div className="mt-2 flex items-center gap-2 text-xs text-text-muted">
          <span>{message.timestamp.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
          {onViewCitations && (
            <button 
              onClick={onViewCitations}
              className="flex items-center gap-1 text-accent-purple hover:text-accent-purple-hover"
            >
              <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
              <span>View Sources</span>
            </button>
          )}
        </div>
        {message.fallbackUsed && (
          <p className="mt-2 text-xs text-text-muted italic">
            Using SarkarSetu&apos;s offline knowledge base. Some information may not
            reflect the latest government updates.
          </p>
        )}
      </div>
    </div>
  );
}

function CitationModal({ citations, onClose }: { citations: RetrievalSourceResponse[]; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div className="bg-bg-elevated rounded-[24px] max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="font-heading font-bold text-xl text-text-primary">Sources & Citations</h2>
          <button onClick={onClose} className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card transition-colors">
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
        <div className="p-4">
          <CitationList citations={citations} compact={false} showScores={true} title="Retrieved Sources" />
        </div>
      </div>
    </div>
  );
}

export default function AssistantPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading assistant..." />
        </div>
      </DashboardLayout>
    }>
      <AssistantPageContent />
    </Suspense>
  );
}
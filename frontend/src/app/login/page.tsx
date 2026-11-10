"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Lock, User, Mail, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, register, isLoading: authLoading } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirmPassword, setRegConfirmPassword] = useState("");

  const MIN_PASSWORD_LENGTH = 12;

  const clearFieldError = useCallback((field: string) => {
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  const handleSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      setError(null);
      setFieldErrors({});
      setIsSubmitting(true);

      try {
        if (isRegister) {
          const nextFieldErrors: Record<string, string> = {};

          if (!email.trim()) nextFieldErrors.email = "Email is required.";
          if (!fullName.trim()) nextFieldErrors.fullName = "Full name is required.";
          if (!regPassword) {
            nextFieldErrors.password = "Password is required.";
          } else if (regPassword.length < MIN_PASSWORD_LENGTH) {
            nextFieldErrors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
          }
          if (!regConfirmPassword) {
            nextFieldErrors.confirmPassword = "Please confirm your password.";
          } else if (regConfirmPassword !== regPassword) {
            nextFieldErrors.confirmPassword = "Passwords do not match.";
          }

          if (Object.keys(nextFieldErrors).length > 0) {
            setFieldErrors(nextFieldErrors);
            setError("Please fix the errors above before continuing.");
            return;
          }

          await register(email, regPassword, fullName || undefined);
        } else {
          if (!email.trim()) {
            setFieldErrors({ email: "Email is required." });
            setError("Please fix the errors above before continuing.");
            return;
          }
          if (!password) {
            setFieldErrors({ password: "Password is required." });
            setError("Please fix the errors above before continuing.");
            return;
          }
          await login(email, password);
        }
        router.replace("/dashboard");
      } catch (err: unknown) {
        const apiError = err as { status?: number; detail?: string; validationErrors?: Array<{ loc?: Array<string | number>; msg?: string; type?: string }> };
        if (apiError.validationErrors && apiError.validationErrors.length > 0) {
          const nextFieldErrors: Record<string, string> = {};
          apiError.validationErrors.forEach((ve) => {
            const fieldName = (ve.loc?.slice(1) || []).map((p) => String(p)).join(".");
            nextFieldErrors[fieldName] = ve.msg || "Invalid value.";
          });
          setFieldErrors(nextFieldErrors);
          setError(
            "Validation failed: " +
              apiError.validationErrors.map((ve) => ve.msg).join("; ")
          );
        } else {
          setError(
            err instanceof Error
              ? err.message
              : "Authentication failed. Please try again."
          );
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      login,
      register,
      router,
      isRegister,
      email,
      password,
      fullName,
      regPassword,
      regConfirmPassword,
    ]
  );

  if (authLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-bg-primary">
        <div className="animate-pulse rounded-full h-8 w-8 bg-bg-dark" />
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-bg-primary px-4">
      <Card
        variant="elevated"
        className="w-full max-w-md shadow-lg"
      >
        <CardHeader className="text-center">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-deep-rose mx-auto mb-4">
            <Lock className="h-6 w-6 text-white" aria-hidden="true" />
          </div>
          <CardTitle className="text-2xl">{isRegister ? "Create Account" : "Sign in"}</CardTitle>
          <p className="mt-2 text-sm text-text-muted">
            {isRegister
              ? "Join SarkarSetu AI to manage your business compliance."
              : "Welcome back to SarkarSetu AI. Sign in to access your workspace."}
          </p>
        </CardHeader>
        <CardContent className="space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-primary px-3 py-2 focus-within:border-deep-rose focus-within:ring-1 focus-within:ring-deep-rose">
                <Mail className="h-4 w-4 text-text-muted" aria-hidden="true" />
                <input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (fieldErrors.email) clearFieldError("email");
                  }}
                  required
                  className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted"
                  autoComplete={isRegister ? "email" : "email"}
                  aria-invalid={!!fieldErrors.email}
                  aria-describedby={fieldErrors.email ? "email-error" : undefined}
                />
              </div>
              {fieldErrors.email && (
                <p id="email-error" className="text-xs text-error">{fieldErrors.email}</p>
              )}

              {isRegister ? (
                <>
                  <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-primary px-3 py-2 focus-within:border-deep-rose focus-within:ring-1 focus-within:ring-deep-rose">
                    <User className="h-4 w-4 text-text-muted" aria-hidden="true" />
                    <input
                      type="text"
                      placeholder="Full name"
                      value={fullName}
                      onChange={(e) => {
                        setFullName(e.target.value);
                        if (fieldErrors.fullName) clearFieldError("fullName");
                      }}
                      required
                      className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted"
                      autoComplete="name"
                      aria-invalid={!!fieldErrors.fullName}
                      aria-describedby={fieldErrors.fullName ? "full-name-error" : undefined}
                    />
                  </div>
                  {fieldErrors.fullName && (
                    <p id="full-name-error" className="text-xs text-error">{fieldErrors.fullName}</p>
                  )}

                  <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-primary px-3 py-2 focus-within:border-deep-rose focus-within:ring-1 focus-within:ring-deep-rose">
                    <Lock className="h-4 w-4 text-text-muted" aria-hidden="true" />
                    <input
                      type="password"
                      placeholder="Password"
                      value={regPassword}
                      onChange={(e) => {
                        setRegPassword(e.target.value);
                        if (fieldErrors.password) clearFieldError("password");
                      }}
                      required
                      minLength={MIN_PASSWORD_LENGTH}
                      className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted"
                      autoComplete="new-password"
                      aria-invalid={!!fieldErrors.password}
                      aria-describedby={fieldErrors.password ? "reg-password-error" : undefined}
                    />
                  </div>
                  {fieldErrors.password && (
                    <p id="reg-password-error" className="text-xs text-error">{fieldErrors.password}</p>
                  )}

                  <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-primary px-3 py-2 focus-within:border-deep-rose focus-within:ring-1 focus-within:ring-deep-rose">
                    <Lock className="h-4 w-4 text-text-muted" aria-hidden="true" />
                    <input
                      type="password"
                      placeholder="Confirm password"
                      value={regConfirmPassword}
                      onChange={(e) => {
                        setRegConfirmPassword(e.target.value);
                        if (fieldErrors.confirmPassword) clearFieldError("confirmPassword");
                      }}
                      required
                      className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted"
                      autoComplete="new-password"
                      aria-invalid={!!fieldErrors.confirmPassword}
                      aria-describedby={fieldErrors.confirmPassword ? "confirm-password-error" : undefined}
                    />
                  </div>
                  {fieldErrors.confirmPassword && (
                    <p id="confirm-password-error" className="text-xs text-error">{fieldErrors.confirmPassword}</p>
                  )}
                </>
              ) : (
                <>
                  <div className="flex items-center gap-2 rounded-lg border border-border bg-bg-primary px-3 py-2 focus-within:border-deep-rose focus-within:ring-1 focus-within:ring-deep-rose">
                    <Lock className="h-4 w-4 text-text-muted" aria-hidden="true" />
                    <input
                      type="password"
                      placeholder="Password"
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (fieldErrors.password) clearFieldError("password");
                      }}
                      required
                      className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted"
                      autoComplete="current-password"
                      aria-invalid={!!fieldErrors.password}
                      aria-describedby={fieldErrors.password ? "login-password-error" : undefined}
                    />
                  </div>
                  {fieldErrors.password && (
                    <p id="login-password-error" className="text-xs text-error">{fieldErrors.password}</p>
                  )}
                </>
              )}
            </div>

            {error && (
              <div className="rounded-lg border border-error/50 bg-error/10 p-3 text-sm text-error">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="lime"
              className="w-full"
              isLoading={isSubmitting}
            >
              {isRegister ? "Create account" : "Sign in"}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border/60" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-bg-elevated px-2 text-text-muted">
                Or continue with
              </span>
            </div>
          </div>

          <Button
            variant="outline"
            className="w-full"
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? "Already have an account? Sign in" : "Don't have an account? Register"}
          </Button>
        </CardContent>
        <CardContent className="pt-6 pb-4 text-center border-t border-border/50">
          <p className="text-xs text-text-muted">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

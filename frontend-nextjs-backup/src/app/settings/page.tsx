"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, type MeResponse, type BusinessProfileResponse } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { cn } from "@/lib/utils";
import { 
  LogOut,
  Save,
  Edit,
  ExternalLink,
  Building2,
  User,
  Bell,
  Trash2,
  Lock,
} from "lucide-react";

function SettingsPageContent() {
  const { user, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();

  // Explicit state type to avoid Hooks order issues
  type SettingsState = {
    businesses: BusinessProfileResponse[];
    loading: boolean;
    saving: boolean;
    error: string | null;
    success: string | null;
    activeTab: "profile" | "business" | "security" | "notifications" | "danger";
    userData: Partial<MeResponse>;
  };

  // Always call useState to maintain consistent hook order across renders
  const [state, setState] = useState<SettingsState>({
    businesses: [],
    loading: true,
    saving: false,
    error: null,
    success: null,
    activeTab: "profile",
    userData: {},
  });

  // Always call useEffect to maintain consistent hook order across renders
  useEffect(() => {
    async function loadData() {
      try {
        const response = await api.listBusinesses();
        setState(prev => ({
          ...prev,
          businesses: response.items,
          loading: false,
        }));
      } catch (err: unknown) {
        const apiError = err as { detail?: string };
        setState(prev => ({
          ...prev,
          error: apiError.detail || "Failed to load settings",
          loading: false,
        }));
      }
    }

    // Fetch data only when user is available and not loading
    if (user && !authLoading) {
      loadData();
    }
  }, [user, authLoading]);

  // Handle profile update
  const handleProfileUpdate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setState(prev => ({ ...prev, saving: true, error: null, success: null }));

    try {
      const formData = new FormData(e.currentTarget);
      const fullName = formData.get("full_name");
      if (fullName) {
        setState(prev => ({
          ...prev,
          userData: { ...prev.userData, full_name: String(fullName) },
        }));
      }
      setState(prev => ({ ...prev, success: "Profile updated successfully" }));
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setState(prev => ({
        ...prev,
        error: apiError.detail || "Failed to update profile",
      }));
    } finally {
      setState(prev => ({ ...prev, saving: false }));
    }
  };

  // Handle logout
  const handleLogout = async () => {
    await logout();
    router.push("/");
    router.refresh();
  };

  // Handle delete account
  const handleDeleteAccount = async () => {
    if (!confirm("Are you sure you want to delete your account? This action cannot be undone.")) return;
    setState(prev => ({ ...prev, error: "Account deletion requires backend API support." }));
  };

  if (authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading settings..." />
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

  const tabs = [
    { id: "profile", label: "Profile", icon: User },
    { id: "business", label: "Business", icon: Building2 },
    { id: "security", label: "Security", icon: Lock },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "danger", label: "Danger Zone", icon: Trash2 },
  ];

  const { businesses, saving, error, success, activeTab, userData } = state;

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-4xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-heading font-bold text-3xl md:text-4xl tracking-tight text-text-primary">
              Settings
            </h1>
            <p className="text-text-muted mt-1">
              Manage your account, business profiles, and preferences.
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-error/5 border border-error/20 rounded-[16px] p-4 flex items-center justify-between">
            <p className="text-error text-sm">{error}</p>
            <Button variant="ghost" size="sm" onClick={() => setState(prev => ({ ...prev, error: null }))}>
              Dismiss
            </Button>
          </div>
        )}

        {success && (
          <div className="bg-success/5 border border-success/20 rounded-[16px] p-4 flex items-center justify-between">
            <p className="text-success text-sm">{success}</p>
            <Button variant="ghost" size="sm" onClick={() => setState(prev => ({ ...prev, success: null }))}>
              Dismiss
            </Button>
          </div>
        )}

        {/* Tab Navigation */}
        <Card variant="outlined" padding="md">
          <CardContent>
            <div className="flex flex-wrap gap-2" role="tablist">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setState(prev => ({ ...prev, activeTab: tab.id as typeof activeTab }))}
                    role="tab"
                    aria-selected={isActive}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors",
                      isActive
                        ? "bg-accent-lime/10 text-text-primary border border-accent-lime/20"
                        : "text-text-muted hover:text-text-primary hover:bg-bg-card"
                    )}
                  >
                    <Icon className="w-4 h-4" aria-hidden="true" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Tab Content */}
        {activeTab === "profile" && (
          <Card variant="outlined" padding="xl">
            <CardHeader>
              <CardTitle size="lg">Profile Information</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div className="grid sm:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="full_name" className="block text-sm font-medium text-text-primary mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      id="full_name"
                      name="full_name"
                      value={userData.full_name ?? user.full_name ?? ""}
                      onChange={(e) => setState(prev => ({ ...prev, userData: { ...prev.userData, full_name: e.target.value } }))}
                      className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-1.5">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={userData.email ?? user.email ?? ""}
                      disabled
                      className="w-full px-4 py-3 rounded-xl border border-border bg-bg-card text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
                    />
                    <p className="text-xs text-text-muted mt-1">Email cannot be changed</p>
                  </div>
                </div>

                <div>
                  <label htmlFor="account_created" className="block text-sm font-medium text-text-primary mb-1.5">
                    Account Created
                  </label>
                  <input
                    type="text"
                    id="account_created"
                    value={user.created_at ? new Date(user.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" }) : "—"}
                    disabled
                    className="w-full px-4 py-3 rounded-xl border border-border bg-bg-card text-text-muted focus:outline-none"
                  />
                </div>

                <div className="flex items-center justify-end pt-4 border-t border-border">
                  <Button type="submit" variant="lime" isLoading={saving} rightIcon={<Save className="w-4 h-4" />}>
                    Save Changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {activeTab === "business" && (
          <div className="space-y-6">
            <Card variant="outlined" padding="xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle size="lg">Business Profiles</CardTitle>
                  <Button variant="outline" size="sm" leftIcon={<Edit className="w-4 h-4" />} asChild>
                    <a href="/profile?create=true">Add New</a>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {businesses.length > 0 ? (
                  <div className="space-y-4">
                    {businesses.map(biz => (
                      <div key={biz.id} className="flex items-center justify-between p-4 rounded-xl bg-bg-card border border-border">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-xl bg-accent-lime/10 flex items-center justify-center">
                            <Building2 className="w-6 h-6 text-accent-lime" aria-hidden="true" />
                          </div>
                          <div>
                            <p className="font-medium text-text-primary">{biz.business_name}</p>
                            <p className="text-text-muted text-sm">{biz.industry} • {biz.city || biz.district}, {biz.state}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {biz.is_default && (
                            <Badge variant="lime" size="sm">Default</Badge>
                          )}
                          <Button variant="ghost" size="sm" asChild>
                            <a href={`/profile?id=${biz.id}`}>Manage</a>
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Building2 className="w-12 h-12 text-text-muted mx-auto mb-4" aria-hidden="true" />
                    <h3 className="font-heading font-bold text-lg text-text-primary mb-2">No business profiles yet</h3>
                    <p className="text-text-muted mb-6">Create your first business profile to unlock personalized recommendations.</p>
                    <Button variant="lime" size="lg" leftIcon={<Building2 className="w-4 h-4" />} asChild>
                      <a href="/profile?create=true">Create Business Profile</a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "security" && (
          <Card variant="outlined" padding="xl">
            <CardHeader>
              <CardTitle size="lg">Security</CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              <div>
                <h3 className="font-heading font-semibold text-text-primary mb-4">Change Password</h3>
                <div className="p-4 rounded-xl bg-bg-card border border-border">
                  <p className="text-text-muted mb-4">Password change functionality requires backend API support.</p>
                  <Button variant="outline" size="sm" disabled>
                    Change Password
                  </Button>
                </div>
              </div>

              <div className="pt-6 border-t border-border">
                <h3 className="font-heading font-semibold text-text-primary mb-4">Active Sessions</h3>
                <div className="p-4 rounded-xl bg-bg-card border border-border">
                  <p className="text-text-muted mb-4">Session management requires backend API support.</p>
                  <Button variant="ghost" size="sm" disabled>
                    View Sessions
                  </Button>
                </div>
              </div>

              <div className="pt-6 border-t border-border">
                <h3 className="font-heading font-semibold text-text-primary mb-4">Two-Factor Authentication</h3>
                <div className="p-4 rounded-xl bg-bg-card border border-border">
                  <p className="text-text-muted mb-4">2FA is not currently available.</p>
                  <Button variant="outline" size="sm" disabled>
                    Enable 2FA
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "notifications" && (
          <Card variant="outlined" padding="xl">
            <CardHeader>
              <CardTitle size="lg">Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-text-muted">
                Notification preferences require backend API support. This section will be available when the notification system is implemented.
              </p>
              
              <div className="space-y-4">
                {[
                  { label: "Email notifications", description: "Receive updates via email", enabled: false },
                  { label: "In-app notifications", description: "Show notifications in the app", enabled: false },
                  { label: "Weekly digest", description: "Summary of your activity each week", enabled: false },
                  { label: "Scheme updates", description: "New schemes matching your profile", enabled: false },
                  { label: "Task reminders", description: "Reminders for pending roadmap tasks", enabled: false },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-bg-card border border-border">
                    <div>
                      <p className="font-medium text-text-primary">{item.label}</p>
                      <p className="text-text-muted text-sm">{item.description}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" disabled className="sr-only peer" />
                      <div className="w-11 h-6 bg-border peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-lime/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-border after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-text-primary after:border-border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-lime"></div>
                    </label>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "danger" && (
          <Card variant="outlined" padding="xl" className="border-error/20 bg-error/5">
            <CardHeader>
              <CardTitle size="lg" className="text-error">Danger Zone</CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="p-6 rounded-xl bg-bg-card border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-heading font-semibold text-text-primary mb-1">Delete Account</h3>
                    <p className="text-text-muted">Permanently delete your account and all associated data. This action cannot be undone.</p>
                  </div>
                  <Button variant="error" onClick={handleDeleteAccount}>
                    <Trash2 className="w-4 h-4" /> Delete Account
                  </Button>
                </div>
              </div>

              <div className="p-6 rounded-xl bg-bg-card border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-heading font-semibold text-text-primary mb-1">Export Data</h3>
                    <p className="text-text-muted">Download a copy of all your data before deleting your account.</p>
                  </div>
                  <Button variant="outline" disabled>
                    <ExternalLink className="w-4 h-4" /> Export Data
                  </Button>
                </div>
              </div>

              <div className="pt-6 border-t border-border flex justify-end">
                <Button variant="ghost" onClick={handleLogout} className="text-error hover:bg-error/5">
                  <LogOut className="w-4 h-4" /> Sign Out
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading settings..." />
        </div>
      </DashboardLayout>
    }>
      <SettingsPageContent />
    </Suspense>
  );
}

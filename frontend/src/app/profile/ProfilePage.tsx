"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle, CardFooter } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/LoadingState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { cn } from "@/lib/utils";
import { ArrowRight, Building2 } from "lucide-react";
import { useSearchParams } from "react-router-dom";

interface BusinessProfileFormValues {
  business_name: string;
  business_type: string;
  industry: string;
  state: string;
  district: string;
  business_structure: string;
  business_stage: string;
  annual_turnover?: number;
  employee_count?: number;
  sales_channels?: string[];
  description?: string;
  city?: string;
  pincode?: string;
  udyam_number?: string;
  gstin?: string;
  website?: string;
  woman_owned?: boolean;
  social_category?: string;
  products_services?: string[];
  operating_mode?: string;
  date_of_establishment?: string;
}

const BUSINESS_STRUCTURES = [
  "Proprietorship",
  "Partnership",
  "LLP",
  "PrivateLimited",
  "PublicLimited",
  "OPC",
  "Cooperative",
  "Trust",
  "Society",
  "Other",
];

const BUSINESS_STAGES = ["Idea", "Startup", "Growth", "Mature", "Scaling"];

const OPERATING_MODES = ["online", "offline", "both"];

const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi",
  "Lakshadweep",
  "Puducherry",
];

const CATEGORIES = [
  "Manufacturing",
  "Services",
  "Trading",
  "Technology",
  "Agriculture",
  "Handicrafts",
  "Other",
];

function ProfilePage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get("mode") || "list";
  const editId = searchParams.get("edit");

  // State
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState<BusinessProfileFormValues>({
    business_name: "",
    business_type: "",
    industry: "",
    state: "",
    district: "",
    business_structure: "Proprietorship",
    business_stage: "Idea",
    annual_turnover: undefined,
    employee_count: undefined,
    sales_channels: [],
    description: "",
    city: "",
    pincode: "",
    udyam_number: "",
    gstin: "",
    website: "",
    woman_owned: false,
    social_category: "",
    products_services: [],
    operating_mode: "online",
    date_of_establishment: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load businesses
  useEffect(() => {
    if (!isAuthenticated || authLoading) return;

    const load = async () => {
      try {
        const result = await api.listBusinesses();
        setBusinesses(result.items ?? []);
        setError(null);
      } catch (err: any) {
        setError(err.detail || "Failed to load business profiles");
      }
    };

    load();
  }, [isAuthenticated, authLoading]);

  // Initialize form from existing business if editing
  useEffect(() => {
    if (editId) {
      const business = businesses.find((b: any) => b.id === editId);
      if (business) {
        setForm({
          business_name: business.business_name,
          business_type: business.business_type,
          industry: business.industry,
          state: business.state,
          district: business.district,
          business_structure: business.business_structure,
          business_stage: business.business_stage,
          annual_turnover: business.annual_turnover,
          employee_count: business.employee_count,
          sales_channels: business.sales_channels || [],
          description: business.description,
          city: business.city,
          pincode: business.pincode,
          udyam_number: business.udyam_number,
          gstin: business.gstin,
          website: business.website,
          woman_owned: business.woman_owned,
          social_category: business.social_category,
          products_services: business.products_services || [],
          operating_mode: business.operating_mode || "online",
          date_of_establishment: business.date_of_establishment || "",
        });
      }
      setEditing(editId);
    } else {
      setEditing(null);
      // Reset form
      setForm({
        business_name: "",
        business_type: "",
        industry: "",
        state: "",
        district: "",
        business_structure: "Proprietorship",
        business_stage: "Idea",
        annual_turnover: undefined,
        employee_count: undefined,
        sales_channels: [],
        description: "",
        city: "",
        pincode: "",
        udyam_number: "",
        gstin: "",
        website: "",
        woman_owned: false,
        social_category: "",
        products_services: [],
        operating_mode: "online",
        date_of_establishment: "",
      });
    }
  }, [editId, businesses]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      if (editing) {
        // Update existing profile
        await api.updateBusiness(editing, {
          business_name: form.business_name,
          business_type: form.business_type,
          industry: form.industry,
          state: form.state,
          district: form.district,
          annual_turnover: form.annual_turnover,
          employee_count: form.employee_count,
          sales_channels: form.sales_channels,
          business_structure: form.business_structure,
          business_stage: form.business_stage,
          description: form.description,
          city: form.city,
          pincode: form.pincode,
          udyam_number: form.udyam_number,
          gstin: form.gstin,
          website: form.website,
          woman_owned: form.woman_owned,
          social_category: form.social_category,
          products_services: form.products_services,
          operating_mode: form.operating_mode,
          date_of_establishment: form.date_of_establishment,
        } as any);

        setSuccess("Business profile updated successfully");
        setEditing(null);
      } else {
        // Create new profile
        await api.createBusiness({
          business_name: form.business_name,
          business_type: form.business_type,
          industry: form.industry,
          state: form.state,
          district: form.district,
          annual_turnover: form.annual_turnover,
          employee_count: form.employee_count,
          sales_channels: form.sales_channels,
          business_structure: form.business_structure,
          business_stage: form.business_stage,
          description: form.description,
          city: form.city,
          pincode: form.pincode,
          udyam_number: form.udyam_number,
          gstin: form.gstin,
          website: form.website,
          woman_owned: form.woman_owned,
          social_category: form.social_category,
          products_services: form.products_services,
          operating_mode: form.operating_mode,
          date_of_establishment: form.date_of_establishment,
        } as any);

        setSuccess("Business profile created successfully");
      }

      // Reload businesses
      const result = await api.listBusinesses();
      setBusinesses(result.items ?? []);
      setForm({
        business_name: "",
        business_type: "",
        industry: "",
        state: "",
        district: "",
        business_structure: "Proprietorship",
        business_stage: "Idea",
        annual_turnover: undefined,
        employee_count: undefined,
        sales_channels: [],
        description: "",
        city: "",
        pincode: "",
        udyam_number: "",
        gstin: "",
        website: "",
        woman_owned: false,
        social_category: "",
        products_services: [],
        operating_mode: "online",
        date_of_establishment: "",
      });
    } catch (err: any) {
      setError(err.detail || "Failed to save business profile");
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to archive this business profile?")) return;

    try {
      await api.archiveBusiness(id);
      setBusinesses(businesses.filter((b: any) => b.id !== id));
      setSuccess("Business profile archived successfully");
    } catch (err: any) {
      setError(err.detail || "Failed to archive business profile");
    }
  };

  const handleRestore = async (id: string) => {
    try {
      await api.restoreBusiness(id);
      const result = await api.listBusinesses();
      setBusinesses(result.items ?? []);
      setSuccess("Business profile restored successfully");
    } catch (err: any) {
      setError(err.detail || "Failed to restore business profile");
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await api.setDefaultBusiness(id);
      const result = await api.listBusinesses();
      setBusinesses(result.items ?? []);
      setSuccess("Default profile set successfully");
    } catch (err: any) {
      setError(err.detail || "Failed to set default profile");
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

  // Mode: List
  if (mode === "list") {
    const defaultBusiness =
      businesses.find((b: any) => b.is_default) || businesses[0] || null;

    return (
      <DashboardLayout>
        <div className="space-y-6">
          {/* Create new profile button */}
          <Button
            variant="lime"
            size="md"
            className="mt-2 w-full justify-center"
            onClick={() => {
              const newUrl = `/profile?mode=create`;
              window.history.pushState({}, "", newUrl);
              setTimeout(() => window.dispatchEvent(new Event("popstate")), 0);
            }}
          >
            Create Business Profile
          </Button>

          {/* Business list */}
          {businesses.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {businesses.map((business: any) => (
                <Card
                  key={business.id}
                  variant="outlined"
                  padding="md"
                  className="h-full"
                >
                  <CardHeader>
                    <CardTitle size="sm">
                      {business.business_name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <dl className="grid grid-cols-1 gap-x-3 gap-y-2 text-sm">
                      <div>
                        <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                          Type
                        </dt>
                        <dd>
                          <StatusBadge
                            status={business.business_stage as any}
                          />
                          <span className="ml-2 text-text-muted">/{business.business_structure}</span>
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                          Location
                        </dt>
                        <dd>
                          {business.state}, {business.district}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">
                          Completion
                        </dt>
                        <dd>
                          <Badge variant="lime" size="sm">
                            {business.completion}%
                          </Badge>
                        </dd>
                      </div>
                    </dl>
                  </CardContent>
                  <CardFooter className="pt-2">
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const newUrl = `/profile?edit=${business.id}&mode=edit`;
                          window.history.pushState({}, "", newUrl);
                          setTimeout(() => window.dispatchEvent(new Event("popstate")), 0);
                        }}
                      >
                        View
                      </Button>
                      {business.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            // Already default, skip
                          }}
                        >
                          Default
                        </Button>
                      )}
                      {!business.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            handleSetDefault(business.id);
                          }}
                        >
                          Set as default
                        </Button>
                      )}
                      <Button
                        variant="error"
                        size="sm"
                        onClick={() => handleDelete(business.id)}
                      >
                        Archive
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Building2}
              title="No business profiles yet"
              description="Create your first business profile to get started with scheme recommendations and roadmaps."
              alignment="left"
              className="py-8"
            />
          )}
        </div>
      </DashboardLayout>
    );
  }

  // Mode: Create/Edit
  return (
    <DashboardLayout>
      <div className="pt-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="font-heading text-2xl font-bold text-text-primary mb-6">
            {editing ? "Edit Business Profile" : "Create Business Profile"}
          </h1>

          {error && (
            <ErrorState
              title="Error"
              message={error}
              onRetry={() => setError(null)}
              alignment="left"
            />
          )}

          {success && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4 mb-6 text-success">
              {success}
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="space-y-6 rounded-lg bg-bg-elevated p-6"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Business name <span className="text-text-muted">*</span>
                </label>
                <input
                  value={form.business_name}
                  onChange={(e) =>
                    setForm({ ...form, business_name: e.target.value })
                  }
                  required
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="e.g., TechStartup Solutions"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Business type <span className="text-text-muted">*</span>
                </label>
                <select
                  value={form.business_type}
                  onChange={(e) =>
                    setForm({ ...form, business_type: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select business type</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Services">Services</option>
                  <option value="Trading">Trading</option>
                  <option value="Technology">Technology</option>
                  <option value="Agriculture">Agriculture</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Industry <span className="text-text-muted">*</span>
                </label>
                <select
                  value={form.industry}
                  onChange={(e) =>
                    setForm({ ...form, industry: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select industry</option>
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  State <span className="text-text-muted">*</span>
                </label>
                <select
                  value={form.state}
                  onChange={(e) =>
                    setForm({ ...form, state: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select state</option>
                  {INDIAN_STATES.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  District <span className="text-text-muted">*</span>
                </label>
                <select
                  value={form.district}
                  onChange={(e) =>
                    setForm({ ...form, district: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select district</option>
                  {/* Districts would be filtered by state in a full implementation */}
                  <option value="Bangalore Urban">Bangalore Urban</option>
                  <option value="Mumbai City">Mumbai City</option>
                  <option value="Delhi North">Delhi North</option>
                  <option value="Chennai">Chennai</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Business structure <span className="text-text-muted">*</span>
                </label>
                <select
                  value={form.business_structure}
                  onChange={(e) =>
                    setForm({ ...form, business_structure: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select structure</option>
                  {BUSINESS_STRUCTURES.map((struct) => (
                    <option key={struct} value={struct}>
                      {struct}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Business stage <span className="text-text-muted">*</span>
                </label>
                <select
                  value={form.business_stage}
                  onChange={(e) =>
                    setForm({ ...form, business_stage: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select stage</option>
                  {BUSINESS_STAGES.map((stage) => (
                    <option key={stage} value={stage}>
                      {stage}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Annual turnover (INR) <span className="text-text-muted">optional</span>
                </label>
                <input
                  type="number"
                  value={form.annual_turnover ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      annual_turnover:
                        e.target.value === "" ? undefined : Number(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted placeholder-[₹0] focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="₹0"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Employee count <span className="text-text-muted">optional</span>
                </label>
                <input
                  type="number"
                  value={form.employee_count ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      employee_count:
                        e.target.value === "" ? undefined : Number(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Woman-owned <span className="text-text-muted">optional</span>
                </label>
                <div className="flex items-center gap-2">
                  <label
                    className={cn(
                      "flex items-center gap-2 rounded border border-border px-4 py-2",
                      form.woman_owned
                        ? "bg-accent-lime/20 text-accent-lime border-accent-lime"
                        : "text-text-muted hover:bg-bg-card hover:border-border"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={form.woman_owned}
                      onChange={(e) =>
                        setForm({ ...form, woman_owned: e.target.checked })
                      }
                      className="rounded border-none w-4 h-4 accent-accent-lime"
                    />
                    <span>Yes</span>
                  </label>
                  <label
                    className="ml-4 text-sm text-text-muted cursor-pointer hover:text-text-primary transition-colors"
                  >
                    No
                  </label>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  City
                </label>
                <input
                  value={form.city}
                  onChange={(e) =>
                    setForm({ ...form, city: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="e.g., Bangalore"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Pincode
                </label>
                <input
                  value={form.pincode}
                  onChange={(e) =>
                    setForm({ ...form, pincode: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="e.g., 560001"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Udyam number <span className="text-text-muted">optional</span>
                </label>
                <input
                  value={form.udyam_number}
                  onChange={(e) =>
                    setForm({ ...form, udyam_number: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="UDYAM-XXXX-XXXX"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  GSTIN <span className="text-text-muted">optional</span>
                </label>
                <input
                  value={form.gstin}
                  onChange={(e) =>
                    setForm({ ...form, gstin: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="e.g., 29ABCDE1234F1Z5"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Website <span className="text-text-muted">optional</span>
                </label>
                <input
                  value={form.website}
                  onChange={(e) =>
                    setForm({ ...form, website: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="https://example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Social category <span className="text-text-muted">optional</span>
                </label>
                <select
                  value={form.social_category}
                  onChange={(e) =>
                    setForm({ ...form, social_category: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="">Select category</option>
                  <option value="General">General</option>
                  <option value="SC">Scheduled Caste</option>
                  <option value="ST">Scheduled Tribe</option>
                  <option value="OBC">Other Backward Class</option>
                  <option value="Women">Women</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Products and services <span className="text-text-muted">optional</span>
                </label>
                <input
                  value={form.products_services?.join(", ") || ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      products_services:
                        e.target.value === ""
                          ? []
                          : e.target.value
                              .split(",")
                              .map((s: string) => s.trim())
                              .filter((s: string) => s.length > 0),
                    })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                  placeholder="e.g., Software development, Consulting services"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Operating mode <span className="text-text-muted">optional</span>
                </label>
                <select
                  value={form.operating_mode}
                  onChange={(e) =>
                    setForm({ ...form, operating_mode: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                >
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                  <option value="both">Both</option>
                </select>
              </div>
            </div>

            {editId && (
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Date of establishment <span className="text-text-muted">optional</span>
                </label>
                <input
                  type="date"
                  value={form.date_of_establishment || ""}
                  onChange={(e) =>
                    setForm({ ...form, date_of_establishment: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl border border-border bg-bg-primary/50 text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime/50 focus:border-transparent"
                />
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                variant="lime"
                disabled={authLoading}
                className="flex-1"
              >
                {editing ? "Update Profile" : "Create Profile"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="md"
                onClick={() => {
                  const newUrl = "/profile?mode=list";
                  window.history.pushState({}, "", newUrl);
                  setTimeout(() => window.dispatchEvent(new Event("popstate")), 0);
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default ProfilePage;
"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, type BusinessProfileResponse, type BusinessProfileCreate, type BusinessProfileUpdate, type BusinessStructure, type BusinessStage, type OperatingMode } from "@/lib/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { LoadingState } from "@/components/ui/LoadingState";
import { EmptyState, ErrorState } from "@/components/ui/EmptyState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { cn } from "@/lib/utils";
import { 
  Building2, 
  User, 
  MapPin, 
  DollarSign, 
  Users, 
  FileText, 
  Save, 
  Edit,
  X,
  Check,
  Plus,
  Trash2,
  Sparkles,
} from "lucide-react";

const businessStructures: BusinessStructure[] = [
  "Proprietorship", "Partnership", "LLP", "PrivateLimited", "PublicLimited", "OPC", "Cooperative", "Trust", "Society", "Other"
];

const businessStages: BusinessStage[] = ["Idea", "Startup", "Growth", "Mature", "Scaling"];
const operatingModes: OperatingMode[] = ["online", "offline", "both"];

const indianStates = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
  "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
  "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
];

function calculateCompletion(biz: BusinessProfileResponse) {
  const fields = [
    biz.business_name, biz.business_type, biz.industry, biz.state, biz.district,
    biz.business_structure, biz.business_stage, biz.city, biz.pincode,
    biz.annual_turnover, biz.employee_count, biz.gstin
  ];
  const filled = fields.filter(f => f !== null && f !== undefined && f !== "").length;
  return Math.round((filled / fields.length) * 100);
}

function InfoRow({ label, value, icon: Icon }: { label: string; value: string; icon: React.ComponentType<{ className?: string }> }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-bg-card border border-border">
      <Icon className="w-5 h-5 text-accent-lime" aria-hidden="true" />
      <div>
        <p className="text-xs text-text-muted uppercase tracking-wider">{label}</p>
        <p className="font-medium text-text-primary">{value}</p>
      </div>
    </div>
  );
}

function DetailSection({ title, icon: Icon, items }: { title: string; icon: React.ComponentType<{ className?: string }>; items: { label: string; value: string }[] }) {
  return (
    <Card variant="outlined" padding="lg">
      <CardContent>
        <h3 className="font-heading font-bold text-lg text-text-primary mb-4 flex items-center gap-2">
          <Icon className="w-5 h-5 text-accent-purple" aria-hidden="true" />
          {title}
        </h3>
        <div className="space-y-3">
          {items.map((item, i) => (
            <div key={i} className="flex justify-between py-2 border-b border-border/50 last:border-0">
              <span className="text-text-muted">{item.label}</span>
              <span className="font-medium text-text-primary text-right">{item.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function FormField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-text-primary mb-1.5 flex items-center gap-1">
        {label}
        {required && <span className="text-error" aria-hidden="true">*</span>}
      </label>
      {children}
    </div>
  );
}

function BusinessForm({ 
  formData, 
  handleChange, 
  handleSubmit, 
  saving, 
  isCreate,
  currentBusiness,
  onCancel 
}: { 
  formData: Partial<BusinessProfileCreate>;
  handleChange: (field: string, value: unknown) => void;
  handleSubmit: (e: React.FormEvent) => void;
  saving: boolean;
  isCreate: boolean;
  currentBusiness: BusinessProfileResponse | null;
  onCancel: () => void;
}) {
  return (
    <Card variant="outlined" padding="xl">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-heading font-bold text-xl text-text-primary">
            {isCreate ? "Create Business Profile" : "Edit Business Profile"}
          </h2>
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            <X className="w-4 h-4" /> Cancel
          </Button>
        </div>

        <SectionHeading title="Basic Information" subtitle="Required fields are marked with *" eyebrow="SECTION 1" />
        
        <div className="grid sm:grid-cols-2 gap-4">
          <FormField label="Business Name *" required>
            <input
              type="text"
              value={formData.business_name || ""}
              onChange={(e) => handleChange("business_name", e.target.value)}
              placeholder="Kumar Textiles Pvt Ltd"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
          
          <FormField label="Business Type *" required>
            <input
              type="text"
              value={formData.business_type || ""}
              onChange={(e) => handleChange("business_type", e.target.value)}
              placeholder="Manufacturing"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <FormField label="Industry *" required>
            <input
              type="text"
              value={formData.industry || ""}
              onChange={(e) => handleChange("industry", e.target.value)}
              placeholder="Apparel"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
          
          <FormField label="Business Structure *" required>
            <select
              value={formData.business_structure || "Proprietorship"}
              onChange={(e) => handleChange("business_structure", e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            >
              {businessStructures.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </FormField>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <FormField label="Business Stage *" required>
            <select
              value={formData.business_stage || "Startup"}
              onChange={(e) => handleChange("business_stage", e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            >
              {businessStages.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </FormField>
          
          <FormField label="Operating Mode *" required>
            <select
              value={formData.operating_mode || "both"}
              onChange={(e) => handleChange("operating_mode", e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            >
              {operatingModes.map(m => (
                <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
              ))}
            </select>
          </FormField>
        </div>

        <SectionHeading title="Location" subtitle="Business address details" eyebrow="SECTION 2" />
        
        <div className="grid sm:grid-cols-2 gap-4">
          <FormField label="State *" required>
            <select
              value={formData.state || ""}
              onChange={(e) => handleChange("state", e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            >
              <option value="">Select State</option>
              {indianStates.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </FormField>
          
          <FormField label="District *" required>
            <input
              type="text"
              value={formData.district || ""}
              onChange={(e) => handleChange("district", e.target.value)}
              placeholder="Bengaluru Urban"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
        </div>

        <div className="grid sm:grid-cols-3 gap-4">
          <FormField label="City">
            <input
              type="text"
              value={formData.city || ""}
              onChange={(e) => handleChange("city", e.target.value)}
              placeholder="Bengaluru"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
          
          <FormField label="PIN Code">
            <input
              type="text"
              value={formData.pincode || ""}
              onChange={(e) => handleChange("pincode", e.target.value)}
              placeholder="560001"
              maxLength={6}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
          
          <FormField label="GSTIN">
            <input
              type="text"
              value={formData.gstin || ""}
              onChange={(e) => handleChange("gstin", e.target.value)}
              placeholder="29ABCDE1234F1Z5"
              maxLength={15}
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
        </div>

        <SectionHeading title="Business Details" subtitle="Optional but helps with better recommendations" eyebrow="SECTION 3" />
        
        <div className="grid sm:grid-cols-2 gap-4">
          <FormField label="Annual Turnover (₹)">
            <input
              type="number"
              value={formData.annual_turnover || ""}
              onChange={(e) => handleChange("annual_turnover", e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="1200000"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
          
          <FormField label="Employee Count">
            <input
              type="number"
              value={formData.employee_count || ""}
              onChange={(e) => handleChange("employee_count", e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="5"
              className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
            />
          </FormField>
        </div>

        <FormField label="Description">
          <textarea
            value={formData.description || ""}
            onChange={(e) => handleChange("description", e.target.value)}
            placeholder="Brief description of your business..."
            rows={3}
            className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent resize-none"
          />
        </FormField>

        <FormField label="Products/Services (comma separated)">
          <input
            type="text"
            value={Array.isArray(formData.products_services) ? formData.products_services.join(", ") : ""}
            onChange={(e) => handleChange("products_services", e.target.value.split(",").map(s => s.trim()).filter(Boolean))}
            placeholder="shirts, trousers, uniforms"
            className="w-full px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
          />
        </FormField>

        <FormField label="Woman Owned">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.woman_owned || false}
              onChange={(e) => handleChange("woman_owned", e.target.checked)}
              className="w-4 h-4 rounded border-border text-accent-lime focus:ring-accent-lime"
            />
            <span className="text-text-primary">This business is woman-owned</span>
          </label>
        </FormField>

        <div className="flex items-center justify-end gap-4 pt-4 border-t border-border">
          <Button type="button" variant="outline" onClick={onCancel}>
            <X className="w-4 h-4" /> Cancel
          </Button>
          <Button type="submit" variant="lime" isLoading={saving} rightIcon={<Save className="w-4 h-4" />}>
            {isCreate ? "Create Profile" : "Save Changes"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function BusinessView({ 
  business, 
  businesses,
  onDelete 
}: { 
  business: BusinessProfileResponse; 
  businesses: BusinessProfileResponse[];
  onDelete: () => void;
}) {
  const completion = calculateCompletion(business);

  return (
    <div className="space-y-6">
      <Card variant="elevated" padding="xl">
        <CardContent className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-center gap-4 sm:gap-6">
            <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-xl bg-accent-lime/10 sm:h-20 sm:w-20">
              <Building2 className="h-8 w-8 text-accent-lime sm:h-10 sm:w-10" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-3">
                <h2 className="font-heading font-bold text-xl text-text-primary sm:text-2xl">{business.business_name}</h2>
                {business.is_default && (
                  <Badge variant="lime" size="sm">Default</Badge>
                )}
              </div>
              <p className="text-text-muted">
                {business.industry} • {business.city || business.district}, {business.state}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="text-left sm:text-center">
              <p className="font-heading font-bold text-3xl text-accent-lime">{completion}%</p>
              <p className="text-text-muted text-sm">Profile Complete</p>
            </div>
            {businesses.length > 1 && (
              <Button variant="ghost" onClick={onDelete} className="text-error hover:bg-error/5">
                <Trash2 className="w-4 h-4" /> Archive
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card variant="outlined" padding="lg">
        <CardContent>
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-text-primary">Profile Completion</span>
              <span className="font-bold text-accent-lime">{completion}%</span>
            </div>
            <div className="h-3 bg-bg-card rounded-full overflow-hidden">
              <div 
                className="h-full bg-accent-lime rounded-full transition-all duration-1000" 
                style={{ width: `${completion}%` }} 
                aria-hidden="true"
              />
            </div>
          </div>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <InfoRow label="Business Type" value={business.business_type} icon={Building2} />
            <InfoRow label="Structure" value={business.business_structure} icon={FileText} />
            <InfoRow label="Stage" value={business.business_stage} icon={Sparkles} />
            <InfoRow label="Operating Mode" value={business.operating_mode || "Not set"} icon={Users} />
          </div>
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <DetailSection 
          title="Location" 
          icon={MapPin}
          items={[
            { label: "State", value: business.state },
            { label: "District", value: business.district },
            { label: "City", value: business.city || "—" },
            { label: "PIN Code", value: business.pincode || "—" },
          ]}
        />
        
        <DetailSection 
          title="Registration" 
          icon={FileText}
          items={[
            { label: "GSTIN", value: business.gstin || "Not provided" },
            { label: "Woman Owned", value: business.woman_owned ? "Yes" : "No" },
          ]}
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <DetailSection 
          title="Business Metrics" 
          icon={DollarSign}
          items={[
            { label: "Annual Turnover", value: business.annual_turnover ? `₹${business.annual_turnover.toLocaleString()}` : "Not provided" },
            { label: "Employees", value: business.employee_count ? business.employee_count.toString() : "Not provided" },
          ]}
        />
        
        <DetailSection 
          title="Products & Services" 
          icon={Sparkles}
          items={[
            { label: "Offerings", value: business.products_services?.join(", ") || "Not provided" },
          ]}
        />
      </div>

      {business.description && (
        <Card variant="outlined" padding="lg">
          <CardContent>
            <h3 className="font-heading font-bold text-lg text-text-primary mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5 text-accent-purple" aria-hidden="true" />
              Description
            </h3>
            <p className="text-text-muted">{business.description}</p>
          </CardContent>
        </Card>
      )}

      <Card variant="outlined" padding="lg">
        <CardContent>
          <h3 className="font-heading font-bold text-lg text-text-primary mb-4">Profile Information</h3>
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-text-muted">Created</p>
              <p className="font-medium text-text-primary">{new Date(business.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" })}</p>
            </div>
            <div>
              <p className="text-text-muted">Last Updated</p>
              <p className="font-medium text-text-primary">{business.updated_at ? new Date(business.updated_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "Never"}</p>
            </div>
            <div>
              <p className="text-text-muted">Profile ID</p>
              <p className="font-mono text-text-primary">{business.id}</p>
            </div>
            <div>
              <p className="text-text-muted">Status</p>
              <p className="font-medium text-text-primary">{business.is_deleted ? "Archived" : "Active"}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ProfilePageContent() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const businessId = searchParams.get("id");
  const isCreate = searchParams.get("create") === "true";
  
  const [businesses, setBusinesses] = useState<BusinessProfileResponse[]>([]);
  const [currentBusiness, setCurrentBusiness] = useState<BusinessProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(isCreate);
  const [formData, setFormData] = useState<Partial<BusinessProfileCreate>>({
    business_name: "",
    business_type: "",
    industry: "",
    state: "",
    district: "",
    business_structure: "Proprietorship",
    business_stage: "Startup",
    operating_mode: "both",
  });

  const populateForm = (biz: BusinessProfileResponse) => {
    setFormData({
      business_name: biz.business_name,
      business_type: biz.business_type,
      industry: biz.industry,
      state: biz.state,
      district: biz.district,
      annual_turnover: biz.annual_turnover || undefined,
      employee_count: biz.employee_count || undefined,
      sales_channels: biz.sales_channels || undefined,
      business_structure: biz.business_structure,
      business_stage: biz.business_stage,
      description: biz.description || undefined,
      city: biz.city || undefined,
      pincode: biz.pincode || undefined,
      gstin: biz.gstin || undefined,
      woman_owned: biz.woman_owned || undefined,
      operating_mode: biz.operating_mode || undefined,
      products_services: biz.products_services || undefined,
    });
  };

  const loadBusinesses = async () => {
    setLoading(true);
    try {
      const response = await api.listBusinesses();
      setBusinesses(response.items);
      
      if (businessId) {
        const biz = response.items.find(b => b.id === businessId);
        if (biz) {
          setCurrentBusiness(biz);
          if (!isCreate) {
            populateForm(biz);
          }
        }
      } else if (response.items.length > 0 && !isCreate) {
        const defaultBiz = response.items.find(b => b.is_default) || response.items[0];
        setCurrentBusiness(defaultBiz);
        populateForm(defaultBiz);
      }
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to load business profiles");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: unknown) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateForm = () => {
    const required = ["business_name", "business_type", "industry", "state", "district", "business_structure", "business_stage"];
    for (const field of required) {
      if (!formData[field as keyof typeof formData]) {
        return `Please fill in ${field.replace("_", " ")}`;
      }
    }
    if (formData.pincode && !/^\d{6}$/.test(formData.pincode)) {
      return "PIN code must be exactly 6 digits";
    }
    if (formData.gstin && !/^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$/.test(formData.gstin)) {
      return "GSTIN format is invalid";
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    try {
      if (isCreate) {
        const newBusiness = await api.createBusiness(formData as BusinessProfileCreate);
        setBusinesses(prev => [newBusiness, ...prev]);
        setCurrentBusiness(newBusiness);
        setEditMode(false);
        router.push(`/profile?id=${newBusiness.id}`);
      } else if (currentBusiness) {
        const updated = await api.updateBusiness(currentBusiness.id, formData as BusinessProfileUpdate);
        setCurrentBusiness(updated);
        setBusinesses(prev => prev.map(b => b.id === updated.id ? updated : b));
        setEditMode(false);
      }
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to save business profile");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!currentBusiness || !confirm("Are you sure you want to archive this business profile?")) return;
    
    try {
      await api.archiveBusiness(currentBusiness.id);
      setBusinesses(prev => prev.filter(b => b.id !== currentBusiness!.id));
      setCurrentBusiness(null);
      router.push("/profile");
    } catch (err: unknown) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to archive business profile");
    }
  };

  const handleNewBusiness = () => {
    setCurrentBusiness(null);
    setFormData({
      business_name: "",
      business_type: "",
      industry: "",
      state: "",
      district: "",
      business_structure: "Proprietorship",
      business_stage: "Startup",
      operating_mode: "both",
    });
    setEditMode(true);
    router.push("/profile?create=true");
  };

  useEffect(() => {
    if (!authLoading && !user) {
      return;
      return;
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user && !authLoading) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadBusinesses();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authLoading]);

  const renderContent = () => {
    if (authLoading) {
      return (
        <DashboardLayout>
          <div className="flex items-center justify-center h-64">
            <LoadingState variant="dots" size="lg" text="Loading profile..." />
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
                Business Profile
              </h1>
              <p className="text-text-muted mt-1">
                Manage your business information for personalized recommendations.
              </p>
            </div>
            {!editMode && !isCreate && (
              <Button variant="outline" size="md" leftIcon={<Edit className="w-4 h-4" />} onClick={() => setEditMode(true)}>
                Edit Profile
              </Button>
            )}
          </div>

          {error && (
            <div className="bg-error/5 border border-error/20 rounded-[16px] p-4 flex items-center justify-between">
              <p className="text-error text-sm">{error}</p>
              <Button variant="ghost" size="sm" onClick={() => setError(null)}>Dismiss</Button>
            </div>
          )}

          {businesses.length > 1 && !editMode && !isCreate && (
            <Card variant="outlined" padding="md">
              <CardContent>
                <div className="flex items-center gap-4">
                  <Building2 className="w-5 h-5 text-accent-lime" aria-hidden="true" />
                  <span className="font-medium text-text-primary">Switch Business:</span>
                  <select
                    value={currentBusiness?.id || ""}
                    onChange={(e) => {
                      const biz = businesses.find(b => b.id === e.target.value);
                      if (biz) {
                        setCurrentBusiness(biz);
                        populateForm(biz);
                      }
                    }}
                    className="flex-1 max-w-md px-4 py-2 rounded-xl border border-border bg-bg-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-lime focus:border-transparent"
                  >
                    {businesses.map(biz => (
                      <option key={biz.id} value={biz.id}>
                        {biz.business_name} {biz.is_default && "(Default)"}
                      </option>
                    ))}
                  </select>
                  <Button variant="ghost" size="sm" onClick={handleNewBusiness} leftIcon={<Plus className="w-4 h-4" />}>
                    New Business
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {editMode || isCreate ? (
            <BusinessForm 
              formData={formData}
              handleChange={handleChange}
              handleSubmit={handleSubmit}
              saving={saving}
              isCreate={isCreate}
              currentBusiness={currentBusiness}
              onCancel={() => { 
                setEditMode(false); 
                if (isCreate) router.push("/profile"); 
              }}
            />
          ) : currentBusiness ? (
            <BusinessView 
              business={currentBusiness} 
              businesses={businesses}
              onDelete={handleDelete}
            />
          ) : (
            <EmptyState
              icon={Building2}
              title="No business profile yet"
              description="Create your first business profile to unlock personalized scheme recommendations, compliance roadmaps, and AI assistance."
              action={{ label: "Create Business Profile", onClick: handleNewBusiness, variant: "lime" }}
              alignment="center"
            />
          )}
        </div>
      </DashboardLayout>
    );
  };

  return renderContent();
}

export default function ProfilePage() {
  return (
    <Suspense fallback={
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <LoadingState variant="dots" size="lg" text="Loading profile..." />
        </div>
      </DashboardLayout>
    }>
      <ProfilePageContent />
    </Suspense>
  );
}
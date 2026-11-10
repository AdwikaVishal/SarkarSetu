# SarkarSetu Frontend - Detailed Analysis

## Overview
The SarkarSetu frontend is a **Next.js 16.4.5** application (app router mode) built with **React 19** that helps Indian entrepreneurs and MSMEs navigate government services, business registration, schemes, compliance, and document management.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Next.js 16.4.5 (App Router) |
| **Language** | TypeScript 5 |
| **Styling** | Tailwind CSS v4 + Custom CSS Variables |
| **UI Components** | Shadcn/ui primitives (Card, Button, Badge, etc.) |
| **Icons** | lucide-react |
| **State Management** | React Context (AuthContext) + @tanstack/react-query |
| **HTTP Client** | Custom fetch wrapper with auth interceptor (lib/api.ts) |
| **Forms** | React hooks (useState, useEffect) |
| **Routing** | Next.js `/app` directory with client & server components |

## Color Palette (from `globals.css`)
- `--color-bg-primary: #2856B8` (Navy - main background)
- `--color-bg-dark: #17243A` (Dark navy)
- `--color-bg-card: #F7F2E8` (Off-white - card backgrounds)
- `--color-bg-elevated: #FFFFFF` (White)
- `--color-text-primary: #17243A` (Dark navy - primary text)
- `--color-text-muted: #657080` (Muted gray)
- `--color-text-inverse: #2856B8` (Navy - inverse text)
- `--color-accent-yellow: #F5C84C` (Gold accent)
- `--color-accent-blue: #4D83D7` (Blue accent)
- `--color-border: #26334A` (Border color)
- `--color-success: #3D8661` (Green - eligibility)
- `--color-warning: #D89534` (Orange - warnings)
- `--color-error: #C65B55` (Red - errors)

## Typography
- **Font Heading**: Space Grotesk (used for h1-h6, navigation labels, headings)
- **Font Body**: Inter (used for body text)

## Architecture

### 1. Layout Structure

The app uses a **`DashboardLayout`** wrapper that provides:
- **Sidebar navigation** (collapsible to 20px on mobile/desktop)
- **Top bar** for mobile (hamburger menu + logo)
- **Auth-aware routing** - shows loading/empty states based on auth status
- **Consistent page structure** with sidebar + main content area

```tsx
// DashboardLayout provides:
- Fixed sidebar with navigation links
- Mobile hamburger menu
- User profile section with logout
- Main content area with proper padding
```

### 2. Context Providers (at `layout.tsx` root)

Two providers wrap the entire application:

```tsx
// AuthProvider - manages authentication state
- Handles login/register via API
- Stores tokens in localStorage  
- Provides `user`, `isLoading`, `login`, `register`, `logout` functions
- Dev mode auto-login with demo credentials

// APIProvider - TanStack React Query wrapper
- Provides queryClient with 5min staleTime
- Global retry config (retry: 1)
- Centralized data fetching state
```

### 3. Page Routing Structure

The `/app` directory contains these route groups:

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `app/page.tsx` | Home - redirects to `/dashboard` |
| `/dashboard` | `app/dashboard/page.tsx` | Main dashboard with stats, roadmaps, assessments, documents |
| `/assistant` | `app/assistant/page.tsx` | AI chat assistant with conversation history |
| `/schemes` | *(not in app dir - likely static or API-driven)* |
| `/eligibility` | `app/eligibility/page.tsx` | Eligibility checker for government schemes |
| `/profile` | `app/profile/page.tsx` | Business profile creation/editing |
| `/roadmap` | `app/roadmap/page.tsx` | Compliance roadmaps with tasks |
| `/documents` | `app/documents/page.tsx` | Document upload and management |
| `/settings` | `app/settings/page.tsx` | User settings and account management |
| `/not-found` | `app/not-found/page.tsx` | 404 page |

### 4. Key Components

#### Navigation
- **`Navbar`** - Desktop/mobile navbar with logo, nav links, mobile menu
- **`Footer`** - Footer with product, resources, company, legal links
- **`DashboardLayout`** - Full-page layout with sidebar navigation

#### UI Primitives (shadcn/ui style)
- **`Card`** - Versatile card component with variant support
- **`Button`** - Primary/outline/lime variants with loading states
- **`Badge`** - Status badges (eligible, pending, completed, etc.)
- **`StatusBadge`** - Document/compliance status indicators
- **`LoadingState`** - Spinner/loading indicators
- **`EmptyState`** - Empty state illustrations with actions
- **`SectionHeading`** - Consistent section headers with eyebrow/subtitle
- **`FileUploader`** - Drag-and-drop file upload with validation
- **`ConfirmDialog`** - Confirmation modals

#### Page-Specific Components

**Dashboard** (`app/dashboard/page.tsx`):
- `StatCard` - Statistic cards with icons and trends
- `InfoItem` - Label/value pairs
- `ConversationCard` - Clickable conversation items
- `RoadmapCard` - Roadmap progress display
- `AssessmentCard` - Eligibility assessment cards
- `QuickLink` - External portal links (Udyam, GST, etc.)

**Assistant** (`app/assistant/page.tsx`):
- AI chat interface with message bubbles
- Citation/source viewing
- Conversation management (create, load, delete)
- Suggested questions on welcome state

**Eligibility** (`app/eligibility/page.tsx`):
- Scheme selector with 10+ government schemes
- Business profile selector
- Real-time eligibility assessment
- `ConditionRow` - Individual rule check display
- `AssessmentDetailCard` - Full assessment details modal

**Profile** (`app/profile/page.tsx`):
- Multi-section business form
- Indian states dropdown (38 states/UTs)
- Completion percentage calculation
- View/archive business profiles
- Form validation (PIN code 6-digit, GSTIN format)

**Roadmap** (`app/roadmap/page.tsx`):
- Roadmap generation and tracking
- Task completion tracking
- Progress percentages
- Dependency graph awareness
- Completed roadmaps view

**Documents** (`app/documents/page.tsx`):
- File upload (PDF/images, max 5 files, 10MB each)
- AI-powered document extraction
- Compliance matching against schemes
- `DocumentDetailModal` - Full document view with extracted fields
- Feature cards (Text Extraction, Field Detection, Compliance Check)

**Settings** (`app/settings/page.tsx`):
- Tabbed interface (Profile, Business, Security, Notifications, Danger Zone)
- Profile information edit
- Business profile list
- Security settings (password 2FA - noted as "requires backend")
- Danger zone with account deletion

### 5. API Client (`lib/api.ts`)

Centralized fetch wrapper with:
- **Auth token management** (access/refresh tokens in localStorage)
- **Auto token refresh** on 401 responses
- **Error handling** with `ApiError` class
- **All API endpoints** categorized:
  - Auth (register, login, logout, me)
  - Business Profiles (CRUD operations)
  - Conversations (chat messages)
  - Eligibility assessment
  - Knowledge search (citations)
  - Roadmaps (generate, track tasks)
  - Workflows
  - AI/Intent operations
  - Documents (upload, list, matching, delete)
  - Recommendations

Key features:
- `fetchWithAuth` - Automatic token injection and refresh
- `fetchMultipart` - File upload support
- `isAuthenticated` helper
- Token expiry detection from JWT payload

### 6. Data Fetching

Uses **@tanstack/react-query** with:
- `staleTime: 5 minutes`
- `retry: 1`
- `refetchOnWindowFocus: false`
- Automatic caching and refetching

All page components use `useAuth()` hook to check authentication status before rendering content.

### 7. Form Handling

Forms use React controlled components with:
- `useState` for form data
- Validation functions (PIN code format, GSTIN format)
- `FormData` for submit handling
- Loading states with `isLoading` prop on buttons
- Cancel/edit modes

### 8. Styling Approach

**CSS Variables** in `globals.css`:
- All colors, fonts, spacings, radii, shadows, transitions defined as CSS custom properties
- Theme applied via `@tailwind base` and `@tailwind utilities`
- Dark mode support via `prefers-color-scheme`

**Tailwind Utilities**:
- `cn()` utility from `lib/utils.ts` using `clsx` + `tailwind-merge` for conditional classNames
- Component variants (primary, outline, lime, ghost, secondary)
- Responsive design (sm:, md:, lg: prefixes)
- Hover/focus states consistent across components

### 9. Key Features Implemented

1. **Authentication** - Login/register with token storage
2. **Business Profile Management** - Create/edit/view business profiles with 12+ fields
3. **Scheme Eligibility Checking** - 10+ government schemes with rule-based assessment
4. **AI Assistant** - Chat interface with conversation history and citations
5. **Document Management** - Upload, extract, and compliance matching
6. **Compliance Roadmaps** - Step-by-step task tracking for registrations
7. **Scheme Recommendations** - Personalized scheme suggestions based on profile
8. **User Settings** - Profile, business, security, notifications management

### 10. Known Limitations / TODOs

- **Backend integration**: Some API endpoints may not be fully implemented on the backend
- **Document processing**: Backend document upload/processing endpoints noted as "not yet implemented"
- **Security features**: Password change, 2FA, session management noted as "requires backend API support"
- **Notification system**: Notifications tab noted as "requires backend API support"
- **Scheme discovery**: `/schemes` route needs to be checked for full implementation

### 11. Development Workflow

```bash
# Install dependencies
npm install

# Development
npm run dev   # next dev with turbopack

# Build
npm run build # next build

# Start production
npm run start # next start
```

### 12. File Structure Summary

```
frontend/
├── src/
│   ├── app/              # Next.js app router pages
│   ├── components/       # Reusable UI components
│   │   ├── layout/       # Navbar, Footer, PageContainer
│   │   ├── ui/           # shadcn-style primitives
│   │   └── dashboard/    # Dashboard-specific components
│   ├── context/          # AuthContext, APIProvider
│   ├── lib/              # API client, utils (cn function)
│   └── types/            # TypeScript type definitions
├── globals.css           # CSS variables + Tailwind config
├── package.json          # Dependencies (Next 16, React 19, Tailwind 4)
└── tailwind.config.js    # Tailwind v4 configuration
```
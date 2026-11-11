import { Routes, Route, Navigate, useRoutes } from "react-router-dom";
import { APIProvider } from "@/context/APIProvider";
import { AuthProvider } from "@/context/AuthClient";
import DashboardPage from "@/app/dashboard/DashboardPage";
import AssistantPage from "@/app/assistant/AssistantPage";
import DocumentsPage from "@/app/documents/DocumentsPage";
import EligibilityPage from "@/app/eligibility/EligibilityPage";
import SchemesPage from "@/app/schemes/SchemesPage";
import RoadmapPage from "@/app/roadmap/RoadmapPage";
import SettingsPage from "@/app/settings/SettingsPage";
import KnowledgePage from "@/app/knowledge/KnowledgePage";
import AIToolsPage from "@/app/ai-tools/AIToolsPage";
import ServiceStatusPage from "@/app/system/ServiceStatusPage";
import TasksPage from "@/app/tasks/TasksPage";
import ActivityPage from "@/app/activity/ActivityPage";
import IntentPage from "@/app/intent/IntentPage";
import WorkflowsPage from "@/app/workflows/WorkflowsPage";
import RecommendationsPage from "@/app/recommendations/RecommendationsPage";
import ProfilePage from "@/app/profile/ProfilePage";

// Redirect root to dashboard
const rootRoute = {
  path: "/",
  element: <Navigate to="/dashboard" replace />,
};

// Other protected routes - all go directly to their pages since auth is handled via dev mode
const pageRoutes = {
  path: "/:page",
  element: ({ page }: { page: string }) => {
    const pageMap: Record<string, React.ReactElement> = {
      assistant: <AssistantPage />,
      documents: <DocumentsPage />,
      eligibility: <EligibilityPage />,
      schemes: <SchemesPage />,
      roadmap: <RoadmapPage />,
      settings: <SettingsPage />,
      knowledge: <KnowledgePage />,
      "ai-tools": <AIToolsPage />,
      status: <ServiceStatusPage />,
      tasks: <TasksPage />,
      activity: <ActivityPage />,
      intent: <IntentPage />,
      workflows: <WorkflowsPage />,
      recommendations: <RecommendationsPage />,
      profile: <ProfilePage />,
    };

    const element = pageMap[page as keyof typeof pageMap];
    return element || <Navigate to="/dashboard" replace />;
  },
};

export default function App() {
  return (
    <APIProvider>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="assistant" element={<AssistantPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="eligibility" element={<EligibilityPage />} />
          <Route path="schemes" element={<SchemesPage />} />
          <Route path="roadmap" element={<RoadmapPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="ai-tools" element={<AIToolsPage />} />
          <Route path="status" element={<ServiceStatusPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="activity" element={<ActivityPage />} />
          <Route path="intent" element={<IntentPage />} />
          <Route path="workflows" element={<WorkflowsPage />} />
          <Route path="recommendations" element={<RecommendationsPage />} />
          <Route path="profile" element={<ProfilePage />} />
          {/* Catch-all redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </APIProvider>
  );
}
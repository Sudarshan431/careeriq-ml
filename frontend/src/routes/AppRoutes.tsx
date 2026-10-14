import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

import { AuthLayout } from "../layouts/AuthLayout";
import { CandidateLayout } from "../layouts/CandidateLayout";
import { RecruiterLayout } from "../layouts/RecruiterLayout";
import { AdminLayout } from "../layouts/AdminLayout";

import { ProtectedRoute } from "./ProtectedRoute";
import { RoleRoute } from "./RoleRoute";

import { LoginPage } from "../pages/auth/LoginPage";
import { RegisterPage } from "../pages/auth/RegisterPage";

import { CandidateDashboardPage } from "../pages/candidate/DashboardPage";
import { CandidateProfilePage } from "../pages/candidate/ProfilePage";
import { CandidateResumePage } from "../pages/candidate/ResumePage";
import { CandidateJobsPage } from "../pages/candidate/JobsPage";
import { CandidateJobDetailPage } from "../pages/candidate/JobDetailPage";
import { CandidateSkillsPage } from "../pages/candidate/SkillsPage";
import { CandidateApplicationsPage } from "../pages/candidate/ApplicationsPage";
import { CandidateJobIntelligencePage } from "../pages/candidate/JobIntelligencePage";
import { CandidateCareerPlansPage } from "../pages/candidate/CareerPlansPage";
import { CandidateAssistantPage } from "../pages/candidate/AssistantPage";

import { RecruiterDashboardPage } from "../pages/recruiter/DashboardPage";
import { RecruiterJobsPage } from "../pages/recruiter/JobsPage";
import { RecruiterJobCreatePage } from "../pages/recruiter/JobCreatePage";
import { RecruiterJobDetailPage } from "../pages/recruiter/JobDetailPage";
import { RecruiterJobCandidatesPage } from "../pages/recruiter/JobCandidatesPage";
import { RecruiterJobApplicantsPage } from "../pages/recruiter/JobApplicantsPage";

import { AdminDashboardPage } from "../pages/admin/DashboardPage";

function RoleHomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  const home = user.role === "RECRUITER" ? "/recruiter/dashboard" : user.role === "ADMIN" ? "/admin/dashboard" : "/candidate/dashboard";
  return <Navigate to={home} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RoleHomeRedirect />} />

      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<RoleRoute allow={["CANDIDATE", "ADMIN"]} />}>
          <Route element={<CandidateLayout />}>
            <Route path="/candidate" element={<Navigate to="/candidate/dashboard" replace />} />
            <Route path="/candidate/dashboard" element={<CandidateDashboardPage />} />
            <Route path="/candidate/profile" element={<CandidateProfilePage />} />
            <Route path="/candidate/resume" element={<CandidateResumePage />} />
            <Route path="/candidate/jobs" element={<CandidateJobsPage />} />
            <Route path="/candidate/jobs/:id" element={<CandidateJobDetailPage />} />
            <Route path="/candidate/jobs/:id/intelligence" element={<CandidateJobIntelligencePage />} />
            <Route path="/candidate/applications" element={<CandidateApplicationsPage />} />
            <Route path="/candidate/skills" element={<CandidateSkillsPage />} />
            <Route path="/candidate/career-plans" element={<CandidateCareerPlansPage />} />
            <Route path="/candidate/assistant" element={<CandidateAssistantPage />} />
          </Route>
        </Route>

        <Route element={<RoleRoute allow={["RECRUITER", "ADMIN"]} />}>
          <Route element={<RecruiterLayout />}>
            <Route path="/recruiter" element={<Navigate to="/recruiter/dashboard" replace />} />
            <Route path="/recruiter/dashboard" element={<RecruiterDashboardPage />} />
            <Route path="/recruiter/jobs" element={<RecruiterJobsPage />} />
            <Route path="/recruiter/jobs/create" element={<RecruiterJobCreatePage />} />
            <Route path="/recruiter/jobs/:id" element={<RecruiterJobDetailPage />} />
            <Route path="/recruiter/jobs/:id/candidates" element={<RecruiterJobCandidatesPage />} />
            <Route path="/recruiter/jobs/:id/applicants" element={<RecruiterJobApplicantsPage />} />
          </Route>
        </Route>

        <Route element={<RoleRoute allow={["ADMIN"]} />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

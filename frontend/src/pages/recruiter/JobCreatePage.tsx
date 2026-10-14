import { useNavigate } from "react-router-dom";
import { JobForm } from "../../components/recruiter/JobForm";

export function RecruiterJobCreatePage() {
  const navigate = useNavigate();
  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Create Job</h1>
      <p className="mt-1 text-sm text-slate-500">Paste a job description; skills and requirements are extracted automatically.</p>
      <div className="mt-6 max-w-2xl">
        <JobForm onCreated={(jobId) => navigate(`/recruiter/jobs/${jobId}`)} />
      </div>
    </div>
  );
}

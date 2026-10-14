import { useState } from "react";
import { Badge } from "../ui/Badge";
import { getApiErrorMessage } from "../../api/client";
import { applicationsApi } from "../../api/applications";
import { formatDate, formatPercent } from "../../utils/formatters";
import { APPLICATION_STATUSES } from "../../types/application";
import type { ApplicationResponse, ApplicationStatus } from "../../types/application";

export function ApplicantRow({ application, onStatusChange }: { application: ApplicationResponse; onStatusChange: (updated: ApplicationResponse) => void }) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleChange(newStatus: ApplicationStatus) {
    setIsUpdating(true);
    setError(null);
    try {
      const updated = await applicationsApi.updateStatus(application.id, newStatus);
      onStatusChange(updated);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsUpdating(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 border-b border-slate-100 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-medium text-slate-900">{application.candidate_email || "Candidate"}</p>
        <p className="text-xs text-slate-500">Applied {formatDate(application.applied_at)}</p>
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
      <div className="flex items-center gap-3">
        {application.match_score !== null && (
          <Badge tone={application.match_score >= 80 ? "success" : application.match_score >= 50 ? "warning" : "danger"}>
            {formatPercent(application.match_score)} match
          </Badge>
        )}
        <select
          value={application.status}
          disabled={isUpdating}
          onChange={(e) => handleChange(e.target.value as ApplicationStatus)}
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
        >
          {APPLICATION_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

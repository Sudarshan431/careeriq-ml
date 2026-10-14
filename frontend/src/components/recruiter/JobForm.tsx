import { useState, type FormEvent } from "react";
import { Button } from "../ui/Button";
import { getApiErrorMessage } from "../../api/client";
import { jobsApi } from "../../api/jobs";

export function JobForm({ onCreated }: { onCreated: (jobId: string) => void }) {
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const result = await jobsApi.create(description);
      onCreated(result.job_id);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Job description</label>
        <textarea
          required
          rows={12}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={"Paste the full job description here.\n\nInclude a Required Skills section, Preferred Skills section, and experience requirement for best results."}
          className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" isLoading={isLoading} className="self-start">
        Create job
      </Button>
    </form>
  );
}

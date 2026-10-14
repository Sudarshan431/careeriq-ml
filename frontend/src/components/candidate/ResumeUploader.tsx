import { useRef, useState, type DragEvent } from "react";
import { UploadCloud, FileText, CheckCircle2 } from "lucide-react";
import { Button } from "../ui/Button";
import { getApiErrorMessage } from "../../api/client";
import { candidatesApi } from "../../api/candidates";
import type { CandidateProfileResponse } from "../../types/candidate";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];
const MAX_SIZE_MB = 10;

export function ResumeUploader({ candidateId, onSuccess }: { candidateId: string; onSuccess: (profile: CandidateProfileResponse) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function validate(f: File): string | null {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) return "Only .pdf, .docx, and .txt files are supported.";
    if (f.size > MAX_SIZE_MB * 1024 * 1024) return `File must be under ${MAX_SIZE_MB}MB.`;
    return null;
  }

  function handleFile(f: File) {
    const err = validate(f);
    if (err) {
      setError(err);
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
    setSuccess(false);
  }

  async function upload() {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    setProgress(0);
    try {
      const profile = await candidatesApi.uploadResume(candidateId, file, setProgress);
      setSuccess(true);
      onSuccess(profile);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
          dragOver ? "border-brand-500 bg-brand-50" : "border-slate-300 bg-slate-50"
        }`}
      >
        {file ? <FileText className="h-8 w-8 text-brand-600" /> : <UploadCloud className="h-8 w-8 text-slate-400" />}
        {file ? (
          <p className="text-sm font-medium text-slate-700">{file.name}</p>
        ) : (
          <>
            <p className="text-sm font-medium text-slate-700">Drag and drop your resume here</p>
            <p className="text-xs text-slate-500">PDF, DOCX, or TXT — up to {MAX_SIZE_MB}MB</p>
          </>
        )}
        <Button variant="secondary" size="sm" onClick={() => inputRef.current?.click()}>
          Browse files
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {file && !error && (
        <div className="mt-4 flex items-center gap-3">
          <Button onClick={upload} isLoading={isUploading}>
            Upload &amp; Analyze
          </Button>
          {isUploading && <span className="text-sm text-slate-500">{progress}%</span>}
          {success && (
            <span className="flex items-center gap-1 text-sm font-medium text-green-600">
              <CheckCircle2 className="h-4 w-4" /> Profile updated
            </span>
          )}
        </div>
      )}
    </div>
  );
}

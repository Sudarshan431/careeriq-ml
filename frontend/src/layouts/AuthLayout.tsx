import { Outlet } from "react-router-dom";
import { Briefcase } from "lucide-react";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-2">
          <Briefcase className="h-6 w-6 text-brand-600" />
          <span className="text-xl font-semibold text-slate-900">CareerIQ</span>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

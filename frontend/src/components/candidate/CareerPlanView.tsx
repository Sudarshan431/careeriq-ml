import { Badge } from "../ui/Badge";
import { formatPercent } from "../../utils/formatters";
import type { CareerPlanResponse } from "../../types/careerPlan";

export function CareerPlanView({ plan }: { plan: CareerPlanResponse }) {
  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-900">{plan.target_role}</p>
          <p className="text-xs text-slate-500">{plan.summary}</p>
        </div>
        <Badge tone={plan.job_readiness_percent >= 70 ? "success" : plan.job_readiness_percent >= 40 ? "warning" : "danger"}>
          {formatPercent(plan.job_readiness_percent)} ready
        </Badge>
      </div>
      {plan.job_readiness_assessment && <p className="mb-4 text-sm text-slate-600">{plan.job_readiness_assessment}</p>}
      <div className="space-y-5">
        {plan.milestones.map((milestone) => (
          <div key={milestone.label}>
            <p className="mb-2 text-sm font-semibold text-slate-900">{milestone.label}</p>
            <ul className="space-y-2">
              {milestone.steps.map((step) => (
                <li key={step.skill} className="rounded-lg bg-slate-50 p-3 text-sm">
                  <p className="font-medium text-slate-800">{step.skill}</p>
                  {step.practice_suggestion && <p className="mt-1 text-xs text-slate-500">{step.practice_suggestion}</p>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

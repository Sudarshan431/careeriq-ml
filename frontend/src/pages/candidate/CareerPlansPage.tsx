import { useEffect, useState } from "react";
import { Route as RouteIcon } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { careerPlanApi } from "../../api/careerPlan";
import { Card, CardBody } from "../../components/ui/Card";
import { CareerPlanView } from "../../components/candidate/CareerPlanView";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import type { CareerPlanResponse } from "../../types/careerPlan";

export function CandidateCareerPlansPage() {
  const { candidateId } = useAuth();
  const [plans, setPlans] = useState<CareerPlanResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!candidateId) return;
    careerPlanApi
      .list(candidateId)
      .then(setPlans)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [candidateId]);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Career Plans</h1>
      <p className="mt-1 text-sm text-slate-500">Your saved learning roadmaps toward specific roles.</p>

      <div className="mt-6">
        {isLoading ? (
          <LoadingBlock />
        ) : error ? (
          <ErrorState message={error} />
        ) : plans.length === 0 ? (
          <EmptyState
            icon={<RouteIcon className="h-8 w-8" />}
            title="No career plans yet."
            description="Open a job you're interested in and generate a plan from its skill-gap page."
          />
        ) : (
          <div className="space-y-6">
            {plans.map((plan) => (
              <Card key={plan.plan_id}>
                <CardBody>
                  <CareerPlanView plan={plan} />
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

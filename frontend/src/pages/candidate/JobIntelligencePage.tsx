import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Target, BookOpen, Route as RouteIcon } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { skillGapApi } from "../../api/skillGap";
import { learningApi } from "../../api/learning";
import { careerPlanApi } from "../../api/careerPlan";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { SkillPriorityList } from "../../components/candidate/SkillPriorityList";
import { LearningRecommendationList } from "../../components/candidate/LearningRecommendationList";
import { CareerPlanView } from "../../components/candidate/CareerPlanView";
import { AssistantChat } from "../../components/candidate/AssistantChat";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { getApiErrorMessage } from "../../api/client";
import type { JobSkillGapResponse } from "../../types/skillGap";
import type { LearningRecommendationsResponse } from "../../types/learning";
import type { CareerPlanResponse } from "../../types/careerPlan";

export function CandidateJobIntelligencePage() {
  const { id } = useParams<{ id: string }>();
  const { candidateId } = useAuth();
  const [skillGap, setSkillGap] = useState<JobSkillGapResponse | null>(null);
  const [learning, setLearning] = useState<LearningRecommendationsResponse | null>(null);
  const [plan, setPlan] = useState<CareerPlanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !candidateId) return;
    setIsLoading(true);
    setError(null);
    Promise.all([skillGapApi.forJob(candidateId, id), learningApi.forJob(candidateId, id)])
      .then(([gapResult, learningResult]) => {
        setSkillGap(gapResult);
        setLearning(learningResult);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [id, candidateId]);

  async function handleGeneratePlan() {
    if (!id || !candidateId) return;
    setIsGeneratingPlan(true);
    setPlanError(null);
    try {
      const result = await careerPlanApi.generate(candidateId, id);
      setPlan(result);
    } catch (err) {
      setPlanError(getApiErrorMessage(err));
    } finally {
      setIsGeneratingPlan(false);
    }
  }

  if (isLoading) return <LoadingBlock label="Analyzing skill gap and learning path…" />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <Link to={`/candidate/jobs/${id}`} className="mb-4 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to job
      </Link>
      <h1 className="text-2xl font-semibold text-slate-900">
        {skillGap ? `Path to ${skillGap.target_job.title}` : "Career Intelligence"}
      </h1>
      {skillGap && <p className="mt-1 text-sm text-slate-500">{skillGap.analysis.assessment}</p>}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex items-center gap-2">
            <Target className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-slate-900">Skill Gaps</h3>
          </CardHeader>
          <CardBody>{skillGap && <SkillPriorityList items={skillGap.skill_priorities} />}</CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-slate-900">What to Learn</h3>
          </CardHeader>
          <CardBody>{learning && <LearningRecommendationList items={learning.recommendations} />}</CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RouteIcon className="h-4 w-4 text-brand-600" />
              <h3 className="text-sm font-semibold text-slate-900">Career Plan</h3>
            </div>
            {!plan && (
              <Button size="sm" onClick={handleGeneratePlan} isLoading={isGeneratingPlan}>
                Generate plan
              </Button>
            )}
          </CardHeader>
          <CardBody>
            {planError && <p className="mb-2 text-sm text-red-600">{planError}</p>}
            {plan ? <CareerPlanView plan={plan} /> : <p className="text-sm text-slate-400">Generate a milestone-based plan toward this role.</p>}
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <AssistantChat jobId={id} />
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

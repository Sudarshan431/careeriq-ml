import { Card, CardBody } from "../../components/ui/Card";
import { AssistantChat } from "../../components/candidate/AssistantChat";

export function CandidateAssistantPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">AI Career Assistant</h1>
      <p className="mt-1 text-sm text-slate-500">
        Ask about your skills, matches, or what to learn next. Answers are grounded in your real CareerIQ data.
      </p>
      <Card className="mt-6 max-w-2xl">
        <CardBody>
          <AssistantChat />
        </CardBody>
      </Card>
    </div>
  );
}

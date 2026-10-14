export interface AssistantChatRequest {
  message: string;
  job_id?: string;
  conversation_id?: string;
}

export interface AssistantChatResponse {
  answer: string;
  context: Record<string, unknown>;
  conversation_id: string;
}

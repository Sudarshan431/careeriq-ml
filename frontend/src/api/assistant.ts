import { client } from "./client";
import type { AssistantChatRequest, AssistantChatResponse } from "../types/assistant";

export const assistantApi = {
  chat: (payload: AssistantChatRequest) => client.post<AssistantChatResponse>("/api/v1/assistant/chat", payload).then((r) => r.data),
};

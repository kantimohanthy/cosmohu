import { AnswerResponse, Source, Entity, IngestionJob, EvidencePassage } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function executeResearchQuery(query: string): Promise<any> {
  const res = await fetch(`${API_BASE}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Research API error (${res.status}): ${errorText}`);
  }
  return res.json();
}

export async function fetchWhyConclusionEvidenceChain(propositionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/research/${propositionId}/evidence`);
  if (!res.ok) throw new Error("Failed to fetch evidence chain");
  return res.json();
}

export async function executeQuery(query: string, topK: number = 5): Promise<AnswerResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error (${res.status}): ${errorText}`);
  }
  return res.json();
}

export async function fetchSources(): Promise<Source[]> {
  const res = await fetch(`${API_BASE}/sources`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  return res.json();
}

export async function fetchEntities(): Promise<Entity[]> {
  const res = await fetch(`${API_BASE}/entities`);
  if (!res.ok) throw new Error("Failed to fetch entities");
  return res.json();
}

export async function triggerIngestion(sourceId: string): Promise<IngestionJob> {
  const res = await fetch(`${API_BASE}/ingestion/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: sourceId }),
  });
  if (!res.ok) throw new Error("Failed to trigger ingestion job");
  return res.json();
}

export async function fetchIngestionJob(jobId: string): Promise<IngestionJob> {
  const res = await fetch(`${API_BASE}/ingestion/jobs/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch job status");
  return res.json();
}

export async function fetchEvidenceDetails(passageId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/evidence/${passageId}`);
  if (!res.ok) throw new Error("Failed to fetch evidence passage details");
  return res.json();
}

export async function fetchEvaluationSuite(): Promise<any> {
  const res = await fetch(`${API_BASE}/eval`);
  if (!res.ok) throw new Error("Failed to run evaluation suite");
  return res.json();
}

// Research Sessions API Functions (Stage 4.3)
export async function createResearchSession(title?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/research/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create research session");
  return res.json();
}

export async function fetchResearchSessions(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/research/sessions`);
  if (!res.ok) throw new Error("Failed to fetch research sessions");
  return res.json();
}

export async function fetchResearchSession(sessionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/research/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch research session");
  return res.json();
}

export async function addQueryToResearchSession(sessionId: string, query: string): Promise<any> {
  const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/queries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Failed to add query to session (${res.status}): ${errText}`);
  }
  return res.json();
}

export async function deleteResearchSession(sessionId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/research/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete research session");
  return true;
}

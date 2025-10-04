import type { CompleteProjectData, DatabaseUser, DatabaseProject } from '../types';

export async function generateSubmission(topic: string, objective: string, guidelines: string) {
  const payload = { topic, objective, guidelines };
  const res = await fetch("/api/generate_submission/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Generate submission main panel failed");
  return res.json();
}

export async function generateSubmissionIndividualPanel(topic: string, objective: string, guidelines: string, user_special_instructions: string, panel_name: string) {
  const payload = { topic, objective, guidelines, user_special_instructions, panel_name };
  const res = await fetch("/api/generate_submission/individual_panel/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Generate submission individual panel failed");
  return res.json();
}

export async function acceptOrReject(payload: { panel_name: string; panel_name_content_id: string }) {
  const res = await fetch("/api/accept_or_reject/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Accept or reject failed");
  return res.json();
}

// New API functions to work with database data
export async function getProject(projectId: number): Promise<DatabaseProject> {
  const res = await fetch(`/api/projects/${projectId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to get project");
  return res.json();
}

export async function getCompleteProjectData(projectId: number): Promise<CompleteProjectData> {
  const res = await fetch(`/api/projects/${projectId}/complete`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to get complete project data");
  return res.json();
}

export async function getUser(userId: number): Promise<DatabaseUser> {
  const res = await fetch(`/api/users/${userId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to get user");
  return res.json();
}

export async function getUserProjects(userId: number): Promise<DatabaseProject[]> {
  const res = await fetch(`/api/users/${userId}/projects`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to get user projects");
  return res.json();
}

export async function updateLike(likeId: number): Promise<void> {
  const res = await fetch(`/api/likes/${likeId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to update like");
  return res.json();
}


import type { CompleteProjectData, DatabaseUser, DatabaseProject } from '../types';

export async function generateSubmission(topic: string, objective: string, guidelines: string, user_id: number) {
  const payload = { topic, objective, guidelines, user_id };
  const res = await fetch("/api/generate_submission/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Generate submission main panel failed");
  return res.json();
}

export async function generateSubmissionIndividualPanel(topic: string, objective: string, guidelines: string, user_special_instructions: string, panel_name: string, user_id: number, project_id: number, query_id: number) {
  const payload = { topic, objective, guidelines, user_special_instructions, panel_name, user_id, project_id, query_id };
  const res = await fetch("/api/generate_submission/individual_panel/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Generate submission individual panel failed");
  return res.json();
}

export async function acceptOrReject(payload: { 
  project_id: number; 
  target_type: "youtube" | "paper"; 
  target_id: number; 
  isLiked: boolean 
}) {
  const res = await fetch("/api/accept_or_reject/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Accept or reject failed");
  return res.json();
}

export async function updateLikeStatus(payload: { 
  liked_disliked_id: number;
}) {
  const res = await fetch("/api/accept_or_reject/update/", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Update like failed");
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

export async function createUser(name: string, email: string): Promise<{ success: boolean; user_id: number; name: string; email: string }> {
  const payload = { name, email };
  const res = await fetch("/api/users/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create user");
  return res.json();
}


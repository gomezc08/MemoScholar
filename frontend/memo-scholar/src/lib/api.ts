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

export async function generateSubmissionIndividualPanel(payload: { topic: string; objective: string; guidelines: string; user_special_instructions: string; panel_name: string }) {
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


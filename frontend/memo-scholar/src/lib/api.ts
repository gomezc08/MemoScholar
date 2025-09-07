export async function postFeedback(payload: { id: string; kind: string; label: "accept" | "reject" }) {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Feedback failed");
  }
  
  export async function saveProject(payload: { topic: string; objective: string; constraints: string }) {
    const res = await fetch("/api/project/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Save failed");
  }
  
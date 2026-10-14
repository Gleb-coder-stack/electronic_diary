const API = {
  async toggleSubmission(id) {
    const r = await fetch(`/api/submissions/${id}/toggle`, { method: "POST" });
    if (!r.ok) throw new Error("Ошибка отметки");
    return r.json();
  },
  async listTasks() {
    const r = await fetch("/api/tasks/");
    return r.json();
  },
  async listSubmissions() {
    const r = await fetch("/api/submissions/");
    return r.json();
  }
};
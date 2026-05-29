const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function authHeader(): Record<string, string> {
  const t = localStorage.getItem("token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function handle(res: Response) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail ?? detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

export const api = {
  url: API_URL,

  async login(email: string, password: string) {
    const body = new URLSearchParams({ username: email, password });
    const r = await fetch(`${API_URL}/api/auth/login`, { method: "POST", body });
    return handle(r);
  },

  async get(path: string) {
    const r = await fetch(`${API_URL}${path}`, { headers: authHeader() });
    return handle(r);
  },

  async post(path: string, body?: unknown) {
    const r = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: body ? JSON.stringify(body) : undefined,
    });
    return handle(r);
  },

  async patch(path: string, body: unknown) {
    const r = await fetch(`${API_URL}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(body),
    });
    return handle(r);
  },

  async put(path: string, body: unknown) {
    const r = await fetch(`${API_URL}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeader() },
      body: JSON.stringify(body),
    });
    return handle(r);
  },

  async delete(path: string) {
    const r = await fetch(`${API_URL}${path}`, { method: "DELETE", headers: authHeader() });
    return handle(r);
  },

  async upload(path: string, file: File, extra?: Record<string, string>) {
    const fd = new FormData();
    fd.append("file", file);
    Object.entries(extra ?? {}).forEach(([k, v]) => fd.append(k, v));
    const r = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { ...authHeader() },
      body: fd,
    });
    return handle(r);
  },

  async download(path: string, filename: string) {
    const r = await fetch(`${API_URL}${path}`, { headers: authHeader() });
    if (!r.ok) throw new Error(`download failed: ${r.statusText}`);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

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

  // Upload avec progression : `fetch` n'expose pas la progression d'envoi, donc
  // on passe par XMLHttpRequest. `onProgress` reçoit le % d'octets transférés
  // puis la phase "processing" une fois l'envoi terminé (le serveur travaille).
  uploadWithProgress(
    path: string,
    file: File,
    extra: Record<string, string> | undefined,
    onProgress: (pct: number, phase: "uploading" | "processing") => void,
  ): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const fd = new FormData();
      fd.append("file", file);
      Object.entries(extra ?? {}).forEach(([k, v]) => fd.append(k, v));

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_URL}${path}`);
      const token = localStorage.getItem("token");
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          onProgress(pct, pct >= 100 ? "processing" : "uploading");
        }
      };
      xhr.upload.onload = () => onProgress(100, "processing");

      xhr.onload = () => {
        const ct = xhr.getResponseHeader("content-type") ?? "";
        if (xhr.status >= 200 && xhr.status < 300) {
          if (xhr.status === 204 || !xhr.responseText) return resolve(null);
          resolve(ct.includes("application/json") ? JSON.parse(xhr.responseText) : xhr.responseText);
          return;
        }
        let detail = xhr.statusText || `échec (${xhr.status})`;
        try {
          detail = JSON.parse(xhr.responseText).detail ?? detail;
        } catch {
          // réponse non-JSON (ex. page 502 du proxy) : on garde le statut
        }
        reject(new Error(detail));
      };
      xhr.onerror = () =>
        reject(new Error("Connexion au serveur impossible (réseau ou serveur indisponible)."));
      xhr.ontimeout = () => reject(new Error("Délai dépassé pendant le dépôt."));

      xhr.send(fd);
    });
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

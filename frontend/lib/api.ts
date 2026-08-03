export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(path: string, init?: RequestInit) {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || JSON.stringify(j);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export function uploadExcel(file: File) {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${API_URL}/api/datasets/upload`, { method: "POST", body: form }).then((r) =>
    r.json().then((j) => {
      if (!r.ok) throw new Error(j.detail || "Upload failed");
      return j;
    })
  );
}

export const api = {
  get: (path: string) => request(path),
  post: (path: string, body?: unknown) => request(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

export function downloadUrl(datasetId: string) {
  return `${API_URL}/api/datasets/${datasetId}/download`;
}
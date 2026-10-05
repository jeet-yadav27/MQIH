async function readError(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) {
    const lines = [detail.message];
    if (detail.missing_columns?.length) {
      lines.push(`Missing: ${detail.missing_columns.join(", ")}`);
    }
    if (detail.unknown_columns?.length) {
      lines.push(`Unknown: ${detail.unknown_columns.join(", ")}`);
    }
    return lines.join(" ");
  }
  if (!response.ok) return `Request failed (${response.status}). Is the API running?`;
  return "Request failed.";
}

async function request(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("Cannot reach the API. Start the FastAPI server on port 8000.");
  }
  if (!response.ok) throw new Error(await readError(response));
  const type = response.headers.get("content-type") || "";
  if (type.includes("application/json")) return response.json();
  return response;
}

export const getHealth = () => request("/health");
export const getMeta = () => request("/meta");
export const getBasicCharts = () => request("/charts/basic");

export function uploadFile(file) {
  const body = new FormData();
  body.append("file", file);
  return request("/upload", { method: "POST", body });
}

export const loadSample = () => request("/upload/sample", { method: "POST" });

export function customChart(payload) {
  return request("/charts/custom", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function downloadDatabase() {
  const response = await request("/export");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ftir_records.csv";
  link.click();
  URL.revokeObjectURL(url);
}

export async function downloadTemplate() {
  const response = await request("/meta/template");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ftir_template.csv";
  link.click();
  URL.revokeObjectURL(url);
}

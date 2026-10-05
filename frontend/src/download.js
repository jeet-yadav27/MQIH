function slug(name) {
  return String(name || "chart")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "chart";
}

function trigger(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function downloadChartPng(node, filename) {
  const svg = node?.querySelector("svg");
  if (!svg) return;
  const rect = svg.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));
  const clone = svg.cloneNode(true);
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height));
  if (!clone.getAttribute("xmlns")) {
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  }
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", "0");
  bg.setAttribute("y", "0");
  bg.setAttribute("width", String(width));
  bg.setAttribute("height", String(height));
  bg.setAttribute("fill", "#fffdf8");
  clone.insertBefore(bg, clone.firstChild);
  const xml = new XMLSerializer().serializeToString(clone);
  const url = URL.createObjectURL(new Blob([xml], { type: "image/svg+xml;charset=utf-8" }));
  const image = new Image();
  image.onload = () => {
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = width * scale;
    canvas.height = height * scale;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fffdf8";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(url);
    const link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = `${slug(filename)}.png`;
    link.click();
  };
  image.onerror = () => URL.revokeObjectURL(url);
  image.src = url;
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  if (/[",\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

export function downloadChartCsv(chart) {
  const rows = chart.kind === "scatter"
    ? chart.data.map((point) => ({
        [chart.x_label || "x"]: point.x,
        [chart.y_label || "y"]: point.y,
      }))
    : chart.data.map((point) => ({
        [chart.x_label || "category"]: point.label,
        [chart.y_label || "value"]: point.value,
      }));
  if (!rows.length) return;
  const keys = Object.keys(rows[0]);
  const lines = [keys.join(",")].concat(rows.map((row) => keys.map((key) => csvCell(row[key])).join(",")));
  trigger(new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" }), `${slug(chart.title)}.csv`);
}

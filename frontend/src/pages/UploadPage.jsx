import { useEffect, useState } from "react";
import { getMeta, loadSample, uploadFile, downloadTemplate } from "../api";

export default function UploadPage({ onUploaded }) {
  const [meta, setMeta] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");

  useEffect(() => {
    getMeta().then(setMeta).catch((err) => setError(err.message));
  }, []);

  async function send(file, sample = false) {
    setBusy(true);
    setError("");
    setFileName(sample ? "ftir_sample.csv" : file.name);
    try {
      const result = sample ? await loadSample() : await uploadFile(file);
      onUploaded(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function takeFile(file) {
    if (!file) return;
    const name = file.name.toLowerCase();
    if (!name.endsWith(".csv") && !name.endsWith(".xlsx")) {
      setError("Upload a .csv or .xlsx file.");
      return;
    }
    send(file);
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Import</p>
          <h2>Upload FTIR records</h2>
          <p className="lede">
            CSV or Excel files are checked against the records schema, then stored in SQLite. A successful import opens the overview charts.
          </p>
        </div>
      </header>

      <section
        className={`dropzone ${dragging ? "dragging" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          takeFile(event.dataTransfer.files?.[0]);
        }}
      >
        <p className="drop-title">{busy ? "Importing…" : "Drop a file here"}</p>
        <p className="muted">or choose one from your computer. Up to 25 MB.</p>
        <div className="row">
          <label className="button primary">
            {busy ? "Working" : "Choose file"}
            <input
              type="file"
              accept=".csv,.xlsx"
              hidden
              disabled={busy}
              onChange={(event) => {
                takeFile(event.target.files?.[0]);
                event.target.value = "";
              }}
            />
          </label>
          <button type="button" className="button" disabled={busy} onClick={() => send(null, true)}>
            Load sample data
          </button>
          <button type="button" className="button ghost" onClick={() => downloadTemplate().catch((err) => setError(err.message))}>
            Download template
          </button>
        </div>
        {fileName && busy && <p className="muted">{fileName}</p>}
      </section>

      {error && (
        <div className="banner error" role="alert">
          {error}
        </div>
      )}

      {meta && (
        <section className="card flat">
          <h3>Expected columns</h3>
          <p className="muted">Required fields must be present. Other schema columns are optional and can be left out of the file.</p>
          <div className="chips">
            {meta.required.map((col) => (
              <span key={col.name} className="chip required" title={col.name}>
                {col.label}
              </span>
            ))}
          </div>
          <p className="section-label">Optional</p>
          <div className="chips">
            {meta.optional.map((col) => (
              <span key={col.name} className="chip" title={col.name}>
                {col.label}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

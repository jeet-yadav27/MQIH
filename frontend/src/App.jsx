import { useEffect, useState } from "react";
import { downloadDatabase, getHealth } from "./api";
import BuilderPage from "./pages/BuilderPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";

const NAV = [
  { id: "dashboard", label: "Dashboard" },
  { id: "upload", label: "Upload" },
  { id: "builder", label: "Chart builder" },
];

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [open, setOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [notice, setNotice] = useState(null);
  const [records, setRecords] = useState(null);
  const [exportError, setExportError] = useState("");

  useEffect(() => {
    getHealth()
      .then((data) => setRecords(data.records))
      .catch(() => setRecords(null));
  }, [refreshKey]);

  function go(next) {
    setPage(next);
    setOpen(false);
  }

  function onUploaded(result) {
    setNotice(result);
    setRefreshKey((value) => value + 1);
    setPage("dashboard");
    setOpen(false);
  }

  return (
    <div className="shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <span className="mark">MQ</span>
          <div>
            <strong>MQIH</strong>
            <p>Field quality</p>
          </div>
        </div>
        <nav>
          {NAV.map((item) => (
            <button key={item.id} type="button" className={page === item.id ? "active" : ""} onClick={() => go(item.id)} aria-current={page === item.id ? "page" : undefined}>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <p>{records == null ? "Database offline" : `${records.toLocaleString()} records`}</p>
          <button
            type="button"
            onClick={() => {
              setExportError("");
              downloadDatabase().catch((err) => setExportError(err.message));
            }}
          >
            Export data
          </button>
          {exportError && <p className="side-error">{exportError}</p>}
        </div>
      </aside>
      {open && <button type="button" className="scrim" aria-label="Close menu" onClick={() => setOpen(false)} />}
      <div className="main">
        <header className="topbar">
          <button type="button" className="menu" onClick={() => setOpen((value) => !value)} aria-label="Open menu">
            Menu
          </button>
          <p>{NAV.find((item) => item.id === page)?.label}</p>
        </header>
        {page === "dashboard" && (
          <DashboardPage refreshKey={refreshKey} notice={notice} onDismiss={() => setNotice(null)} />
        )}
        {page === "upload" && <UploadPage onUploaded={onUploaded} />}
        {page === "builder" && <BuilderPage />}
      </div>
    </div>
  );
}

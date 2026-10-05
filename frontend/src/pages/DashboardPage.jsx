import { useEffect, useState } from "react";
import { getBasicCharts } from "../api";
import ChartCard from "../components/ChartCard";

function formatStat(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function formatPct(value) {
  if (value == null) return "—";
  return `${Math.round(Number(value) * 100)}%`;
}

export default function DashboardPage({ refreshKey, notice, onDismiss }) {
  const [state, setState] = useState({ loading: true, error: "", data: null });

  useEffect(() => {
    let cancel = false;
    setState((prev) => ({ ...prev, loading: true, error: "" }));
    getBasicCharts()
      .then((data) => {
        if (!cancel) setState({ loading: false, error: "", data });
      })
      .catch((err) => {
        if (!cancel) setState({ loading: false, error: err.message, data: null });
      });
    return () => {
      cancel = true;
    };
  }, [refreshKey]);

  const summary = state.data?.summary;
  const empty = summary && summary.record_count === 0;

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Overview</p>
          <h2>Field quality snapshot</h2>
          <p className="lede">Distributions, a report timeline, and summary statistics are built from the records currently in the database.</p>
        </div>
      </header>

      {notice && (
        <div className="banner ok" role="status">
          <div>
            <strong>{notice.message}</strong>
            <p>
              {notice.filename}
              {notice.sheet ? ` · sheet ${notice.sheet}` : ""} · {notice.rows_read} rows read · {notice.total_records} records in the database
            </p>
            {notice.optional_columns_omitted?.length > 0 && (
              <details>
                <summary>{notice.optional_columns_omitted.length} optional columns were not in the file</summary>
                <p>{notice.optional_columns_omitted.join(", ")}</p>
              </details>
            )}
            {notice.rows_rejected > 0 && (
              <p>{notice.rows_rejected} rows were skipped because the FTIR number was blank.</p>
            )}
          </div>
          <button type="button" className="icon-button" onClick={onDismiss} aria-label="Dismiss confirmation">
            ×
          </button>
        </div>
      )}

      {state.loading && <p className="muted">Building charts…</p>}
      {state.error && (
        <div className="banner error" role="alert">
          {state.error}
        </div>
      )}

      {empty && !state.loading && (
        <section className="card empty-state">
          <h3>No records yet</h3>
          <p>Upload a CSV or Excel extract, or load the sample file, and this page will fill with country, rank, status, and time-series charts.</p>
        </section>
      )}

      {summary && summary.record_count > 0 && (
        <>
          <section className="stat-grid">
            <article className="stat">
              <p>Records</p>
              <strong>{summary.record_count.toLocaleString()}</strong>
            </article>
            <article className="stat">
              <p>Resolved</p>
              <strong>{formatPct(summary.resolved_rate)}</strong>
            </article>
            <article className="stat">
              <p>With SBPR</p>
              <strong>{formatPct(summary.sbpr_rate)}</strong>
            </article>
            <article className="stat">
              <p>Median km</p>
              <strong>{formatStat(summary.measures?.[1]?.median)}</strong>
            </article>
          </section>

          <section className="card flat">
            <h3>Summary statistics</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Measure</th>
                    <th>Count</th>
                    <th>Mean</th>
                    <th>Median</th>
                    <th>Min</th>
                    <th>Max</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.measures.map((measure) => (
                    <tr key={measure.column}>
                      <td>{measure.label}</td>
                      <td>{measure.count.toLocaleString()}</td>
                      <td>{formatStat(measure.mean)}</td>
                      <td>{formatStat(measure.median)}</td>
                      <td>{formatStat(measure.min)}</td>
                      <td>{formatStat(measure.max)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="chart-grid">
            {state.data.charts.map((chart) => (
              <ChartCard key={chart.id} chart={chart} />
            ))}
          </section>
        </>
      )}
    </div>
  );
}

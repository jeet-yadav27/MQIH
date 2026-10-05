import { useEffect, useState } from "react";
import { customChart, getMeta } from "../api";
import ChartCard from "../components/ChartCard";

const TYPES = [
  { id: "bar", label: "Bar" },
  { id: "line", label: "Line" },
  { id: "pie", label: "Pie" },
  { id: "scatter", label: "Scatter" },
];

export default function BuilderPage() {
  const [meta, setMeta] = useState(null);
  const [chartType, setChartType] = useState("bar");
  const [x, setX] = useState("outbreak_country");
  const [y, setY] = useState("days_used");
  const [agg, setAgg] = useState("count");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [chart, setChart] = useState(null);

  useEffect(() => {
    getMeta()
      .then((data) => {
        setMeta(data);
        if (data.categorical?.length) setX(data.categorical.find((col) => col.name === "outbreak_country")?.name || data.categorical[0].name);
        if (data.numeric?.length) setY(data.numeric[0].name);
      })
      .catch((err) => setError(err.message));
  }, []);

  const xOptions = chartType === "scatter" ? meta?.numeric || [] : [...(meta?.categorical || []), ...(meta?.date || []), ...(meta?.numeric || [])];
  const needsY = chartType === "scatter" || agg !== "count";

  useEffect(() => {
    if (!xOptions.length) return;
    if (!xOptions.some((col) => col.name === x)) setX(xOptions[0].name);
  }, [chartType, meta]);

  async function generate(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const payload = { chart_type: chartType, x, agg: chartType === "pie" ? "count" : agg };
      if (chartType === "scatter" || (chartType !== "pie" && agg !== "count")) payload.y = y;
      if (chartType === "scatter") payload.y = y;
      const result = await customChart(payload);
      setChart(result);
    } catch (err) {
      setChart(null);
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Explore</p>
          <h2>Chart builder</h2>
          <p className="lede">Pick a chart type and columns. The API aggregates the database and this page draws the result.</p>
        </div>
      </header>

      <div className="builder">
        <form className="card flat builder-form" onSubmit={generate}>
          <label>
            Chart type
            <div className="segmented">
              {TYPES.map((type) => (
                <button
                  key={type.id}
                  type="button"
                  className={chartType === type.id ? "on" : ""}
                  onClick={() => setChartType(type.id)}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </label>

          <label>
            X axis
            <select value={x} onChange={(event) => setX(event.target.value)}>
              {xOptions.map((col) => (
                <option key={col.name} value={col.name}>
                  {col.label}
                </option>
              ))}
            </select>
          </label>

          {chartType !== "scatter" && chartType !== "pie" && (
            <label>
              Aggregation
              <select value={agg} onChange={(event) => setAgg(event.target.value)}>
                <option value="count">Count</option>
                <option value="mean">Mean</option>
                <option value="median">Median</option>
                <option value="sum">Sum</option>
              </select>
            </label>
          )}

          {needsY && (
            <label>
              {chartType === "scatter" ? "Y axis" : "Measure"}
              <select value={y} onChange={(event) => setY(event.target.value)}>
                {(meta?.numeric || []).map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.label}
                  </option>
                ))}
              </select>
            </label>
          )}

          <button type="submit" className="button primary" disabled={busy || !x}>
            {busy ? "Querying…" : "Generate chart"}
          </button>
          <p className="muted hint">
            Bar, line, and pie charts count categories unless you choose a numeric measure. Scatter plots compare two numeric columns.
          </p>
        </form>

        <div className="builder-result">
          {error && (
            <div className="banner error" role="alert">
              {error}
            </div>
          )}
          {!chart && !error && <section className="card empty-state"><h3>No chart yet</h3><p>Choose columns and generate a chart. You can download a PNG or the plotted rows as CSV.</p></section>}
          {chart && <ChartCard chart={chart} height={420} />}
          {chart?.data?.length > 0 && (
            <section className="card flat">
              <h3>Plotted data</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      {chart.kind === "scatter" ? (
                        <>
                          <th>{chart.x_label}</th>
                          <th>{chart.y_label}</th>
                        </>
                      ) : (
                        <>
                          <th>{chart.x_label}</th>
                          <th>{chart.y_label}</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {chart.data.slice(0, 40).map((row, index) => (
                      <tr key={`${row.label || row.x}-${index}`}>
                        <td>{chart.kind === "scatter" ? row.x : row.label}</td>
                        <td>{chart.kind === "scatter" ? row.y : row.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {chart.data.length > 40 && <p className="muted">Showing 40 of {chart.data.length} points. CSV export includes every point.</p>}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

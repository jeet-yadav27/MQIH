import { useRef } from "react";
import InsightChart from "./InsightChart";
import { downloadChartCsv, downloadChartPng } from "../download";

export default function ChartCard({ chart, height = 280 }) {
  const ref = useRef(null);
  const ready = chart.data?.length > 0;
  return (
    <section className="card">
      <header className="card-head">
        <div>
          <h3>{chart.title}</h3>
          {chart.subtitle && <p>{chart.subtitle}</p>}
        </div>
        <div className="card-actions">
          <button type="button" onClick={() => downloadChartPng(ref.current, chart.title)} disabled={!ready}>
            PNG
          </button>
          <button type="button" onClick={() => downloadChartCsv(chart)} disabled={!ready}>
            CSV
          </button>
        </div>
      </header>
      <div className="chart-body" ref={ref}>
        {ready ? (
          <InsightChart chart={chart} height={height} />
        ) : (
          <p className="muted">{chart.message || "No data for this chart."}</p>
        )}
      </div>
    </section>
  );
}

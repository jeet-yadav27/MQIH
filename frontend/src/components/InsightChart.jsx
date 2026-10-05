import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const PALETTE = ["#1f6f6a", "#c45c26", "#1a2332", "#d4a054", "#4c6e8a", "#8c4a3a", "#6b8f71", "#8d6a9f", "#3d5a4c", "#b36b4c"];

function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  const number = Number(value);
  const digits = Math.abs(number) >= 100 ? 0 : 2;
  return number.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function axisTick(angled) {
  return { fill: "#5c564c", fontSize: 12, ...(angled ? {} : {}) };
}

export default function InsightChart({ chart, height = 280 }) {
  const data = chart.data || [];
  const angled = chart.kind !== "pie" && chart.kind !== "scatter" && data.length > 6;

  if (chart.kind === "pie") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="label" innerRadius={58} outerRadius={96} paddingAngle={2} stroke="#fffdf8">
            {data.map((entry, index) => (
              <Cell key={entry.label} fill={PALETTE[index % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value, name) => [formatNumber(value), name]} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chart.kind === "scatter") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="#efe8dc" />
          <XAxis dataKey="x" type="number" name={chart.x_label} tick={axisTick(false)} stroke="#c9bfb0" />
          <YAxis dataKey="y" type="number" name={chart.y_label} tick={axisTick(false)} stroke="#c9bfb0" width={56} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value, name) => [formatNumber(value), name === "y" ? chart.y_label : chart.x_label]}
          />
          <Scatter data={data} fill="#c45c26" />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  const xAxis = (
    <XAxis
      dataKey="short"
      tick={axisTick(angled)}
      stroke="#c9bfb0"
      interval={0}
      angle={angled ? -32 : 0}
      textAnchor={angled ? "end" : "middle"}
      height={angled ? 74 : 32}
    />
  );
  const yAxis = <YAxis tick={axisTick(false)} stroke="#c9bfb0" width={48} />;
  const tooltip = (
    <Tooltip
      formatter={(value) => [formatNumber(value), chart.y_label || "Value"]}
      labelFormatter={(_, payload) => payload?.[0]?.payload?.label || ""}
    />
  );
  const grid = <CartesianGrid stroke="#efe8dc" vertical={false} />;

  if (chart.kind === "line") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          {grid}
          {xAxis}
          {yAxis}
          {tooltip}
          <Line type="monotone" dataKey="value" stroke="#c45c26" strokeWidth={2.5} dot={{ r: 3, fill: "#c45c26" }} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        {grid}
        {xAxis}
        {yAxis}
        {tooltip}
        <Bar dataKey="value" fill="#1f6f6a" radius={[4, 4, 0, 0]} maxBarSize={48} />
      </BarChart>
    </ResponsiveContainer>
  );
}

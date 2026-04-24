import { useState } from "react";
import { Line, Doughnut, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler,
} from "chart.js";
import {
  TrendingUp, TrendingDown, DollarSign, AlertTriangle,
  Download, Wifi, WifiOff, Plus, RefreshCw,
} from "lucide-react";
import { useAccounts, useMonthlyTrend, useSpendingAnalytics, useWebSocket, useTransactions } from "../hooks/useFinance";
import { useAuth } from "../context/AuthContext";
import { exportAPI } from "../services/api";
import toast from "react-hot-toast";

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

const CATEGORY_COLORS = [
  "#38bdf8", "#34d399", "#fb923c", "#f87171",
  "#a78bfa", "#fbbf24", "#60a5fa", "#f472b6", "#94a3b8",
];

export default function Dashboard() {
  const { user } = useAuth();
  const { data: accounts, totalBalance } = useAccounts();
  const { data: trend }    = useMonthlyTrend(6);
  const { data: spending } = useSpendingAnalytics(new Date().getMonth() + 1, new Date().getFullYear());
  const { data: transactions, refetch } = useTransactions({ limit: 10 });
  const [liveAlerts, setLiveAlerts] = useState([]);

  const { connected } = useWebSocket(user?.id, (msg) => {
    if (msg.type === "new_transaction") {
      refetch();
      if (msg.anomaly_alert) {
        setLiveAlerts((a) => [msg, ...a].slice(0, 5));
        toast.error("⚠️ Anomalous transaction detected!", { duration: 5000 });
      }
    }
    if (msg.type === "budget_alert") {
      toast(`💸 Budget alert: ${msg.category} at ${msg.percentage}%`, { icon: "⚠️" });
    }
  });

  const monthlyIncome   = trend.at(-1)?.income   || 0;
  const monthlyExpenses = trend.at(-1)?.expenses  || 0;
  const savingsRate     = monthlyIncome > 0 ? ((monthlyIncome - monthlyExpenses) / monthlyIncome * 100).toFixed(1) : 0;
  const anomalyCount    = transactions.filter((t) => t.is_anomaly).length;

  // ── Chart data ─────────────────────────────────────────────────────────────
  const lineData = {
    labels: trend.map((t) => t.month),
    datasets: [
      {
        label: "Income",
        data: trend.map((t) => t.income),
        borderColor: "#34d399",
        backgroundColor: "rgba(52,211,153,0.08)",
        fill: true, tension: 0.4, pointRadius: 4,
      },
      {
        label: "Expenses",
        data: trend.map((t) => t.expenses),
        borderColor: "#f87171",
        backgroundColor: "rgba(248,113,113,0.08)",
        fill: true, tension: 0.4, pointRadius: 4,
      },
    ],
  };

  const doughnutData = {
    labels: spending.map((s) => s.category),
    datasets: [{
      data: spending.map((s) => s.total),
      backgroundColor: CATEGORY_COLORS,
      borderWidth: 0,
      hoverOffset: 8,
    }],
  };

  const chartOptions = {
    responsive: true,
    plugins: { legend: { labels: { color: "#94a3b8", font: { size: 11 } } } },
    scales: {
      x: { ticks: { color: "#64748b" }, grid: { color: "#1e293b" } },
      y: { ticks: { color: "#64748b" }, grid: { color: "#1e293b" } },
    },
  };

  const handleExport = async (type) => {
    try {
      const res = type === "csv" ? await exportAPI.csv() : await exportAPI.pdf();
      const url = URL.createObjectURL(new Blob([res.data]));
      const a   = document.createElement("a");
      a.href     = url;
      a.download = type === "csv" ? "transactions.csv" : "report.pdf";
      a.click();
      toast.success(`${type.toUpperCase()} exported!`);
    } catch {
      toast.error("Export failed");
    }
  };

  return (
    <div style={{ fontFamily: "'DM Mono', monospace", background: "#020817", minHeight: "100vh", color: "#e2e8f0", padding: "24px" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: 700, color: "#f8fafc", letterSpacing: "-0.5px", margin: 0 }}>
            ⚡ FMWP
          </h1>
          <p style={{ color: "#64748b", margin: "4px 0 0", fontSize: "13px" }}>
            Welcome back, {user?.full_name} · {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "12px", color: connected ? "#34d399" : "#f87171" }}>
            {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
            {connected ? "Live" : "Offline"}
          </span>
          <button onClick={() => handleExport("csv")} style={btnStyle("#1e293b")}>
            <Download size={14} /> CSV
          </button>
          <button onClick={() => handleExport("pdf")} style={btnStyle("#1e293b")}>
            <Download size={14} /> PDF
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" }}>
        {[
          { label: "Total Balance",    value: `$${totalBalance.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, icon: <DollarSign size={18} />,    color: "#38bdf8" },
          { label: "Monthly Income",   value: `$${monthlyIncome.toLocaleString()}`,   icon: <TrendingUp size={18} />,   color: "#34d399" },
          { label: "Monthly Expenses", value: `$${monthlyExpenses.toLocaleString()}`, icon: <TrendingDown size={18} />, color: "#f87171" },
          { label: "Anomalies",        value: anomalyCount,                           icon: <AlertTriangle size={18} />, color: "#fbbf24" },
        ].map((kpi) => (
          <div key={kpi.label} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <p style={{ margin: 0, fontSize: "11px", color: "#64748b", textTransform: "uppercase", letterSpacing: "1px" }}>{kpi.label}</p>
                <p style={{ margin: "8px 0 0", fontSize: "24px", fontWeight: 700, color: kpi.color }}>{kpi.value}</p>
              </div>
              <span style={{ color: kpi.color, opacity: 0.7 }}>{kpi.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "16px", marginBottom: "24px" }}>
        <div style={cardStyle}>
          <h3 style={sectionTitle}>Income vs Expenses Trend</h3>
          <Line data={lineData} options={chartOptions} />
        </div>
        <div style={cardStyle}>
          <h3 style={sectionTitle}>Spending by Category</h3>
          {spending.length > 0 ? (
            <Doughnut data={doughnutData} options={{ responsive: true, plugins: { legend: { position: "bottom", labels: { color: "#94a3b8", font: { size: 10 } } } } }} />
          ) : (
            <p style={{ color: "#475569", textAlign: "center", marginTop: "40px" }}>No data yet</p>
          )}
        </div>
      </div>

      {/* Recent Transactions */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ ...sectionTitle, margin: 0 }}>Recent Transactions</h3>
          <button onClick={refetch} style={btnStyle("#0f172a")}><RefreshCw size={14} /></button>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1e293b" }}>
              {["Date", "Type", "Category", "Description", "Amount", "⚠️"].map((h) => (
                <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "#475569", fontWeight: 500, fontSize: "11px", textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id} style={{ borderBottom: "1px solid #0f172a" }}>
                <td style={tdStyle}>{new Date(tx.created_at).toLocaleDateString()}</td>
                <td style={{ ...tdStyle, color: tx.type === "income" ? "#34d399" : "#f87171", fontWeight: 600 }}>{tx.type}</td>
                <td style={tdStyle}>{tx.category}</td>
                <td style={tdStyle}>{tx.description || tx.merchant || "—"}</td>
                <td style={{ ...tdStyle, fontWeight: 700, color: tx.type === "income" ? "#34d399" : "#f87171" }}>
                  {tx.type === "income" ? "+" : "-"}${tx.amount.toFixed(2)}
                </td>
                <td style={tdStyle}>{tx.is_anomaly ? "⚠️" : ""}</td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr><td colSpan={6} style={{ textAlign: "center", padding: "32px", color: "#475569" }}>No transactions yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const cardStyle = {
  background: "#0f172a",
  border: "1px solid #1e293b",
  borderRadius: "12px",
  padding: "20px",
};

const sectionTitle = {
  margin: "0 0 16px",
  fontSize: "13px",
  fontWeight: 600,
  color: "#94a3b8",
  textTransform: "uppercase",
  letterSpacing: "1px",
};

const tdStyle = { padding: "10px 12px", color: "#cbd5e1" };

const btnStyle = (bg) => ({
  background: bg,
  border: "1px solid #1e293b",
  borderRadius: "8px",
  color: "#94a3b8",
  padding: "6px 12px",
  cursor: "pointer",
  fontSize: "12px",
  display: "flex",
  alignItems: "center",
  gap: "4px",
});

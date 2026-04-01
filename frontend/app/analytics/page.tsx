"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { TrendingUp, Send, Users, Mail, Star } from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_HEX: Record<string, string> = {
  new: "#9ca3af",
  researched: "#3b82f6",
  drafted: "#f59e0b",
  sent: "#10b981",
  replied: "#8b5cf6",
  archived: "#ef4444",
};

function Metric({
  label,
  value,
  icon: Icon,
  sub,
  color = "brand",
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  sub?: string;
  color?: string;
}) {
  const colorMap: Record<string, string> = {
    brand: "bg-brand-50 text-brand-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    yellow: "bg-yellow-50 text-yellow-600",
  };
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={cn("p-2.5 rounded-lg", colorMap[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.getSummary().then((r) => r.data),
  });

  const pieData = data
    ? Object.entries(data.prospects_by_status).map(([name, value]) => ({ name, value }))
    : [];

  const volumeData = data
    ? [
        { period: "Last 7 days", sent: data.emails_sent_last_7_days },
        { period: "Last 30 days", sent: data.emails_sent_last_30_days },
        { period: "All time", sent: data.total_sent },
      ]
    : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500 mt-0.5">Outreach performance at a glance.</p>
      </div>

      {/* Top metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Metric
          label="Prospects"
          value={data?.total_prospects ?? 0}
          icon={Users}
        />
        <Metric
          label="Emails Sent"
          value={data?.total_sent ?? 0}
          icon={Send}
          sub={`${data?.emails_sent_last_7_days ?? 0} this week`}
          color="green"
        />
        <Metric
          label="Reply Rate"
          value={data ? `${(data.reply_rate * 100).toFixed(1)}%` : "—"}
          icon={TrendingUp}
          color="purple"
        />
        <Metric
          label="Avg Rating"
          value={data?.avg_rating ? `${data.avg_rating}/5` : "—"}
          icon={Star}
          color="yellow"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline funnel */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-5">Prospect Pipeline</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={STATUS_HEX[entry.name] ?? "#9ca3af"}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              No data yet
            </div>
          )}
        </div>

        {/* Volume chart */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-5">Email Volume</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={volumeData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="sent" fill="#0b85f0" radius={[4, 4, 0, 0]} name="Sent" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status breakdown table */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="font-semibold text-gray-900 mb-4">Status Breakdown</h2>
          <div className="grid grid-cols-3 gap-4">
            {data &&
              Object.entries(data.prospects_by_status).map(([status, count]) => (
                <div
                  key={status}
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-50"
                >
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: STATUS_HEX[status] ?? "#9ca3af" }}
                  />
                  <div>
                    <p className="text-xs text-gray-500 capitalize">{status}</p>
                    <p className="text-lg font-bold text-gray-900">{count}</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

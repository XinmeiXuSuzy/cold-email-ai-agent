"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi, prospectsApi } from "@/lib/api";
import { Users, Mail, Send, TrendingUp, Clock, CheckCircle } from "lucide-react";
import { cn, formatRelative, STATUS_COLORS } from "@/lib/utils";
import Link from "next/link";

function StatCard({
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
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={cn("p-2.5 rounded-lg", colorMap[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => analyticsApi.getSummary().then((r) => r.data),
  });

  const { data: recentProspects } = useQuery({
    queryKey: ["prospects", "recent"],
    queryFn: () => prospectsApi.list({ page: 1, page_size: 5 }).then((r) => r.data),
  });

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1 text-sm">Your cold email outreach at a glance.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Prospects"
          value={analytics?.total_prospects ?? "—"}
          icon={Users}
          sub={`${analytics?.prospects_by_status?.new ?? 0} new`}
        />
        <StatCard
          label="Emails Sent"
          value={analytics?.total_sent ?? "—"}
          icon={Send}
          sub={`${analytics?.emails_sent_last_7_days ?? 0} this week`}
          color="green"
        />
        <StatCard
          label="Reply Rate"
          value={analytics ? `${(analytics.reply_rate * 100).toFixed(1)}%` : "—"}
          icon={TrendingUp}
          color="purple"
        />
        <StatCard
          label="Drafts"
          value={analytics?.total_drafts ?? "—"}
          icon={Mail}
          color="yellow"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Pipeline</h2>
          {analytics?.prospects_by_status ? (
            <div className="space-y-3">
              {Object.entries(analytics.prospects_by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={cn("badge", STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700")}>
                      {status}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No data yet.</p>
          )}
        </div>

        {/* Recent Prospects */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Recent Prospects</h2>
            <Link href="/prospects" className="text-xs text-brand-600 hover:underline">
              View all →
            </Link>
          </div>
          {recentProspects?.items.length ? (
            <div className="space-y-3">
              {recentProspects.items.map((p) => (
                <Link
                  key={p.id}
                  href={`/prospects/${p.id}`}
                  className="flex items-center gap-3 group"
                >
                  <div className="w-8 h-8 bg-brand-100 rounded-full flex items-center justify-center text-brand-700 font-semibold text-xs flex-shrink-0">
                    {p.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 group-hover:text-brand-600 truncate">
                      {p.name}
                    </p>
                    <p className="text-xs text-gray-400 truncate">
                      {p.role} · {p.company}
                    </p>
                  </div>
                  <span className={cn("badge flex-shrink-0", STATUS_COLORS[p.outreach_status])}>
                    {p.outreach_status}
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Users className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-400">No prospects yet.</p>
              <Link href="/prospects" className="text-xs text-brand-600 hover:underline mt-1 inline-block">
                Add your first prospect →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

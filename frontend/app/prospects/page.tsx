"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { prospectsApi, type Prospect } from "@/lib/api";
import { cn, formatRelative, STATUS_COLORS } from "@/lib/utils";
import { Plus, Search, Upload, Users, ExternalLink } from "lucide-react";
import Link from "next/link";
import { ProspectForm } from "@/components/prospects/ProspectForm";
import { CsvUpload } from "@/components/prospects/CsvUpload";

const STATUSES = ["", "new", "researched", "drafted", "sent", "replied", "archived"];

export default function ProspectsPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["prospects", page, search, status],
    queryFn: () =>
      prospectsApi
        .list({ page, page_size: 20, search: search || undefined, status: status || undefined })
        .then((r) => r.data),
  });

  function refresh() {
    qc.invalidateQueries({ queryKey: ["prospects"] });
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prospects</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {data?.total ?? 0} total prospects
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => { setShowUpload(true); setShowForm(false); }}
            className="btn-secondary"
          >
            <Upload className="w-4 h-4" />
            Import CSV
          </button>
          <button
            onClick={() => { setShowForm(true); setShowUpload(false); }}
            className="btn-primary"
          >
            <Plus className="w-4 h-4" />
            Add Prospect
          </button>
        </div>
      </div>

      {/* Inline form / upload */}
      {showForm && (
        <div className="card p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">New Prospect</h2>
          <ProspectForm
            onSuccess={() => { setShowForm(false); refresh(); }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {showUpload && (
        <div className="card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Import from CSV</h2>
            <button onClick={() => setShowUpload(false)} className="text-gray-400 hover:text-gray-600 text-sm">
              Close
            </button>
          </div>
          <CsvUpload onSuccess={() => { setShowUpload(false); refresh(); }} />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Search name, email, company…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <select
          className="input w-40"
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
        >
          <option value="">All statuses</option>
          {STATUSES.filter(Boolean).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : data?.items.length === 0 ? (
          <div className="text-center py-16">
            <Users className="w-10 h-10 text-gray-200 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No prospects found</p>
            <p className="text-sm text-gray-400 mt-1">Add one manually or import a CSV.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Company</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Added</th>
                <th className="w-12" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data?.items.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 group">
                  <td className="px-4 py-3">
                    <Link href={`/prospects/${p.id}`} className="font-medium text-gray-900 hover:text-brand-600">
                      {p.name}
                    </Link>
                    <p className="text-xs text-gray-400">{p.email}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    <p>{p.company}</p>
                    <p className="text-xs text-gray-400">{p.role}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("badge", STATUS_COLORS[p.outreach_status] ?? "bg-gray-100 text-gray-700")}>
                      {p.outreach_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{formatRelative(p.created_at)}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/prospects/${p.id}`}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-gray-600"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * data.page_size + 1}–
            {Math.min(page * data.page_size, data.total)} of {data.total}
          </p>
          <div className="flex gap-2">
            <button
              className="btn-secondary"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <button
              className="btn-secondary"
              disabled={page * data.page_size >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

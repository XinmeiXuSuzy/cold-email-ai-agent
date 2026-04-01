"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { emailsApi, prospectsApi } from "@/lib/api";
import { cn, formatRelative, STATUS_COLORS } from "@/lib/utils";
import { Mail, Send } from "lucide-react";
import Link from "next/link";

const DRAFT_STATUSES = ["", "draft", "approved", "sent", "archived"];

export default function DraftsPage() {
  const [status, setStatus] = useState("draft");

  const { data: drafts, isLoading } = useQuery({
    queryKey: ["all-drafts", status],
    queryFn: () =>
      emailsApi.list({ status: status || undefined }).then((r) => r.data),
  });

  // Fetch prospect names for display
  const { data: prospects } = useQuery({
    queryKey: ["prospects-map"],
    queryFn: async () => {
      const res = await prospectsApi.list({ page_size: 100 });
      return Object.fromEntries(res.data.items.map((p) => [p.id, p]));
    },
  });

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Email Drafts</h1>
        <p className="text-sm text-gray-500 mt-0.5">Review and send generated emails.</p>
      </div>

      {/* Status filter */}
      <div className="flex gap-2 mb-5">
        {DRAFT_STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              status === s
                ? "bg-brand-600 text-white"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            )}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : drafts?.length === 0 ? (
        <div className="card text-center py-16">
          <Mail className="w-10 h-10 text-gray-200 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No drafts found</p>
          <p className="text-sm text-gray-400 mt-1">
            Go to a prospect page and generate an email.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {drafts?.map((draft) => {
            const prospect = prospects?.[draft.prospect_id];
            return (
              <div key={draft.id} className="card p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn("badge", STATUS_COLORS[draft.status])}>
                        {draft.status}
                      </span>
                      <span className="text-xs text-gray-400">{draft.tone}</span>
                      {draft.is_edited && (
                        <span className="text-xs text-gray-300">edited</span>
                      )}
                    </div>
                    <p className="font-medium text-gray-900 truncate">{draft.subject}</p>
                    {prospect && (
                      <p className="text-sm text-gray-500 mt-0.5">
                        To:{" "}
                        <Link
                          href={`/prospects/${prospect.id}`}
                          className="text-brand-600 hover:underline"
                        >
                          {prospect.name}
                        </Link>{" "}
                        · {prospect.company}
                      </p>
                    )}
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                      {draft.opening_line}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <span className="text-xs text-gray-400">
                      {formatRelative(draft.created_at)}
                    </span>
                    {prospect && (
                      <Link
                        href={`/prospects/${prospect.id}`}
                        className="btn-secondary text-xs px-3 py-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        Review & Send
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

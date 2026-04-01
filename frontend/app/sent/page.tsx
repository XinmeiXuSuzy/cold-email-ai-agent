"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { emailsApi, prospectsApi, type SentEmail } from "@/lib/api";
import { cn, formatDate, formatRelative } from "@/lib/utils";
import { Send, MessageSquare, ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

const REPLY_COLORS: Record<string, string> = {
  none: "bg-gray-100 text-gray-600",
  replied: "bg-blue-100 text-blue-700",
  positive: "bg-green-100 text-green-700",
  negative: "bg-red-100 text-red-700",
};

function SentEmailRow({ email }: { email: SentEmail }) {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState(false);

  const { data: prospects } = useQuery({
    queryKey: ["prospects-map"],
    queryFn: async () => {
      const res = await prospectsApi.list({ page_size: 100 });
      return Object.fromEntries(res.data.items.map((p) => [p.id, p]));
    },
  });
  const prospect = prospects?.[email.prospect_id];

  async function updateReply(status: string) {
    setUpdating(true);
    try {
      await emailsApi.updateReplyStatus(email.id, status);
      qc.invalidateQueries({ queryKey: ["sent-emails"] });
      toast.success("Reply status updated");
    } catch {
      toast.error("Update failed");
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div className="card overflow-hidden">
      <div
        className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={cn("badge", REPLY_COLORS[email.reply_status])}>
              {email.reply_status === "none" ? "awaiting reply" : email.reply_status}
            </span>
            {email.follow_up_scheduled_at && !email.follow_up_sent && (
              <span className="badge bg-yellow-100 text-yellow-700">follow-up scheduled</span>
            )}
          </div>
          <p className="font-medium text-gray-900 truncate">{email.subject}</p>
          {prospect && (
            <p className="text-sm text-gray-500">
              <Link href={`/prospects/${prospect.id}`} className="text-brand-600 hover:underline" onClick={(e) => e.stopPropagation()}>
                {prospect.name}
              </Link>
              {" · "}{prospect.company}
            </p>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-xs text-gray-400">{formatDate(email.sent_at)}</p>
          <p className="text-xs text-gray-300">{formatRelative(email.sent_at)}</p>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
      </div>

      {expanded && (
        <div className="px-5 pb-5 border-t border-gray-100 space-y-4 pt-4">
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 font-mono whitespace-pre-wrap leading-relaxed">
            {email.body}
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 mb-2">Mark reply status:</p>
            <div className="flex gap-2">
              {["none", "replied", "positive", "negative"].map((s) => (
                <button
                  key={s}
                  disabled={updating || email.reply_status === s}
                  onClick={() => updateReply(s)}
                  className={cn(
                    "px-2.5 py-1 rounded-lg text-xs font-medium transition-colors border",
                    email.reply_status === s
                      ? "border-transparent " + REPLY_COLORS[s]
                      : "border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40"
                  )}
                >
                  {s === "none" ? "No reply" : s}
                </button>
              ))}
            </div>
          </div>

          {email.follow_up_scheduled_at && (
            <p className="text-xs text-gray-400">
              Follow-up scheduled: {formatDate(email.follow_up_scheduled_at)}
              {email.follow_up_sent && " · sent"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function SentPage() {
  const { data: sentEmails, isLoading } = useQuery({
    queryKey: ["sent-emails"],
    queryFn: () => emailsApi.listSent().then((r) => r.data),
  });

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sent Emails</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {sentEmails?.length ?? 0} emails sent
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : sentEmails?.length === 0 ? (
        <div className="card text-center py-16">
          <Send className="w-10 h-10 text-gray-200 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No emails sent yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Generate and send emails from the Prospects page.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {sentEmails?.map((email) => (
            <SentEmailRow key={email.id} email={email} />
          ))}
        </div>
      )}
    </div>
  );
}

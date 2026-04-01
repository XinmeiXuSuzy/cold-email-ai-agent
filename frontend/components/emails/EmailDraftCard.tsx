"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { emailsApi, type EmailDraft, type Prospect } from "@/lib/api";
import { cn, formatRelative, STATUS_COLORS } from "@/lib/utils";
import { Send, ThumbsUp, ChevronDown, ChevronUp, Pencil, Check } from "lucide-react";
import toast from "react-hot-toast";

interface EmailDraftCardProps {
  draft: EmailDraft;
  prospect: Prospect;
}

export function EmailDraftCard({ draft, prospect }: EmailDraftCardProps) {
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState(true);
  const [editing, setEditing] = useState(false);
  const [sending, setSending] = useState(false);
  const [followUpDays, setFollowUpDays] = useState<number | "">("");

  const [form, setForm] = useState({
    subject: draft.subject,
    opening_line: draft.opening_line,
    body: draft.body,
    cta: draft.cta,
    follow_up: draft.follow_up ?? "",
  });

  async function handleSave() {
    try {
      await emailsApi.update(draft.id, form);
      qc.invalidateQueries({ queryKey: ["drafts"] });
      setEditing(false);
      toast.success("Draft saved");
    } catch {
      toast.error("Save failed");
    }
  }

  async function handleSend() {
    setSending(true);
    try {
      await emailsApi.send({
        draft_id: draft.id,
        schedule_follow_up_days: followUpDays ? Number(followUpDays) : undefined,
      });
      qc.invalidateQueries({ queryKey: ["drafts"] });
      qc.invalidateQueries({ queryKey: ["prospect"] });
      toast.success(`Email sent to ${prospect.email}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Send failed";
      toast.error(msg);
    } finally {
      setSending(false);
    }
  }

  const isSent = draft.status === "sent";

  return (
    <div className={cn("card overflow-hidden", isSent && "opacity-75")}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className={cn("badge flex-shrink-0", STATUS_COLORS[draft.status] ?? "bg-gray-100")}>
            {draft.status}
          </span>
          <p className="text-sm font-medium text-gray-900 truncate">{draft.subject}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          <span className="text-xs text-gray-400">{formatRelative(draft.created_at)}</span>
          <span className="text-xs text-gray-300">{draft.tone}</span>
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </div>

      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-gray-100">
          {editing ? (
            <div className="space-y-3 pt-4">
              <div>
                <label className="label text-xs">Subject</label>
                <input
                  className="input text-sm"
                  value={form.subject}
                  onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
                />
              </div>
              <div>
                <label className="label text-xs">Opening line</label>
                <textarea
                  className="input text-sm min-h-[60px] resize-none"
                  value={form.opening_line}
                  onChange={(e) => setForm((f) => ({ ...f, opening_line: e.target.value }))}
                />
              </div>
              <div>
                <label className="label text-xs">Body</label>
                <textarea
                  className="input text-sm min-h-[120px] resize-y"
                  value={form.body}
                  onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
                />
              </div>
              <div>
                <label className="label text-xs">CTA</label>
                <textarea
                  className="input text-sm min-h-[60px] resize-none"
                  value={form.cta}
                  onChange={(e) => setForm((f) => ({ ...f, cta: e.target.value }))}
                />
              </div>
              {form.follow_up !== undefined && (
                <div>
                  <label className="label text-xs">Follow-up</label>
                  <textarea
                    className="input text-sm min-h-[80px] resize-none"
                    value={form.follow_up}
                    onChange={(e) => setForm((f) => ({ ...f, follow_up: e.target.value }))}
                  />
                </div>
              )}
              <div className="flex gap-2">
                <button onClick={handleSave} className="btn-primary text-xs px-3 py-1.5">
                  <Check className="w-3.5 h-3.5" /> Save
                </button>
                <button onClick={() => setEditing(false)} className="btn-secondary text-xs px-3 py-1.5">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="pt-4 space-y-3">
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 space-y-3 font-mono leading-relaxed whitespace-pre-wrap">
                <p className="not-italic font-semibold text-gray-900">Subject: {draft.subject}</p>
                <p>{draft.opening_line}</p>
                <p>{draft.body}</p>
                <p className="font-medium">{draft.cta}</p>
              </div>

              {draft.follow_up && (
                <details className="text-sm">
                  <summary className="cursor-pointer text-gray-400 hover:text-gray-600 text-xs">
                    View follow-up version
                  </summary>
                  <div className="mt-2 bg-gray-50 rounded-lg p-4 text-gray-600 whitespace-pre-wrap font-mono text-xs leading-relaxed">
                    {draft.follow_up}
                  </div>
                </details>
              )}
            </div>
          )}

          {/* Actions */}
          {!isSent && !editing && (
            <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
              <button onClick={() => setEditing(true)} className="btn-secondary text-xs px-3 py-1.5">
                <Pencil className="w-3.5 h-3.5" /> Edit
              </button>
              <div className="flex-1" />
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={1}
                  max={30}
                  placeholder="Follow-up days"
                  className="input text-xs w-32"
                  value={followUpDays}
                  onChange={(e) => setFollowUpDays(e.target.value === "" ? "" : Number(e.target.value))}
                />
                <button
                  onClick={handleSend}
                  disabled={sending}
                  className="btn-primary text-xs px-3 py-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  {sending ? "Sending…" : "Send"}
                </button>
              </div>
            </div>
          )}

          {isSent && (
            <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
              <ThumbsUp className="w-3.5 h-3.5 text-green-500" />
              <span className="text-xs text-gray-400">Sent {formatRelative(draft.updated_at)}</span>
              {draft.is_edited && <span className="text-xs text-gray-300">· edited</span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

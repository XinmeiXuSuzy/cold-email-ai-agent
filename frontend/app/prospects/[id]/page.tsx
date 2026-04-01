"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { prospectsApi, emailsApi, type Prospect } from "@/lib/api";
import { cn, formatDate, formatRelative, STATUS_COLORS, TONE_OPTIONS } from "@/lib/utils";
import {
  ArrowLeft,
  FlaskConical,
  Sparkles,
  Pencil,
  Trash2,
  Globe,
  Linkedin,
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { ProspectForm } from "@/components/prospects/ProspectForm";
import { EmailDraftCard } from "@/components/emails/EmailDraftCard";

export default function ProspectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();

  const [editing, setEditing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [researching, setResearching] = useState(false);
  const [tone, setTone] = useState("concise");
  const [extraContext, setExtraContext] = useState("");

  const { data: prospect, isLoading } = useQuery({
    queryKey: ["prospect", id],
    queryFn: () => prospectsApi.get(id).then((r) => r.data),
  });

  const { data: research } = useQuery({
    queryKey: ["research", id],
    queryFn: () => prospectsApi.getResearch(id).then((r) => r.data),
    retry: false,
  });

  const { data: drafts } = useQuery({
    queryKey: ["drafts", id],
    queryFn: () => emailsApi.list({ prospect_id: id }).then((r) => r.data),
  });

  async function handleResearch() {
    setResearching(true);
    try {
      await prospectsApi.research(id);
      qc.invalidateQueries({ queryKey: ["research", id] });
      qc.invalidateQueries({ queryKey: ["prospect", id] });
      toast.success("Research complete");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Research failed";
      toast.error(msg, { duration: 6000 });
    } finally {
      setResearching(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
      await emailsApi.generate({
        prospect_id: id,
        tone,
        additional_context: extraContext || undefined,
      });
      qc.invalidateQueries({ queryKey: ["drafts", id] });
      toast.success("Draft generated");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Generation failed";
      toast.error(msg, { duration: 6000 });
    } finally {
      setGenerating(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this prospect? This cannot be undone.")) return;
    try {
      await prospectsApi.delete(id);
      toast.success("Prospect deleted");
      router.push("/prospects");
    } catch {
      toast.error("Delete failed");
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!prospect) return <div className="p-8 text-gray-400">Prospect not found.</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Back */}
      <Link href="/prospects" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6">
        <ArrowLeft className="w-4 h-4" />
        Prospects
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center text-brand-700 font-bold text-lg">
            {prospect.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{prospect.name}</h1>
            <p className="text-gray-500 text-sm">
              {prospect.role} {prospect.company && `· ${prospect.company}`}
            </p>
            <p className="text-gray-400 text-xs mt-0.5">{prospect.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn("badge", STATUS_COLORS[prospect.outreach_status])}>
            {prospect.outreach_status}
          </span>
          <button onClick={() => setEditing((e) => !e)} className="btn-secondary">
            <Pencil className="w-4 h-4" />
            Edit
          </button>
          <button onClick={handleDelete} className="btn-danger">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Edit form */}
      {editing && (
        <div className="card p-6 mb-6">
          <h2 className="font-semibold mb-4">Edit Prospect</h2>
          <ProspectForm
            prospect={prospect}
            onSuccess={(p) => {
              setEditing(false);
              qc.setQueryData(["prospect", id], p);
            }}
            onCancel={() => setEditing(false)}
          />
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Left: Details + Research */}
        <div className="col-span-1 space-y-4">
          {/* Details */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-900 mb-3 text-sm">Details</h2>
            <dl className="space-y-2 text-sm">
              {prospect.industry && (
                <div>
                  <dt className="text-gray-400 text-xs">Industry</dt>
                  <dd className="text-gray-700">{prospect.industry}</dd>
                </div>
              )}
              {prospect.website && (
                <div>
                  <dt className="text-gray-400 text-xs">Website</dt>
                  <dd>
                    <a href={prospect.website} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      {prospect.website.replace(/^https?:\/\//, "")}
                    </a>
                  </dd>
                </div>
              )}
              {prospect.linkedin_url && (
                <div>
                  <dt className="text-gray-400 text-xs">LinkedIn</dt>
                  <dd>
                    <a href={prospect.linkedin_url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline flex items-center gap-1">
                      <Linkedin className="w-3 h-3" />
                      Profile
                    </a>
                  </dd>
                </div>
              )}
              {prospect.notes && (
                <div>
                  <dt className="text-gray-400 text-xs">Notes</dt>
                  <dd className="text-gray-700 whitespace-pre-wrap">{prospect.notes}</dd>
                </div>
              )}
              <div>
                <dt className="text-gray-400 text-xs">Added</dt>
                <dd className="text-gray-500">{formatDate(prospect.created_at)}</dd>
              </div>
            </dl>
          </div>

          {/* Research */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-gray-900 text-sm">Research</h2>
              <button
                onClick={handleResearch}
                disabled={researching}
                className="btn-secondary text-xs px-2 py-1"
              >
                <FlaskConical className="w-3 h-3" />
                {researching ? "Running…" : research ? "Re-run" : "Run"}
              </button>
            </div>
            {research ? (
              <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                {research.content}
                <p className="text-xs text-gray-400 mt-2">{formatRelative(research.created_at)}</p>
              </div>
            ) : (
              <p className="text-sm text-gray-400">
                No research yet. Run research to enrich this prospect before generating an email.
              </p>
            )}
          </div>

          {/* Generate */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-900 text-sm mb-3">Generate Email</h2>
            <div className="space-y-3">
              <div>
                <label className="label text-xs">Tone</label>
                <select className="input text-sm" value={tone} onChange={(e) => setTone(e.target.value)}>
                  {TONE_OPTIONS.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label text-xs">Extra context (optional)</label>
                <textarea
                  className="input text-sm min-h-[64px] resize-none"
                  placeholder="What to emphasize, specific offer, etc."
                  value={extraContext}
                  onChange={(e) => setExtraContext(e.target.value)}
                />
              </div>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="btn-primary w-full justify-center"
              >
                <Sparkles className="w-4 h-4" />
                {generating ? "Generating…" : "Generate Draft"}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Drafts */}
        <div className="col-span-2">
          <h2 className="font-semibold text-gray-900 mb-3">
            Email Drafts{" "}
            {drafts?.length ? (
              <span className="text-gray-400 font-normal text-sm">({drafts.length})</span>
            ) : null}
          </h2>
          {drafts?.length === 0 && (
            <div className="card p-8 text-center text-gray-400">
              <Sparkles className="w-8 h-8 mx-auto mb-2 text-gray-200" />
              <p className="text-sm">No drafts yet. Generate one on the left.</p>
            </div>
          )}
          <div className="space-y-4">
            {drafts?.map((draft) => (
              <EmailDraftCard key={draft.id} draft={draft} prospect={prospect} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

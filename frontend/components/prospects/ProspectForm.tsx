"use client";

import { useState } from "react";
import { prospectsApi, type Prospect } from "@/lib/api";
import toast from "react-hot-toast";

interface ProspectFormProps {
  prospect?: Prospect;
  onSuccess: (p: Prospect) => void;
  onCancel: () => void;
}

export function ProspectForm({ prospect, onSuccess, onCancel }: ProspectFormProps) {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: prospect?.name ?? "",
    email: prospect?.email ?? "",
    role: prospect?.role ?? "",
    company: prospect?.company ?? "",
    industry: prospect?.industry ?? "",
    website: prospect?.website ?? "",
    linkedin_url: prospect?.linkedin_url ?? "",
    notes: prospect?.notes ?? "",
  });

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = prospect
        ? await prospectsApi.update(prospect.id, form)
        : await prospectsApi.create(form);
      onSuccess(res.data);
      toast.success(prospect ? "Prospect updated" : "Prospect created");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Something went wrong";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Name *</label>
          <input className="input" required value={form.name} onChange={set("name")} placeholder="Jane Smith" />
        </div>
        <div>
          <label className="label">Email *</label>
          <input className="input" type="email" required value={form.email} onChange={set("email")} placeholder="jane@example.com" />
        </div>
        <div>
          <label className="label">Role</label>
          <input className="input" value={form.role} onChange={set("role")} placeholder="VP of Engineering" />
        </div>
        <div>
          <label className="label">Company</label>
          <input className="input" value={form.company} onChange={set("company")} placeholder="Acme Corp" />
        </div>
        <div>
          <label className="label">Industry</label>
          <input className="input" value={form.industry} onChange={set("industry")} placeholder="SaaS" />
        </div>
        <div>
          <label className="label">Website</label>
          <input className="input" value={form.website} onChange={set("website")} placeholder="https://acme.com" />
        </div>
        <div className="col-span-2">
          <label className="label">LinkedIn URL</label>
          <input className="input" value={form.linkedin_url} onChange={set("linkedin_url")} placeholder="https://linkedin.com/in/..." />
        </div>
        <div className="col-span-2">
          <label className="label">Notes</label>
          <textarea
            className="input min-h-[80px] resize-none"
            value={form.notes}
            onChange={set("notes")}
            placeholder="Any additional context about this prospect..."
          />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Saving…" : prospect ? "Update" : "Create Prospect"}
        </button>
      </div>
    </form>
  );
}

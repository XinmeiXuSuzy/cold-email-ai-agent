"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle } from "lucide-react";
import { prospectsApi } from "@/lib/api";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

interface CsvUploadProps {
  onSuccess: () => void;
}

export function CsvUpload({ onSuccess }: CsvUploadProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ created: number; skipped: number } | null>(null);

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0];
      if (!file) return;
      setLoading(true);
      setResult(null);
      try {
        const res = await prospectsApi.uploadCsv(file);
        setResult(res.data);
        toast.success(`Imported ${res.data.created} prospects`);
        onSuccess();
      } catch (err: unknown) {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Upload failed";
        toast.error(msg);
      } finally {
        setLoading(false);
      }
    },
    [onSuccess]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
    disabled: loading,
  });

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors",
          isDragActive ? "border-brand-400 bg-brand-50" : "border-gray-200 hover:border-gray-300 bg-gray-50"
        )}
      >
        <input {...getInputProps()} />
        {loading ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-500">Importing…</p>
          </div>
        ) : result ? (
          <div className="flex flex-col items-center gap-2 text-green-600">
            <CheckCircle className="w-8 h-8" />
            <p className="text-sm font-medium">{result.created} created, {result.skipped} skipped</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload className="w-8 h-8 text-gray-400" />
            <p className="text-sm font-medium text-gray-700">
              {isDragActive ? "Drop the CSV here" : "Drag & drop a CSV or click to browse"}
            </p>
            <p className="text-xs text-gray-400">Required columns: name, email</p>
          </div>
        )}
      </div>

      <div className="text-xs text-gray-400 flex items-start gap-2">
        <FileText className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
        <span>
          Optional columns: role, company, industry, website, linkedin_url, notes
        </span>
      </div>
    </div>
  );
}

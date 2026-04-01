import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), "MMM d, yyyy");
}

export function formatRelative(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export const STATUS_COLORS: Record<string, string> = {
  new: "bg-gray-100 text-gray-700",
  researched: "bg-blue-100 text-blue-700",
  drafted: "bg-yellow-100 text-yellow-700",
  sent: "bg-green-100 text-green-700",
  replied: "bg-purple-100 text-purple-700",
  archived: "bg-red-100 text-red-700",
  draft: "bg-yellow-100 text-yellow-700",
  approved: "bg-blue-100 text-blue-700",
};

export const TONE_OPTIONS = [
  { value: "concise", label: "Concise" },
  { value: "warm", label: "Warm" },
  { value: "direct", label: "Direct" },
  { value: "consultative", label: "Consultative" },
  { value: "casual", label: "Casual" },
];

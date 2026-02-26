"use client";
import { TagBrief } from "@/types";

export default function TagBadge({ tag, onRemove }: { tag: TagBrief; onRemove?: () => void }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: tag.color || "#6b7280" }}
    >
      {tag.name}
      {onRemove && (
        <button onClick={onRemove} className="ml-0.5 hover:opacity-75">&times;</button>
      )}
    </span>
  );
}

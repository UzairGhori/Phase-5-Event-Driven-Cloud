"use client";
import { Tag } from "@/types";

export default function TagList({
  tags,
  onDelete,
}: {
  tags: Tag[];
  onDelete: (id: string) => void;
}) {
  if (!tags.length) return <p className="text-gray-500 text-sm">No tags yet.</p>;

  return (
    <ul className="space-y-2">
      {tags.map((t) => (
        <li key={t.id} className="flex items-center justify-between p-2 bg-white rounded shadow-sm">
          <div className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded-full inline-block"
              style={{ backgroundColor: t.color || "#6b7280" }}
            />
            <span className="font-medium">{t.name}</span>
            <span className="text-xs text-gray-400">({t.task_count} tasks)</span>
          </div>
          <button onClick={() => onDelete(t.id)} className="text-red-500 text-xs hover:underline">
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}

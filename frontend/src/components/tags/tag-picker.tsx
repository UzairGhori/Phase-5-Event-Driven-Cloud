"use client";
import { Tag } from "@/types";

export default function TagPicker({
  tags,
  selected,
  onChange,
}: {
  tags: Tag[];
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else if (selected.length < 10) {
      onChange([...selected, id]);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => toggle(t.id)}
          className={`px-2 py-1 rounded-full text-xs border ${
            selected.includes(t.id) ? "ring-2 ring-blue-500 border-blue-500" : "border-gray-300"
          }`}
          style={{ backgroundColor: selected.includes(t.id) ? (t.color || "#6b7280") + "30" : undefined }}
        >
          <span className="w-2 h-2 rounded-full inline-block mr-1" style={{ backgroundColor: t.color || "#6b7280" }} />
          {t.name}
        </button>
      ))}
      {tags.length === 0 && <span className="text-xs text-gray-400">No tags available</span>}
    </div>
  );
}

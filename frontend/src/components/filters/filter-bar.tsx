"use client";
import { Tag } from "@/types";

export interface Filters {
  status: string;
  priority: string;
  tag: string;
  overdue: string;
}

export default function FilterBar({
  filters,
  tags,
  onChange,
}: {
  filters: Filters;
  tags: Tag[];
  onChange: (f: Filters) => void;
}) {
  const set = (key: keyof Filters, val: string) => onChange({ ...filters, [key]: val });

  return (
    <div className="flex flex-wrap gap-3 items-center">
      <select className="border rounded px-2 py-1 text-sm" value={filters.status} onChange={(e) => set("status", e.target.value)}>
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="in_progress">In Progress</option>
        <option value="completed">Completed</option>
      </select>
      <select className="border rounded px-2 py-1 text-sm" value={filters.priority} onChange={(e) => set("priority", e.target.value)}>
        <option value="">All Priority</option>
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
        <option value="critical">Critical</option>
      </select>
      <select className="border rounded px-2 py-1 text-sm" value={filters.tag} onChange={(e) => set("tag", e.target.value)}>
        <option value="">All Tags</option>
        {tags.map((t) => (
          <option key={t.id} value={t.slug}>{t.name}</option>
        ))}
      </select>
      <label className="flex items-center gap-1 text-sm">
        <input type="checkbox" checked={filters.overdue === "true"} onChange={(e) => set("overdue", e.target.checked ? "true" : "")} />
        Overdue only
      </label>
    </div>
  );
}

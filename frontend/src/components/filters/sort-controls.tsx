"use client";

export default function SortControls({
  sortBy,
  sortOrder,
  onSortByChange,
  onSortOrderChange,
}: {
  sortBy: string;
  sortOrder: string;
  onSortByChange: (v: string) => void;
  onSortOrderChange: (v: string) => void;
}) {
  return (
    <div className="flex gap-2 items-center">
      <select className="border rounded px-2 py-1 text-sm" value={sortBy} onChange={(e) => onSortByChange(e.target.value)}>
        <option value="created_at">Created</option>
        <option value="due_date">Due Date</option>
        <option value="priority">Priority</option>
        <option value="title">Title</option>
      </select>
      <button
        className="border rounded px-2 py-1 text-sm"
        onClick={() => onSortOrderChange(sortOrder === "asc" ? "desc" : "asc")}
      >
        {sortOrder === "asc" ? "↑ Asc" : "↓ Desc"}
      </button>
    </div>
  );
}

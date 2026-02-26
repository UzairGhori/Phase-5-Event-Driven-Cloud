"use client";

export default function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex gap-1 items-center justify-center mt-4">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-40">
        Prev
      </button>
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`px-3 py-1 border rounded text-sm ${p === page ? "bg-blue-600 text-white" : ""}`}
        >
          {p}
        </button>
      ))}
      <button disabled={page >= totalPages} onClick={() => onChange(page + 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-40">
        Next
      </button>
    </div>
  );
}

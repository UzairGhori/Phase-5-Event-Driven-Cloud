"use client";
import { useState } from "react";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899"];

export default function TagCreateDialog({
  open,
  onClose,
  onCreate,
}: {
  open: boolean;
  onClose: () => void;
  onCreate: (name: string, color: string) => void;
}) {
  const [name, setName] = useState("");
  const [color, setColor] = useState(COLORS[0]);

  if (!open) return null;

  const handleSubmit = () => {
    if (!name.trim()) return;
    onCreate(name.trim(), color);
    setName("");
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-80 shadow-xl">
        <h3 className="text-lg font-semibold mb-4">Create Tag</h3>
        <input
          className="w-full border rounded px-3 py-2 mb-3"
          placeholder="Tag name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={50}
        />
        <div className="flex gap-2 mb-4">
          {COLORS.map((c) => (
            <button
              key={c}
              className={`w-7 h-7 rounded-full border-2 ${color === c ? "border-gray-900" : "border-transparent"}`}
              style={{ backgroundColor: c }}
              onClick={() => setColor(c)}
            />
          ))}
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
          <button onClick={handleSubmit} className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
            Create
          </button>
        </div>
      </div>
    </div>
  );
}

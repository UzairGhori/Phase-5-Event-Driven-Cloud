"use client";
import { useEffect, useRef, useState } from "react";

export default function SearchInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [local, setLocal] = useState(value);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => setLocal(value), [value]);

  const handleChange = (v: string) => {
    setLocal(v);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => onChange(v), 300);
  };

  return (
    <input
      className="border rounded px-3 py-2 w-full"
      placeholder="Search tasks..."
      value={local}
      onChange={(e) => handleChange(e.target.value)}
    />
  );
}

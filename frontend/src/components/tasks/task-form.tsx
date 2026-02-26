"use client";
import { useState } from "react";
import { Tag, TaskCreateInput } from "@/types";
import TagPicker from "@/components/tags/tag-picker";

export default function TaskForm({
  tags,
  onSubmit,
  onCancel,
}: {
  tags: Tag[];
  onSubmit: (data: TaskCreateInput) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [dueDate, setDueDate] = useState("");
  const [reminderAt, setReminderAt] = useState("");
  const [recurrencePattern, setRecurrencePattern] = useState("");
  const [recurrenceInterval, setRecurrenceInterval] = useState(1);
  const [recurrenceEndsAt, setRecurrenceEndsAt] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const data: TaskCreateInput = { title: title.trim(), priority };
    if (description) data.description = description;
    if (dueDate) data.due_date = new Date(dueDate).toISOString();
    if (reminderAt) data.reminder_at = new Date(reminderAt).toISOString();
    if (recurrencePattern) {
      data.recurrence_pattern = recurrencePattern;
      data.recurrence_interval = recurrenceInterval;
      if (recurrenceEndsAt) data.recurrence_ends_at = new Date(recurrenceEndsAt).toISOString();
    }
    if (selectedTags.length) data.tag_ids = selectedTags;
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-4 rounded-lg shadow space-y-3">
      <input className="w-full border rounded px-3 py-2" placeholder="Task title *" value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={255} />
      <textarea className="w-full border rounded px-3 py-2" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} maxLength={2000} />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-500">Priority</label>
          <select className="w-full border rounded px-2 py-1" value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500">Due Date</label>
          <input type="datetime-local" className="w-full border rounded px-2 py-1" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
        </div>
      </div>

      {dueDate && (
        <div>
          <label className="text-xs text-gray-500">Reminder</label>
          <input type="datetime-local" className="w-full border rounded px-2 py-1" value={reminderAt} onChange={(e) => setReminderAt(e.target.value)} max={dueDate} />
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-gray-500">Recurrence</label>
          <select className="w-full border rounded px-2 py-1" value={recurrencePattern} onChange={(e) => setRecurrencePattern(e.target.value)}>
            <option value="">None</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
        {recurrencePattern && (
          <>
            <div>
              <label className="text-xs text-gray-500">Every N</label>
              <input type="number" min={1} className="w-full border rounded px-2 py-1" value={recurrenceInterval} onChange={(e) => setRecurrenceInterval(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-gray-500">Ends At</label>
              <input type="datetime-local" className="w-full border rounded px-2 py-1" value={recurrenceEndsAt} onChange={(e) => setRecurrenceEndsAt(e.target.value)} />
            </div>
          </>
        )}
      </div>

      <div>
        <label className="text-xs text-gray-500 mb-1 block">Tags (max 10)</label>
        <TagPicker tags={tags} selected={selectedTags} onChange={setSelectedTags} />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
        <button type="submit" className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">Create Task</button>
      </div>
    </form>
  );
}

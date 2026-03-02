"use client";
import { useEffect, useState, useCallback } from "react";
import { Task, Tag, PaginatedTasks, TaskCreateInput } from "@/types";
import SearchInput from "@/components/search/search-input";
import FilterBar, { Filters } from "@/components/filters/filter-bar";
import SortControls from "@/components/filters/sort-controls";
import Pagination from "@/components/ui/pagination";
import TagBadge from "@/components/tags/tag-badge";
import TagList from "@/components/tags/tag-list";
import TagCreateDialog from "@/components/tags/tag-create-dialog";
import TaskForm from "@/components/tasks/task-form";
import { WsClient } from "@/lib/ws";

function authHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Filters>({ status: "", priority: "", tag: "", overdue: "" });
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [showForm, setShowForm] = useState(false);
  const [showTagDialog, setShowTagDialog] = useState(false);
  const [showTags, setShowTags] = useState(false);
  const [notification, setNotification] = useState("");

  const fetchTasks = useCallback(async () => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", "20");
    params.set("sort_by", sortBy);
    params.set("sort_order", sortOrder);
    if (search) params.set("search", search);
    if (filters.status) params.set("status", filters.status);
    if (filters.priority) params.set("priority", filters.priority);
    if (filters.tag) params.set("tag", filters.tag);
    if (filters.overdue) params.set("overdue", "true");

    const res = await fetch(`/api/tasks?${params}`, { headers: authHeaders() });
    if (res.status === 401) { window.location.href = "/login"; return; }
    const data: PaginatedTasks = await res.json();
    setTasks(data.items);
    setTotal(data.total);
    setTotalPages(data.total_pages);
  }, [page, search, filters, sortBy, sortOrder]);

  const fetchTags = useCallback(async () => {
    const res = await fetch("/api/tags", { headers: authHeaders() });
    if (res.ok) setTags(await res.json());
  }, []);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);
  useEffect(() => { fetchTags(); }, [fetchTags]);

  // WebSocket real-time updates
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    const ws = new WsClient(token);
    ws.connect();
    ws.onEvent((ev) => {
      if (ev.event_type.startsWith("task.")) fetchTasks();
      if (ev.event_type === "reminder.triggered") {
        setNotification(`Reminder: ${(ev.data as { task_title?: string }).task_title || "Task reminder"}`);
        setTimeout(() => setNotification(""), 5000);
      }
    });
    return () => ws.close();
  }, [fetchTasks]);

  const createTask = async (data: TaskCreateInput) => {
    await fetch("/api/tasks", { method: "POST", headers: authHeaders(), body: JSON.stringify(data) });
    setShowForm(false);
    fetchTasks();
  };

  const completeTask = async (id: string) => {
    await fetch(`/api/tasks/${id}/complete`, { method: "PATCH", headers: authHeaders() });
    fetchTasks();
  };

  const deleteTask = async (id: string) => {
    await fetch(`/api/tasks/${id}`, { method: "DELETE", headers: authHeaders() });
    fetchTasks();
  };

  const createTag = async (name: string, color: string) => {
    await fetch("/api/tags", { method: "POST", headers: authHeaders(), body: JSON.stringify({ name, color }) });
    fetchTags();
  };

  const deleteTag = async (id: string) => {
    await fetch(`/api/tags/${id}`, { method: "DELETE", headers: authHeaders() });
    fetchTags();
    fetchTasks();
  };

  const logout = () => { localStorage.removeItem("token"); window.location.href = "/login"; };

  const priorityColor: Record<string, string> = {
    low: "text-gray-500", medium: "text-blue-500", high: "text-orange-500", critical: "text-red-600 font-bold",
  };

  return (
    <div className="max-w-5xl mx-auto p-4">
      {notification && (
        <div className="fixed top-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded shadow z-50">{notification}</div>
      )}

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Todo Dashboard</h1>
        <div className="flex gap-2">
          <button onClick={() => setShowTags(!showTags)} className="px-3 py-1 text-sm border rounded">Tags</button>
          <button onClick={() => setShowForm(!showForm)} className="px-3 py-1 text-sm bg-blue-600 text-white rounded">+ New Task</button>
          <button onClick={logout} className="px-3 py-1 text-sm text-gray-500 border rounded">Logout</button>
        </div>
      </div>

      {showTags && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold">Your Tags</h2>
            <button onClick={() => setShowTagDialog(true)} className="text-sm text-blue-600">+ New Tag</button>
          </div>
          <TagList tags={tags} onDelete={deleteTag} />
          <TagCreateDialog open={showTagDialog} onClose={() => setShowTagDialog(false)} onCreate={createTag} />
        </div>
      )}

      {showForm && <div className="mb-4"><TaskForm tags={tags} onSubmit={createTask} onCancel={() => setShowForm(false)} /></div>}

      <div className="space-y-3 mb-4">
        <SearchInput value={search} onChange={(v) => { setSearch(v); setPage(1); }} />
        <div className="flex items-center justify-between">
          <FilterBar filters={filters} tags={tags} onChange={(f) => { setFilters(f); setPage(1); }} />
          <SortControls sortBy={sortBy} sortOrder={sortOrder} onSortByChange={setSortBy} onSortOrderChange={setSortOrder} />
        </div>
      </div>

      <p className="text-sm text-gray-500 mb-2">{total} task{total !== 1 ? "s" : ""}</p>

      <div className="space-y-2">
        {tasks.map((t) => (
          <div key={t.id} className={`p-3 bg-white rounded shadow-sm flex items-start justify-between ${t.is_overdue ? "border-l-4 border-red-500" : ""}`}>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={`text-xs uppercase ${priorityColor[t.priority] || ""}`}>{t.priority}</span>
                <span className={`font-medium ${t.status === "completed" ? "line-through text-gray-400" : ""}`}>{t.title}</span>
                {t.is_overdue && <span className="text-xs bg-red-100 text-red-600 px-1 rounded">Overdue</span>}
                {t.recurrence_pattern && <span className="text-xs bg-purple-100 text-purple-600 px-1 rounded">{t.recurrence_pattern}</span>}
              </div>
              {t.description && <p className="text-sm text-gray-500 mt-1">{t.description}</p>}
              <div className="flex items-center gap-2 mt-1">
                {t.due_date && <span className="text-xs text-gray-400">Due: {new Date(t.due_date).toLocaleDateString()}</span>}
                {t.reminder_at && !t.reminder_sent && <span className="text-xs text-yellow-600">Reminder set</span>}
                {t.tags.map((tag) => <TagBadge key={tag.id} tag={tag} />)}
              </div>
            </div>
            <div className="flex gap-1 ml-2">
              {t.status !== "completed" && (
                <button onClick={() => completeTask(t.id)} className="text-xs text-green-600 border rounded px-2 py-1 hover:bg-green-50">Done</button>
              )}
              <button onClick={() => deleteTask(t.id)} className="text-xs text-red-500 border rounded px-2 py-1 hover:bg-red-50">Del</button>
            </div>
          </div>
        ))}
        {tasks.length === 0 && <p className="text-center text-gray-400 py-8">No tasks found.</p>}
      </div>

      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}

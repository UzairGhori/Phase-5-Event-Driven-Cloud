// Phase V — Shared TypeScript interfaces

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: "pending" | "in_progress" | "completed";
  priority: "low" | "medium" | "high" | "critical";
  user_id: string;
  due_date: string | null;
  is_overdue: boolean;
  recurrence_pattern: "daily" | "weekly" | "monthly" | null;
  recurrence_interval: number | null;
  recurrence_ends_at: string | null;
  source_task_id: string | null;
  reminder_at: string | null;
  reminder_sent: boolean;
  tags: TagBrief[];
  created_at: string;
  updated_at: string;
}

export interface TagBrief {
  id: string;
  name: string;
  slug: string;
  color: string | null;
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
  color: string | null;
  user_id: string;
  created_at: string;
  task_count: number;
}

export interface PaginatedTasks {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskCreateInput {
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  reminder_at?: string;
  recurrence_pattern?: string;
  recurrence_interval?: number;
  recurrence_ends_at?: string;
  tag_ids?: string[];
}

export interface TaskUpdateInput {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string | null;
  reminder_at?: string | null;
  recurrence_pattern?: string | null;
  recurrence_interval?: number | null;
  recurrence_ends_at?: string | null;
  tag_ids?: string[];
}

export interface User {
  id: string;
  username: string;
  email: string;
}

export interface WsEvent {
  event_type: string;
  data: Record<string, unknown>;
}

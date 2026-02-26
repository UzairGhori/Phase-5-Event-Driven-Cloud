// T-A027 — Proxy POST /api/tasks/:taskId/tags
import { taskApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest, { params }: { params: Promise<{ taskId: string }> }) {
  const { taskId } = await params;
  const body = await req.json();
  const res = await fetch(taskApiUrl(`/api/tasks/${taskId}/tags`), {
    method: "POST",
    headers: forwardHeaders(req),
    body: JSON.stringify(body),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

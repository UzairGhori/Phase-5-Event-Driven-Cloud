// T-A027 — Proxy PATCH /api/tasks/:taskId/complete
import { taskApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ taskId: string }> }) {
  const { taskId } = await params;
  const res = await fetch(taskApiUrl(`/api/tasks/${taskId}/complete`), {
    method: "PATCH",
    headers: forwardHeaders(req),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

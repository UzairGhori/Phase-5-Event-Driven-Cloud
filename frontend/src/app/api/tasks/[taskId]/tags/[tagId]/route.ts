// T-A027 — Proxy DELETE /api/tasks/:taskId/tags/:tagId
import { taskApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ taskId: string; tagId: string }> }) {
  const { taskId, tagId } = await params;
  const res = await fetch(taskApiUrl(`/api/tasks/${taskId}/tags/${tagId}`), {
    method: "DELETE",
    headers: forwardHeaders(req),
  });
  if (res.status === 204) return new NextResponse(null, { status: 204 });
  return NextResponse.json(await res.json(), { status: res.status });
}

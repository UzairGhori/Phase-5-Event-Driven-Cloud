import { taskApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ tagId: string }> }) {
  const { tagId } = await params;
  const body = await req.json();
  const res = await fetch(taskApiUrl(`/api/tags/${tagId}`), {
    method: "PATCH",
    headers: forwardHeaders(req),
    body: JSON.stringify(body),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ tagId: string }> }) {
  const { tagId } = await params;
  const res = await fetch(taskApiUrl(`/api/tags/${tagId}`), {
    method: "DELETE",
    headers: forwardHeaders(req),
  });
  if (res.status === 204) return new NextResponse(null, { status: 204 });
  return NextResponse.json(await res.json(), { status: res.status });
}

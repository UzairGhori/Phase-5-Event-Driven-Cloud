// T-A027 — Proxy GET /api/tasks and POST /api/tasks
import { taskApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const qs = req.nextUrl.search;
  const res = await fetch(taskApiUrl(`/api/tasks${qs}`), { headers: forwardHeaders(req) });
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await fetch(taskApiUrl("/api/tasks"), {
    method: "POST",
    headers: forwardHeaders(req),
    body: JSON.stringify(body),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

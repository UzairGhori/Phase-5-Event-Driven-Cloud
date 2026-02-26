import { taskApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const qs = req.nextUrl.search;
  const res = await fetch(taskApiUrl(`/api/tasks/overdue${qs}`), { headers: forwardHeaders(req) });
  return NextResponse.json(await res.json(), { status: res.status });
}

import { chatApiUrl, forwardHeaders } from "@/lib/dapr";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await fetch(chatApiUrl("/api/chat/message"), {
    method: "POST",
    headers: forwardHeaders(req),
    body: JSON.stringify(body),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

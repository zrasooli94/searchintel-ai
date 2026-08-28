import { cookies } from "next/headers";

import {
  configuredOperatorSecret,
  isOperatorSession,
  newOperatorSessionToken,
  OPERATOR_COOKIE,
} from "@/lib/operator-session";
import {
  OPERATOR_SESSION_SECONDS,
  passphrasesMatch,
} from "@/lib/operator-token";


export async function GET() {
  return Response.json({
    authorized: await isOperatorSession(),
  });
}


export async function POST(request: Request) {
  const expected = configuredOperatorSecret();
  const payload = await request.json().catch(() => null) as {
    passphrase?: unknown;
  } | null;
  const supplied = typeof payload?.passphrase === "string"
    ? payload.passphrase
    : "";

  if (!expected || !passphrasesMatch(supplied, expected)) {
    return Response.json(
      { detail: "Invalid operator passphrase." },
      { status: 401 },
    );
  }

  const cookieStore = await cookies();
  cookieStore.set(
    OPERATOR_COOKIE,
    newOperatorSessionToken(),
    {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
      maxAge: OPERATOR_SESSION_SECONDS,
    },
  );
  return Response.json({ authorized: true });
}


export async function DELETE() {
  const cookieStore = await cookies();
  cookieStore.set(OPERATOR_COOKIE, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return Response.json({ authorized: false });
}

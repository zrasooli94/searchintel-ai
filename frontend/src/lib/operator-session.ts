import "server-only";

import { cookies } from "next/headers";

import {
  createOperatorToken,
  verifyOperatorToken,
} from "@/lib/operator-token";


export const OPERATOR_COOKIE = "searchintel_operator";


function operatorSecret(): string | undefined {
  return process.env.SEARCHINTEL_OPERATOR_SECRET?.trim() || undefined;
}


export async function isOperatorSession(): Promise<boolean> {
  const cookieStore = await cookies();
  return verifyOperatorToken(
    cookieStore.get(OPERATOR_COOKIE)?.value,
    operatorSecret(),
  );
}


export function newOperatorSessionToken(): string {
  const secret = operatorSecret();
  if (!secret) {
    throw new Error(
      "SEARCHINTEL_OPERATOR_SECRET is not configured.",
    );
  }
  return createOperatorToken(secret);
}


export function configuredOperatorSecret(): string | undefined {
  return operatorSecret();
}


export async function operatorMutationGuard(): Promise<Response | null> {
  if (await isOperatorSession()) {
    return null;
  }
  return Response.json(
    {
      detail: "Authorized operator access is required.",
    },
    { status: 403 },
  );
}


export async function operatorBackendHeaders(): Promise<HeadersInit> {
  const denied = await operatorMutationGuard();
  if (denied) {
    throw new Error("Authorized operator access is required.");
  }
  const apiToken = process.env.SEARCHINTEL_API_TOKEN?.trim();
  if (!apiToken) {
    throw new Error("SEARCHINTEL_API_TOKEN is not configured.");
  }
  return {
    "X-SearchIntel-Operator": apiToken,
  };
}

import "server-only";


const DEVELOPMENT_API_BASE_URL =
  "http://127.0.0.1:8000/api/v1";


export function searchIntelApiBaseUrl(): string {
  const configured =
    process.env.SEARCHINTEL_API_BASE_URL
      ?.trim()
      .replace(/\/$/, "");

  if (configured) {
    return configured;
  }

  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "SEARCHINTEL_API_BASE_URL is required in production.",
    );
  }

  return DEVELOPMENT_API_BASE_URL;
}


export function searchIntelApiHeaders(
  initial?: HeadersInit,
): Headers {
  const token =
    process.env.SEARCHINTEL_API_TOKEN?.trim();

  if (
    process.env.NODE_ENV === "production"
    && !token
  ) {
    throw new Error(
      "SEARCHINTEL_API_TOKEN is required in production.",
    );
  }

  const headers = new Headers(initial);
  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return headers;
}


export function searchIntelFetch(
  input: string | URL | Request,
  init: RequestInit = {},
): Promise<Response> {
  return fetch(
    input,
    {
      ...init,
      headers: searchIntelApiHeaders(
        init.headers,
      ),
    },
  );
}

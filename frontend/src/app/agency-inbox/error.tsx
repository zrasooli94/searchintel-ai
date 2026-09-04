"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <main className="crystal-page min-h-screen p-10"><h1 className="text-2xl">Agency Inbox could not load</h1><p className="my-4">No data was changed. Please try again.</p><button onClick={reset} className="crystal-primary-button px-4 py-2">Try again</button></main>;
}

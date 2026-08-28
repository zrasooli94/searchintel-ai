"use client";

import {
  KeyRound,
  Loader2,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";


export default function OperatorAccessPanel({
  initialAuthorized,
}: {
  initialAuthorized: boolean;
}) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(initialAuthorized);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const value = new FormData(form).get("passphrase");
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/operator/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ passphrase: String(value ?? "") }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(typeof payload?.detail === "string" ? payload.detail : "Could not authorize operator access.");
      }
      setAuthorized(true);
      form.reset();
      router.refresh();
    } catch (signInError) {
      setError(signInError instanceof Error ? signInError.message : "Could not authorize operator access.");
    } finally {
      setLoading(false);
    }
  }

  async function signOut() {
    setLoading(true);
    await fetch("/api/operator/session", { method: "DELETE" });
    setAuthorized(false);
    setLoading(false);
    router.refresh();
  }

  return (
    <section className="rounded-[20px] border border-slate-200/80 bg-white/85 p-5 shadow-sm">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div className="flex gap-3">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${authorized ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-500"}`}>
            {authorized ? <ShieldCheck className="h-5 w-5" /> : <LockKeyhole className="h-5 w-5" />}
          </div>
          <div>
            <div className="font-medium text-slate-950">
              {authorized ? "Operator controls unlocked" : "Public demo mode"}
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              {authorized
                ? "Paid execution and configuration mutations are enabled for this private browser session."
                : "Historical dashboards remain public. Paid execution and configuration changes require agency operator access."}
            </p>
          </div>
        </div>

        {authorized ? (
          <button type="button" onClick={signOut} disabled={loading} className="rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-medium text-slate-600 hover:bg-slate-50">
            Lock controls
          </button>
        ) : (
          <form onSubmit={signIn} className="flex w-full gap-2 md:w-auto">
            <label className="sr-only" htmlFor="operator-passphrase">Operator passphrase</label>
            <input id="operator-passphrase" name="passphrase" type="password" required autoComplete="current-password" placeholder="Operator passphrase" className="crystal-field min-w-0 px-3 py-2.5 text-sm md:w-56" />
            <button type="submit" disabled={loading} className="crystal-primary-button shrink-0 px-4 py-2.5 text-sm">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
              Unlock
            </button>
          </form>
        )}
      </div>
      {error && <p className="mt-3 text-xs text-red-700">{error}</p>}
    </section>
  );
}

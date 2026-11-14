"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, cap, type Profile } from "@/lib/api";
import { clearSession, loadSession } from "@/lib/session";

const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${Math.round(x * 100)}%`);

export default function Perfil() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const s = loadSession();
    if (!s) {
      router.replace("/");
      return;
    }
    api.profile(s.student).then(setProfile).catch((e: Error) => setError(e.message));
  }, [router]);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="text-3xl font-semibold tracking-tight">El meu progrés</h1>
      {error && <p className="text-red-600">{error}</p>}
      {profile && (
        <>
          <div className="grid grid-cols-3 gap-3">
            {[
              ["Nivell", String(profile.level)],
              ["Problemes", String(profile.attempts)],
              ["Al primer intent", pct(profile.accuracy)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
                <div className="text-3xl font-semibold tabular-nums">{value}</div>
              </div>
            ))}
          </div>

          <section className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="mb-3 font-semibold">Per temes</h2>
            {profile.by_topic.length === 0 ? (
              <p className="text-zinc-500">Encara no has fet cap problema.</p>
            ) : (
              <ul className="flex flex-col gap-3">
                {profile.by_topic.map((t) => (
                  <li key={t.topic} className="flex flex-col gap-1">
                    <div className="flex justify-between text-sm">
                      <span>{cap(t.topic)}</span>
                      <span className="tabular-nums text-zinc-500">
                        {t.correct}/{t.attempts} · {pct(t.accuracy)}
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                      <div className="h-full rounded-full bg-amber-500" style={{ width: pct(t.accuracy) }} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <p className="text-sm text-zinc-500">
            Aquestes dades només són en aquesta placa. Cap servidor de fora les veu.
          </p>
          <div className="flex gap-3">
            <Link href="/practica/" className="rounded-full bg-amber-500 px-5 py-2 font-medium text-white hover:bg-amber-600">
              Continua practicant
            </Link>
            <button
              onClick={() => {
                clearSession();
                router.push("/");
              }}
              className="rounded-full border border-zinc-300 px-5 py-2 dark:border-zinc-700"
            >
              Surt
            </button>
          </div>
        </>
      )}
    </main>
  );
}

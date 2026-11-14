"use client";

import { useEffect, useState } from "react";
import { api, cap, imageUrl, type Teacher } from "@/lib/api";

const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${Math.round(x * 100)}%`);

// Vermell (s'encallen) -> verd (ho dominen)
function cellColor(accuracy: number | undefined) {
  if (accuracy === undefined) return "transparent";
  const hue = Math.round(accuracy * 120);
  return `hsla(${hue}, 70%, 50%, 0.25)`;
}

export default function Mestre() {
  const [data, setData] = useState<Teacher | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () => api.teacher().then(setData).catch((e: Error) => setError(e.message));
    load();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">On s&apos;encalla la classe</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Només àlies, cap dada personal. S&apos;actualitza sol cada 10 segons.
        </p>
      </div>
      {error && <p className="text-red-600">{error}</p>}
      {data && (
        <>
          <p className="text-sm text-zinc-500">
            {data.students} alumnes · {data.attempts} problemes intentats
          </p>

          <section className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="mb-3 font-semibold">Encerts al primer intent, per tema i nivell</h2>
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="text-left text-zinc-500">
                  <th className="py-2 pr-3 font-medium">Tema</th>
                  {data.levels.map((l) => (
                    <th key={l} className="px-2 py-2 text-center font-medium">
                      Nivell {l}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.topics.map((topic) => (
                  <tr key={topic} className="border-t border-zinc-100 dark:border-zinc-800">
                    <td className="py-2 pr-3">{cap(topic)}</td>
                    {data.levels.map((l) => {
                      const cell = data.cells.find((c) => c.topic === topic && c.level === l);
                      return (
                        <td key={l} className="px-2 py-2 text-center tabular-nums" style={{ background: cellColor(cell?.accuracy) }}>
                          {cell ? (
                            <>
                              {pct(cell.accuracy)}
                              <span className="block text-[10px] text-zinc-500">
                                {cell.attempts} intents · {cell.avg_hints.toLocaleString("ca")} ajudes
                              </span>
                            </>
                          ) : (
                            <span className="text-zinc-300">·</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="mb-1 font-semibold">Les trampes on més cau la classe</h2>
            <p className="mb-4 text-sm text-zinc-500">
              Les opcions incorrectes més triades i l&apos;error de raonament que hi porta. Bon material per comentar a classe.
            </p>
            {data.traps.length === 0 ? (
              <p className="text-zinc-500">Encara no hi ha errors registrats.</p>
            ) : (
              <ul className="grid gap-3 sm:grid-cols-2">
                {data.traps.map((t) => (
                  <li key={`${t.problem_id}-${t.letter}`} className="flex flex-col gap-2 rounded-xl border border-zinc-200 p-3 dark:border-zinc-800">
                    <div className="flex justify-between text-xs text-zinc-500">
                      <span>
                        {cap(t.topic)} · nivell {t.level}
                      </span>
                      <span>
                        {t.count} alumnes ({pct(t.share)}) han triat la {t.letter}
                      </span>
                    </div>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={imageUrl(t)} alt={`Problema ${t.problem_id}`} className="rounded-lg border bg-white" />
                    <p className="text-sm">{t.trap || "Sense explicació preparada per a aquesta opció."}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </main>
  );
}

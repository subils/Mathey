"use client";

import { useEffect, useState } from "react";
import LedMatrix from "@/components/LedMatrix";
import { api, type Matrix, type Stats } from "@/lib/api";

// Sala de màquines: el que fa la placa ara mateix, per ensenyar-ho al jurat.
export default function Placa() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [matrix, setMatrix] = useState<Matrix | undefined>();
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () => {
      api.stats().then(setStats, (e: Error) => setError(e.message));
      api.matrix().then((m) => setMatrix(m.matrix), () => undefined);
    };
    load();
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, []);

  const tiles: [string, string][] = stats
    ? [
        ["On corre", stats.host],
        ["IA de la placa", stats.llm === "up" ? "activa" : "no disponible"],
        [
          "Memòria lliure",
          stats.memory ? `${stats.memory.available_mb.toLocaleString("ca")} de ${stats.memory.total_mb.toLocaleString("ca")} MB` : "–",
        ],
        ["Problemes amb contingut verificat", `${stats.bank.verified} de ${stats.bank.prepared}`],
        ["Alumnes · respostes · ajudes", `${stats.students} · ${stats.attempts} · ${stats.hints}`],
        [
          "Preguntes de la IA (mediana)",
          stats.questions.median_seconds !== null ? `${stats.questions.median_seconds.toLocaleString("ca")} s` : "encara cap",
        ],
        ["Preguntes de la IA / de reserva", `${stats.questions.from_board} / ${stats.questions.fallback}`],
        ["Internet", stats.internet],
      ]
    : [];

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Sala de màquines</h1>
        <p className="text-zinc-600 dark:text-zinc-400">Què fa la placa ara mateix. S&apos;actualitza cada 3 segons.</p>
      </div>
      {error && <p className="text-red-600">{error}</p>}
      <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
        <div className="flex items-center justify-center rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <LedMatrix matrix={matrix} size={18} />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {tiles.map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
              <div className="mt-1 text-xl font-semibold tabular-nums">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

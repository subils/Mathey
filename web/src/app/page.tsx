"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { saveSession, useSession } from "@/lib/session";

const GRADES = ["5è", "6è", "1r ESO", "2n ESO"];

export default function Home() {
  const router = useRouter();
  const [alias, setAlias] = useState("");
  const [grade, setGrade] = useState("6è");
  const [easy, setEasy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const existing = useSession()?.alias ?? null;

  async function start(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const session = await api.session(alias.trim(), grade, easy);
      saveSession(session);
      router.push("/practica/");
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-10 px-4 py-12">
      <section className="flex flex-col gap-3">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          No et donarem la resposta.
          <br />
          <span className="text-amber-600">T&apos;ajudarem a trobar-la.</span>
        </h1>
        <p className="max-w-xl text-lg text-zinc-600 dark:text-zinc-400">
          Problemes del Cangur al teu nivell. Quan t&apos;encallis, el mentor et fa una pregunta, et dona una pista o
          et proposa un problema més fàcil que fa servir la mateixa idea. Tot passa dins d&apos;aquesta placa, sense
          internet.
        </p>
      </section>

      {existing && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-white p-4 dark:border-amber-900 dark:bg-zinc-900">
          <p>
            Hola de nou, <strong>{existing}</strong>!
          </p>
          <button
            onClick={() => router.push("/practica/")}
            className="rounded-full bg-amber-500 px-5 py-2 font-medium text-white hover:bg-amber-600"
          >
            Continua practicant
          </button>
        </div>
      )}

      <form
        onSubmit={start}
        className="flex flex-col gap-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
      >
        <h2 className="text-xl font-semibold">{existing ? "O comença com algú altre" : "Comença"}</h2>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Com et dic? (un sobrenom, no cal el teu nom real)</span>
          <input
            value={alias}
            onChange={(e) => setAlias(e.target.value)}
            maxLength={30}
            required
            placeholder="Per exemple: Llamp"
            className="rounded-xl border border-zinc-300 px-4 py-3 text-lg outline-none focus:border-amber-500 dark:border-zinc-700 dark:bg-zinc-950"
          />
        </label>
        <fieldset className="flex flex-col gap-1.5">
          <legend className="mb-1.5 text-sm font-medium">Quin curs fas?</legend>
          <div className="flex flex-wrap gap-2">
            {GRADES.map((g) => (
              <button
                type="button"
                key={g}
                onClick={() => setGrade(g)}
                className={`rounded-xl border px-4 py-2.5 text-base ${
                  grade === g
                    ? "border-amber-500 bg-amber-50 font-semibold text-amber-900 dark:bg-amber-900/30 dark:text-amber-100"
                    : "border-zinc-300 hover:border-zinc-400 dark:border-zinc-700"
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </fieldset>
        <label className="flex items-start gap-3 text-sm">
          <input type="checkbox" checked={easy} onChange={(e) => setEasy(e.target.checked)} className="mt-1 h-4 w-4" />
          <span>
            <strong>Lectura fàcil.</strong> Enunciats amb frases curtes, una idea per línia i lletra més gran.
          </span>
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy || !alias.trim()}
          className="rounded-full bg-amber-500 px-6 py-3 text-lg font-semibold text-white hover:bg-amber-600 disabled:opacity-50"
        >
          {busy ? "Un moment…" : "Som-hi!"}
        </button>
      </form>

      <p className="text-center text-xs text-zinc-500">
        Les teves respostes es guarden només en aquesta placa. No surten mai de l&apos;aula.
      </p>
    </main>
  );
}

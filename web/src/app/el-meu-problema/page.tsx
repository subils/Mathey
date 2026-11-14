"use client";

// Pàgina de PROVA de «Porta el teu problema». Funcional, sense disseny: tot el
// frontend es refarà. El que importa aquí és el flux i les crides a l'API.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, cap, imageUrl, type OwnHelp, type OwnMatch } from "@/lib/api";
import { useSession } from "@/lib/session";

/** Redueix la foto al navegador (màx. 1600 px, JPEG) perquè la placa la llegeixi de pressa. */
async function shrink(file: File, max = 1600): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, max / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.9);
}

export default function ElMeuProblema() {
  const router = useRouter();
  const session = useSession();
  const [text, setText] = useState("");
  const [ocrInfo, setOcrInfo] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [match, setMatch] = useState<OwnMatch | null>(null);
  const [doubt, setDoubt] = useState("");
  const [helps, setHelps] = useState<{ doubt: string; help: OwnHelp }[]>([]);

  useEffect(() => {
    if (session === null) router.replace("/");
  }, [session, router]);

  if (!session) return null;

  const run = async (label: string, work: () => Promise<void>) => {
    setBusy(label);
    setError("");
    try {
      await work();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  };

  const onFile = (file: File | undefined) =>
    file &&
    run("La placa està llegint la foto…", async () => {
      const result = await api.ownOcr(session.student, await shrink(file));
      setText(result.text);
      setMatch(null);
      setHelps([]);
      setOcrInfo(
        result.empty
          ? "No he pogut llegir cap text. Escriu el problema a mà."
          : `Llegit amb ${result.engine} en ${result.seconds?.toLocaleString("ca")} s. Repassa'l i corregeix el que calgui.`,
      );
    });

  const onMatch = () =>
    run("Buscant problemes semblants…", async () => {
      setMatch(await api.ownMatch(session.student, text));
      setHelps([]);
    });

  const onHelp = () =>
    match &&
    run("La placa està pensant…", async () => {
      const help = await api.ownHelp(session.student, match.own_id, doubt);
      setHelps((list) => [...list, { doubt, help }]);
      setDoubt("");
    });

  const box = "rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900";
  const button = "rounded-full bg-amber-500 px-5 py-2 font-medium text-white hover:bg-amber-600 disabled:opacity-50";
  const area =
    "w-full rounded-xl border border-zinc-300 p-3 outline-none focus:border-amber-500 dark:border-zinc-700 dark:bg-zinc-950";

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-5 px-4 py-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Porta el teu problema</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Fes una foto d&apos;un problema dels deures o del llibre. No te&apos;l resoldrem: et buscarem un problema
          semblant per practicar i t&apos;ajudarem allà on t&apos;encalles.
        </p>
      </div>

      <section className={box}>
        <h2 className="mb-3 font-semibold">1. El problema</h2>
        <input type="file" accept="image/*" onChange={(e) => onFile(e.target.files?.[0])} className="mb-3 block text-sm" />
        {ocrInfo && <p className="mb-2 text-sm text-zinc-500">{ocrInfo}</p>}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          placeholder="…o escriu aquí l'enunciat."
          className={area}
        />
        <button onClick={onMatch} disabled={!!busy || text.trim().split(/\s+/).length < 4} className={`mt-3 ${button}`}>
          Busca problemes semblants
        </button>
      </section>

      {busy && <p className="text-amber-700 dark:text-amber-300">{busy}</p>}
      {error && <p className="text-red-600">{error}</p>}

      {match && (
        <>
          <section className={box}>
            <h2 className="mb-1 font-semibold">2. Per practicar la mateixa idea</h2>
            <p className="mb-3 text-sm text-zinc-500">
              Sembla un problema de <strong>{cap(match.topic)}</strong> (confiança {Math.round(match.topic_confidence * 100)}%).
            </p>
            {match.message && <p className="mb-3">{match.message}</p>}
            <ul className="flex flex-col gap-4">
              {match.siblings.map((s) => (
                <li key={s.id} className="flex flex-col gap-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={imageUrl(s)} alt={s.text} className="rounded-lg border bg-white" />
                  <div className="flex items-center justify-between text-sm text-zinc-500">
                    <span>
                      {cap(s.topic)} · nivell {s.level} · semblança {s.score.toLocaleString("ca")}
                    </span>
                    <Link href={`/practica/?id=${encodeURIComponent(s.id)}`} className="font-medium text-amber-700 underline">
                      Practica aquest
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-sm">
              <strong>Una estratègia:</strong> {match.strategy}
            </p>
          </section>

          <section className={box}>
            <h2 className="mb-3 font-semibold">3. On t&apos;encalles?</h2>
            {helps.map(({ doubt: asked, help }, i) => (
              <div key={i} className="mb-4 flex flex-col gap-1">
                <p className="text-sm text-zinc-500">Tu: {asked}</p>
                <p className="rounded-xl bg-amber-50 p-3 dark:bg-amber-950/40">{help.reply}</p>
                <p className="text-[11px] text-zinc-500">
                  {help.source === "placa"
                    ? `Pista de la IA de la placa · ${help.seconds.toLocaleString("ca")} s`
                    : `Ajuda preparada (${help.rejected ?? "la IA no ha respost"})`}
                </p>
              </div>
            ))}
            <textarea
              value={doubt}
              onChange={(e) => setDoubt(e.target.value)}
              rows={3}
              maxLength={300}
              placeholder="Explica què has fet i on no saps continuar…"
              className={area}
            />
            <button onClick={onHelp} disabled={!!busy || doubt.trim().split(/\s+/).length < 2} className={`mt-3 ${button}`}>
              Demana una pista
            </button>
          </section>
        </>
      )}
    </main>
  );
}

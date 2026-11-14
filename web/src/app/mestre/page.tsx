"use client";

import { RefreshCw, Users } from "lucide-react";
import { PageShell } from "@/components/marketing/page-shell";
import { DoubleCard, Eyebrow, Pill } from "@/components/ui/surface";
import { api, cap, imageUrl } from "@/lib/api";
import { useLive } from "@/lib/use-live";

const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${Math.round(x * 100)}%`);

/** Vermell (s'encallen) → verd (ho dominen), barrejat amb blanc perquè el text es llegeixi. */
const cellColor = (accuracy: number) =>
  `color-mix(in oklab, hsl(${Math.round(accuracy * 130)} 70% 50%) ${18 + accuracy * 22}%, white)`;

export default function Mestre() {
  const { data, error } = useLive(() => api.teacher(), 10000);

  return (
    <PageShell
      eyebrow="Vista del mestre"
      title={
        <>
          On s&apos;encalla <span className="text-gradient">la classe</span>
        </>
      }
      lead="Només àlies, cap dada personal. S'actualitza sola cada 10 segons."
      aside={
        data && (
          <div className="flex gap-2 text-[13px]">
            <Pill className="px-2.5 py-1 text-[10px]">
              <Users className="size-3" /> {data.students} alumnes
            </Pill>
            <Pill className="px-2.5 py-1 text-[10px]">
              <RefreshCw className="size-3" /> {data.attempts} problemes
            </Pill>
          </div>
        )
      }
    >
      {error && !data && <p className="mb-6 rounded-xl bg-destructive/[0.07] px-4 py-3 text-destructive">No hi ha connexió amb la placa.</p>}
      {data && (
        <div className="flex flex-col gap-px">
          <DoubleCard plain className="overflow-x-auto p-6 md:p-8">
            <div className="mb-5 flex flex-col gap-1">
              <h2 className="text-lg font-medium">Encerts al primer intent, per tema i nivell</h2>
              <p className="text-sm font-light text-muted-foreground">Sota de cada percentatge: intents i ajudes per problema.</p>
            </div>
            <table className="w-full min-w-[620px] border-separate border-spacing-1.5 text-[13px]">
              <thead>
                <tr>
                  <th />
                  {data.levels.map((l) => (
                    <th key={l} className="pb-1 text-center text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                      Nivell {l}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.topics.map((topic) => (
                  <tr key={topic}>
                    <td className="pr-3 text-right whitespace-nowrap text-muted-foreground">{cap(topic)}</td>
                    {data.levels.map((l) => {
                      const cell = data.cells.find((c) => c.topic === topic && c.level === l);
                      return (
                        <td
                          key={l}
                          className="h-16 rounded-xl text-center tabular-nums"
                          style={{ background: cell ? cellColor(cell.accuracy) : "rgb(0 0 0 / 0.035)" }}
                        >
                          {cell && (
                            <>
                              <span className="block font-mono text-[15px] font-semibold">{pct(cell.accuracy)}</span>
                              <span className="block text-[11px] text-foreground/60">
                                {cell.attempts} intents · {cell.avg_hints.toLocaleString("ca")} ajudes
                              </span>
                            </>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </DoubleCard>

          <div className="mt-16 mb-6 flex flex-col gap-2">
            <Eyebrow>Les trampes</Eyebrow>
            <h2 className="text-[clamp(22px,2.6vw,32px)] font-medium tracking-[-0.02em]">On més cau la classe</h2>
            <p className="max-w-2xl text-[15px] font-light text-muted-foreground">
              Les opcions incorrectes més triades i l&apos;error de raonament que hi porta. Bon material per comentar a classe.
            </p>
          </div>
          {data.traps.length === 0 ? (
            <DoubleCard plain className="p-10 text-center text-muted-foreground">
              Encara no hi ha errors registrats.
            </DoubleCard>
          ) : (
            <div className="grid grid-cols-1 gap-px md:grid-cols-2">
              {data.traps.map((t, i) => (
                <DoubleCard key={`${t.problem_id}-${t.letter}`} index={i} className="flex flex-col gap-4 p-6">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[12px]">
                    <span className="rounded-md bg-black/[0.05] px-2 py-0.5 font-medium">
                      {cap(t.topic)} · nivell {t.level}
                    </span>
                    <span className="text-muted-foreground">
                      <strong className="font-semibold text-foreground">{t.count}</strong> alumnes ({pct(t.share)}) han triat la{" "}
                      <span className="font-mono font-semibold text-destructive">{t.letter}</span>
                    </span>
                  </div>
                  {/* eslint-disable-next-line @next/next/no-img-element -- exportació estàtica */}
                  <img src={imageUrl(t)} alt={`Problema ${t.problem_id}`} className="rounded-xl border border-black/[0.05] bg-white" />
                  <p className="text-[14px] leading-relaxed">{t.trap || "Sense explicació preparada per a aquesta opció."}</p>
                </DoubleCard>
              ))}
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
}

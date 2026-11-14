"use client";

import { LedMatrix } from "@/components/app/led-matrix";
import { PageShell } from "@/components/marketing/page-shell";
import { DoubleCard, Eyebrow, Pill } from "@/components/ui/surface";
import { api, cap } from "@/lib/api";
import { useLive } from "@/lib/use-live";
import { cn } from "@/lib/utils";

// Sala de màquines: el que fa la placa ara mateix, per ensenyar-ho al jurat.
export default function Placa() {
  const { data: stats, error } = useLive(() => api.stats(), 3000);
  const { data: frame } = useLive(() => api.matrix(), 1000);

  const q = stats?.questions;
  const tiles: { label: string; value: string; note?: string; live?: boolean }[] = stats
    ? [
        { label: "On corre", value: stats.host },
        { label: "IA de la placa", value: stats.llm === "up" ? "Activa" : "No disponible", live: stats.llm === "up" },
        {
          label: "Memòria lliure",
          value: stats.memory ? `${stats.memory.available_mb.toLocaleString("ca")} MB` : "–",
          note: stats.memory ? `de ${stats.memory.total_mb.toLocaleString("ca")} MB` : "només a la placa (Linux)",
        },
        { label: "Contingut verificat", value: `${stats.bank.verified}`, note: `de ${stats.bank.prepared} problemes preparats` },
        { label: "Alumnes", value: `${stats.students}`, note: `${stats.attempts} respostes · ${stats.hints} ajudes` },
        {
          label: "IA: mediana",
          value: q?.median_seconds != null ? `${q.median_seconds.toLocaleString("ca")} s` : "encara cap",
          note: q?.worst_seconds != null ? `la més lenta: ${q.worst_seconds.toLocaleString("ca")} s` : undefined,
        },
        { label: "IA / reserva", value: q ? `${q.from_board} / ${q.fallback}` : "–", note: "preguntes de la placa i ajudes preparades" },
        { label: "Internet", value: "No cal", note: cap(stats.internet) },
      ]
    : [];

  return (
    <PageShell
      eyebrow="Sala de màquines"
      title={
        <>
          Què fa la placa <span className="text-gradient">ara mateix</span>
        </>
      }
      lead="S'actualitza cada 3 segons. Tot el que veus surt d'aquesta placa: cap servidor de fora."
      aside={<Pill className="px-2.5 py-1 text-[10px]">{error ? "Sense connexió" : "En directe"}</Pill>}
    >
      <div className="grid grid-cols-1 gap-px lg:grid-cols-[1fr_1.6fr]">
        <DoubleCard accent className="flex flex-col items-center justify-center gap-5 p-8 md:p-12">
          <LedMatrix matrix={frame?.matrix} dot={18} />
          <Eyebrow>La matriu de la placa</Eyebrow>
        </DoubleCard>
        <div className="grid grid-cols-2 gap-px">
          {tiles.map((t, i) => (
            <DoubleCard key={t.label} index={i} className="flex flex-col justify-between gap-4 p-5 md:p-6">
              <span className="flex items-center gap-2 text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
                {t.live !== undefined && (
                  <span className={cn("size-1.5 rounded-full", t.live ? "bg-success animate-pulse-soft" : "bg-black/20")} />
                )}
                {t.label}
              </span>
              <div>
                <p className="font-mono text-[clamp(20px,2.2vw,28px)] font-semibold tracking-[-0.02em] tabular-nums">{t.value}</p>
                {t.note && <p className="mt-1 text-[13px] leading-snug font-light text-muted-foreground">{t.note}</p>}
              </div>
            </DoubleCard>
          ))}
        </div>
      </div>
    </PageShell>
  );
}

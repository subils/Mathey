"use client";

import { ArrowRight, Check, Flame, Lightbulb, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { HoppingKangaroo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { DoubleCard, Eyebrow } from "@/components/ui/surface";
import { api, cap, type Profile } from "@/lib/api";
import { levelName } from "@/lib/school";
import { loadSession, saveSession } from "@/lib/session";
import { useStudent } from "@/lib/use-student";
import { cn } from "@/lib/utils";

const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${Math.round(x * 100)}%`);

export default function Progres() {
  const { session, onApiError } = useStudent();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState("");

  const student = session?.student;
  useEffect(() => {
    if (!student) return;
    api.profile(student).then((p) => {
      setProfile(p);
      // La barra de l'app llegeix la ratxa, el nivell i l'Elo de la sessió: es posen al dia
      const current = loadSession();
      if (current && (current.streak !== p.streak || current.level !== p.level || current.elo !== p.elo))
        saveSession({ ...current, streak: p.streak, level: p.level, elo: p.elo ?? current.elo });
    }, (e: Error) => {
      if (!onApiError(e)) setError(e.message);
    });
  }, [student, onApiError]);

  if (!session) return null;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-4 pt-10 pb-16 md:px-6">
      <header className="flex flex-col gap-2">
        <Eyebrow>El meu progrés</Eyebrow>
        <h1 className="text-[clamp(28px,4vw,44px)] leading-[1.08] font-medium tracking-[-0.03em]">
          Hola, <span className="text-gradient">{session.alias}</span>.
        </h1>
        <p className="text-[15px] font-light text-muted-foreground">
          Aquestes dades només són en aquesta placa. Cap servidor de fora les veu.
        </p>
      </header>

      {error && <p className="rounded-xl bg-destructive/[0.07] px-4 py-3 text-destructive">{error}</p>}
      {!profile && !error && (
        <div className="flex justify-center py-20">
          <HoppingKangaroo className="w-14" />
        </div>
      )}

      {profile && (
        <>
          <div className="grid grid-cols-2 gap-px md:grid-cols-4">
            {[
              { label: "Nivell", value: levelName(profile.level), mono: false },
              { label: "Elo", value: profile.elo !== undefined ? String(profile.elo) : "—", mono: true },
              { label: "Problemes", value: String(profile.attempts), mono: true },
              { label: "Al primer intent", value: pct(profile.accuracy), mono: true },
            ].map((t, i) => (
              <DoubleCard key={t.label} index={i} className="flex flex-col gap-6 p-6">
                <span className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">{t.label}</span>
                <span
                  className={cn(
                    "font-semibold tracking-[-0.02em] tabular-nums",
                    t.mono ? "font-mono text-[32px]" : "text-[22px] leading-tight",
                  )}
                >
                  {t.value}
                </span>
              </DoubleCard>
            ))}
          </div>

          <div className="grid gap-px md:grid-cols-[1.3fr_1fr]">
            <DoubleCard plain className="flex flex-col gap-5 p-6 md:p-8">
              <h2 className="text-lg font-medium">Per temes</h2>
              {profile.by_topic.length === 0 ? (
                <p className="text-muted-foreground">Encara no has fet cap problema.</p>
              ) : (
                <ul className="flex flex-col gap-4">
                  {profile.by_topic.map((t) => (
                    <li key={t.topic} className="flex flex-col gap-1.5">
                      <div className="flex justify-between text-[14px]">
                        <span>{cap(t.topic)}</span>
                        <span className="font-mono text-[13px] text-muted-foreground tabular-nums">
                          {t.correct}/{t.attempts} · {pct(t.accuracy)}
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-black/[0.06]">
                        <div
                          className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-soft))] transition-[width] duration-700 ease-motion-move"
                          style={{ width: pct(t.accuracy) }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </DoubleCard>

            <DoubleCard plain className="flex flex-col gap-5 p-6 md:p-8">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium">Últims problemes</h2>
                <span className="inline-flex items-center gap-1 font-mono text-[13px] text-orange-600">
                  <Flame className="size-3.5" /> {profile.streak}
                </span>
              </div>
              {profile.recent.length === 0 ? (
                <p className="text-muted-foreground">Encara cap.</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {profile.recent.map((r, i) => (
                    <li key={`${r.problem_id}-${i}`} className="flex items-center gap-3 text-[14px]">
                      <span
                        className={cn(
                          "flex size-6 shrink-0 items-center justify-center rounded-full",
                          r.correct ? "bg-success/12 text-success" : "bg-destructive/10 text-destructive",
                        )}
                      >
                        {r.correct ? <Check className="size-3.5" strokeWidth={3} /> : <X className="size-3.5" />}
                      </span>
                      <span className="flex-1 truncate">{cap(r.topic)}</span>
                      {r.hints_used > 0 && (
                        <span className="inline-flex items-center gap-0.5 text-[12px] text-muted-foreground">
                          <Lightbulb className="size-3" /> {r.hints_used}
                        </span>
                      )}
                      <span className="font-mono text-[12px] text-muted-foreground">niv. {r.level}</span>
                    </li>
                  ))}
                </ul>
              )}
            </DoubleCard>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button asChild size="lg">
              <Link href="/app/repte/">
                Continua practicant <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/app/xat/">Porta el teu problema</Link>
            </Button>
          </div>
        </>
      )}
    </main>
  );
}

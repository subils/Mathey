"use client";

import { ModeCards } from "@/components/app/mode-cards";
import { HoppingKangaroo, Mark } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { DoubleCard, Eyebrow } from "@/components/ui/surface";
import { api, type Health, type Session } from "@/lib/api";
import { GRADES, type Grade } from "@/lib/school";
import { clearSession, saveSession, useSession } from "@/lib/session";
import { cn } from "@/lib/utils";
import { ArrowLeft, ArrowRight, BookOpenText, Check, RotateCw, Type, WifiOff } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useState } from "react";

type Boot = "loading" | "ready" | "offline";

/** Mínim que es veu el cangur saltant, perquè l'entrada no faci pampallugues. */
const SPLASH_MS = 900;

export default function AppHome() {
  const session = useSession();
  const [boot, setBoot] = useState<Boot>("loading");
  const [health, setHealth] = useState<Health | null>(null);

  const probe = useCallback(() => {
    const started = performance.now();
    const settle = (next: Boot) =>
      setTimeout(() => setBoot(next), Math.max(0, SPLASH_MS - (performance.now() - started)));
    api.health().then(
      (h) => {
        setHealth(h);
        settle("ready");
      },
      () => settle("offline"),
    );
  }, []);

  useEffect(probe, [probe]);

  const retry = () => {
    setBoot("loading");
    probe();
  };

  if (boot === "loading" || session === undefined) return <Splash />;
  if (boot === "offline") return <Offline onRetry={retry} />;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pt-10 pb-16 md:px-6 md:pt-16">
      {session ? <Hub session={session} /> : <Onboarding health={health} />}
    </main>
  );
}

function Splash() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-5 pb-24">
      <HoppingKangaroo className="w-24 text-foreground" label="Engegant Mathey" />
      <p className="text-sm font-light text-muted-foreground">Connectant amb la placa…</p>
    </main>
  );
}

function Offline({ onRetry }: { onRetry: () => void }) {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 pb-24">
      <DoubleCard plain className="flex max-w-md flex-col items-center gap-4 p-10 text-center">
        <span className="flex size-12 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-black/5">
          <WifiOff className="size-5 text-muted-foreground" />
        </span>
        <h1 className="text-[22px] font-semibold tracking-[-0.02em]">No trobo la placa</h1>
        <p className="text-sm leading-relaxed font-light text-muted-foreground">
          Comprova que la placa està engegada i connectada a aquest ordinador. No cal internet.
        </p>
        <Button variant="default" size="lg" onClick={onRetry}>
          <RotateCw /> Torna-ho a provar
        </Button>
      </DoubleCard>
    </main>
  );
}

/* ------------------------------------------------------------------ */
/* Hub: l'alumne ja ha entrat                                          */
/* ------------------------------------------------------------------ */

function Hub({ session }: { session: Session }) {
  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-3">
        <Eyebrow>Benvingut de nou</Eyebrow>
        <h1 className="text-[clamp(30px,4.6vw,52px)] leading-[1.06] font-medium tracking-[-0.03em]">
          Hola, <span className="text-gradient">{session.alias}</span>.
          <br />
          Què fem avui?
        </h1>
        <div className="mt-1 flex flex-wrap gap-2 text-[13px]">
          {session.elo !== undefined && <Stat label="Elo" value={String(session.elo)} mono />}
          {session.easy_mode && <Stat label="Lectura" value="fàcil" />}
        </div>
      </header>
      <ModeCards />
      <button
        onClick={clearSession}
        className="self-center text-[13px] text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
      >
        No ets {session.alias}? Entra amb un altre nom
      </button>
    </div>
  );
}

function Stat({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-lg border border-black/[0.06] bg-white/70 px-2.5 py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn("font-medium", mono && "font-mono tabular-nums")}>{value}</span>
    </span>
  );
}

/* ------------------------------------------------------------------ */
/* Onboarding: quatre passos en una targeta que canvia d'alçada        */
/* ------------------------------------------------------------------ */

const STEPS = ["Nom", "Curs", "Lectura", "Mode"] as const;

function Onboarding({ health }: { health: Health | null }) {
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [alias, setAlias] = useState("");
  const [grade, setGrade] = useState<Grade>("6è");
  const [easy, setEasy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // L'alumne creat al pas 3. Es desa en triar el mode: si es desés abans, el
  // hub substituiria l'onboarding abans d'hora.
  const [pending, setPending] = useState<Session | null>(null);

  const go = (next: number) => {
    setDirection(next > step ? 1 : -1);
    setError("");
    setStep(next);
  };

  async function createStudent() {
    setBusy(true);
    setError("");
    try {
      setPending(await api.session(alias.trim(), grade, easy));
      go(3);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const commit = () => pending && saveSession(pending);

  return (
    <div
      className={cn(
        "mx-auto flex w-full flex-col items-center gap-8 transition-[max-width] duration-300 ease-motion-move",
        step === 3 ? "max-w-4xl" : "max-w-xl",
      )}
    >
      <div className="flex flex-col items-center gap-4 text-center">
        <Mark draw className="h-14 text-foreground" />
        <Progress step={step} />
      </div>

      <motion.div layout transition={{ layout: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } }} className="w-full">
        <DoubleCard plain className="overflow-hidden p-7 md:p-9">
          <AnimatePresence mode="popLayout" initial={false} custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              initial={{ opacity: 0, filter: "blur(4px)", x: direction * 16 }}
              animate={{ opacity: 1, filter: "blur(0px)", x: 0 }}
              exit={{ opacity: 0, filter: "blur(4px)", x: direction * -16, transition: { duration: 0.12 } }}
              transition={{ duration: 0.26, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col gap-6"
            >
              {step === 0 && (
                <form
                  className="flex flex-col gap-6"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (alias.trim()) go(1);
                  }}
                >
                  <StepTitle
                    eyebrow="Hola! Sóc Mathey"
                    title="Com et dic?"
                    text="Un sobrenom. No cal el teu nom real: tot es queda en aquesta placa."
                  />
                  <Input
                    autoFocus
                    value={alias}
                    onChange={(e) => setAlias(e.target.value)}
                    maxLength={30}
                    placeholder="Per exemple: Mathew"
                    aria-label="Sobrenom"
                    className="h-14 text-lg"
                  />
                  <Nav nextDisabled={!alias.trim()} />
                </form>
              )}

              {step === 1 && (
                <>
                  <StepTitle eyebrow="Pas 2 de 4" title={`Quin curs fas, ${alias.trim()}?`} text="Començaràs amb problemes del teu curs i el teu Elo s'anirà ajustant." />
                  <div className="grid grid-cols-2 gap-2.5">
                    {GRADES.map((g) => (
                      <Choice key={g.value} selected={grade === g.value} onClick={() => setGrade(g.value)}>
                        <span className="text-lg font-semibold tracking-tight">{g.label}</span>
                        <span className="text-[13px] text-muted-foreground">{g.long}</span>
                      </Choice>
                    ))}
                  </div>
                  <Nav onBack={() => go(0)} onNext={() => go(2)} />
                </>
              )}

              {step === 2 && (
                <>
                  <StepTitle eyebrow="Pas 3 de 4" title="Com t'agrada llegir?" text="Ho pots canviar quan vulguis des del menú." />
                  <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                    <Choice selected={!easy} onClick={() => setEasy(false)}>
                      <BookOpenText className="size-5 text-muted-foreground" />
                      <span className="font-semibold">Normal</span>
                      <span className="text-[13px] leading-snug text-muted-foreground">L&apos;enunciat original del Cangur, amb la figura.</span>
                    </Choice>
                    <Choice selected={easy} onClick={() => setEasy(true)}>
                      <Type className="size-5 text-muted-foreground" />
                      <span className="font-semibold">Lectura fàcil</span>
                      <span className="text-[13px] leading-snug text-muted-foreground">Frases curtes, una idea per línia i lletra més gran.</span>
                    </Choice>
                  </div>
                  {error && <p className="text-sm text-destructive">{error}</p>}
                  <Nav onBack={() => go(1)} onNext={createStudent} busy={busy} nextLabel="Som-hi" />
                </>
              )}

              {step === 3 && (
                <>
                  <StepTitle
                    eyebrow="Ja hi som"
                    title="Què vols fer?"
                    text={`${health?.problems ? `${health.problems} problemes del Cangur verificats` : "Problemes del Cangur"} o el teu propi problema.`}
                  />
                  <div onClickCapture={commit}>
                    <ModeCards compact />
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </DoubleCard>
      </motion.div>

      <p className="max-w-sm text-center text-[12px] leading-relaxed text-muted-foreground">
        Les teves respostes es guarden només en aquesta placa. No surten mai de l&apos;aula.
      </p>
    </div>
  );
}

function Progress({ step }: { step: number }) {
  return (
    <div className="flex items-center gap-1.5" aria-label={`Pas ${step + 1} de ${STEPS.length}`}>
      {STEPS.map((name, i) => (
        <span
          key={name}
          className={cn(
            "h-1.5 rounded-full transition-all duration-300 ease-motion-move",
            i < step ? "w-6 bg-foreground" : i === step ? "w-10 bg-accent" : "w-6 bg-black/10",
          )}
        />
      ))}
    </div>
  );
}

function StepTitle({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) {
  return (
    <div className="flex flex-col gap-2">
      <Eyebrow>{eyebrow}</Eyebrow>
      <h1 className="text-[clamp(26px,4vw,34px)] leading-[1.1] font-medium tracking-[-0.02em]">{title}</h1>
      <p className="text-[15px] leading-relaxed font-light text-muted-foreground">{text}</p>
    </div>
  );
}

function Choice({
  selected,
  children,
  ...props
}: React.ComponentProps<"button"> & { selected: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      className={cn(
        "relative flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-[border-color,background-color,box-shadow] duration-150 outline-none focus-visible:ring-3 focus-visible:ring-(--app-field-ring)",
        selected
          ? "border-accent bg-accent/[0.04] shadow-[0_0_0_3px_var(--app-field-ring)]"
          : "border-(--app-field-border) bg-(--app-field-bg) hover:border-(--app-field-border-hover)",
      )}
      {...props}
    >
      {selected && (
        <span className="absolute top-3 right-3 flex size-5 items-center justify-center rounded-full bg-accent text-white">
          <Check className="size-3" strokeWidth={3} />
        </span>
      )}
      {children}
    </button>
  );
}

function Nav({
  onBack,
  onNext,
  nextDisabled,
  busy,
  nextLabel = "Continua",
}: {
  onBack?: () => void;
  onNext?: () => void;
  nextDisabled?: boolean;
  busy?: boolean;
  nextLabel?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 pt-1">
      {onBack ? (
        <Button type="button" variant="ghost" size="lg" onClick={onBack}>
          <ArrowLeft /> Enrere
        </Button>
      ) : (
        <span />
      )}
      <Button
        type={onNext ? "button" : "submit"}
        size="lg"
        onClick={onNext}
        disabled={nextDisabled || busy}
        className="min-w-36"
      >
        {busy ? "Un moment…" : nextLabel} {!busy && <ArrowRight />}
      </Button>
    </div>
  );
}

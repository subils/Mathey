"use client";

import { useEffect, useState } from "react";
import { HoppingKangaroo } from "@/components/brand/logo";
import { TextShimmer } from "@/components/ui/text-shimmer";
import { cn } from "@/lib/utils";

/** Segons des que ha començat l'espera (s'actualitza cada 100 ms). */
export function useElapsed(running: boolean) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!running) return;
    const started = performance.now();
    const timer = setInterval(() => setSeconds((performance.now() - started) / 1000), 100);
    return () => {
      clearInterval(timer);
      setSeconds(0);
    };
  }, [running]);
  return seconds;
}

/**
 * «La placa està pensant»: el cangur saltant, el text amb brillantor i els
 * segons. A la placa, la IA triga de 10 a 40 s: cal que es vegi que treballa.
 */
export function Thinking({
  label = "La placa està pensant",
  hint,
  className,
}: {
  label?: string;
  hint?: string;
  className?: string;
}) {
  const seconds = useElapsed(true);
  return (
    <div className={cn("flex items-center gap-3", className)} aria-live="polite">
      <HoppingKangaroo className="w-9 text-foreground" label={label} />
      <div className="flex flex-col">
        <TextShimmer duration={2} className="text-[14px]">
          {label}
        </TextShimmer>
        <span className="font-mono text-[12px] text-muted-foreground tabular-nums">
          {seconds.toFixed(1)} s{hint && seconds > 8 ? ` · ${hint}` : ""}
        </span>
      </div>
    </div>
  );
}

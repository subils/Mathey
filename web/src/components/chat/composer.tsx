"use client";

// Compositor del xat. La lògica d'enganxar i arrossegar imatges segueix el
// patró de `prompt-input.tsx` de Vercel AI Elements (Apache-2.0): items del
// porta-retalls amb `getAsFile()`, comptador de profunditat en arrossegar
// perquè la capa no parpellegi, i un `<input type=file>` amagat.

import { ArrowUp, ImagePlus, Square, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { PromptInput, PromptInputTextarea } from "@/components/ui/prompt-input";
import { imageFromTransfer } from "@/lib/image";
import { cn } from "@/lib/utils";

const SPRING = { type: "spring" as const, visualDuration: 0.32, bounce: 0.25 };

export type ComposerProps = {
  value: string;
  onValueChange: (value: string) => void;
  onSubmit: () => void;
  /** Vista prèvia de la imatge adjunta (blob: o data:), o null. */
  image?: string | null;
  /** Mentre l'OCR la llegeix: brillantor per sobre de la miniatura. */
  imageBusy?: boolean;
  onImage?: (file: File) => void;
  onRemoveImage?: () => void;
  busy?: boolean;
  onStop?: () => void;
  placeholder?: string;
  /** Accepta imatges deixades a qualsevol lloc de la pàgina. */
  globalDrop?: boolean;
  autoFocus?: boolean;
  className?: string;
  canSubmit?: boolean;
};

export function Composer({
  value,
  onValueChange,
  onSubmit,
  image,
  imageBusy,
  onImage,
  onRemoveImage,
  busy,
  onStop,
  placeholder = "Escriu aquí…",
  globalDrop,
  autoFocus,
  className,
  canSubmit,
}: ComposerProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const depth = useRef(0);
  const ready = canSubmit ?? (value.trim().length > 0 || !!image);

  // Arrossegar una imatge a qualsevol lloc de la pàgina
  useEffect(() => {
    if (!globalDrop || !onImage) return;
    const hasFiles = (e: DragEvent) => Array.from(e.dataTransfer?.types ?? []).includes("Files");
    const enter = (e: DragEvent) => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      depth.current += 1;
      setDragging(true);
    };
    const over = (e: DragEvent) => hasFiles(e) && e.preventDefault();
    const leave = (e: DragEvent) => {
      if (!hasFiles(e)) return;
      depth.current = Math.max(0, depth.current - 1);
      if (depth.current === 0) setDragging(false);
    };
    const drop = (e: DragEvent) => {
      if (!hasFiles(e)) return;
      e.preventDefault();
      depth.current = 0;
      setDragging(false);
      const file = imageFromTransfer(e.dataTransfer);
      if (file) onImage(file);
    };
    window.addEventListener("dragenter", enter);
    window.addEventListener("dragover", over);
    window.addEventListener("dragleave", leave);
    window.addEventListener("drop", drop);
    return () => {
      window.removeEventListener("dragenter", enter);
      window.removeEventListener("dragover", over);
      window.removeEventListener("dragleave", leave);
      window.removeEventListener("drop", drop);
    };
  }, [globalDrop, onImage]);

  const onPaste = (e: React.ClipboardEvent) => {
    if (!onImage) return;
    const file = imageFromTransfer(e.clipboardData);
    if (file) {
      // Només s'atura si hi havia una imatge: enganxar text continua funcionant.
      e.preventDefault();
      onImage(file);
    }
  };

  return (
    <>
      <AnimatePresence>
        {dragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-white/50 p-6 backdrop-blur-md"
          >
            <motion.div
              initial={{ scale: 0.96 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.96 }}
              className="flex h-full max-h-[420px] w-full max-w-2xl flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-accent/50 bg-white/70"
            >
              <span className="flex size-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
                <ImagePlus className="size-6" />
              </span>
              <p className="text-lg font-medium">Deixa la foto aquí</p>
              <p className="text-sm font-light text-muted-foreground">La placa en llegirà el text</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div layout transition={{ layout: SPRING }} className={cn("relative w-full", className)}>
        <PromptInput
          value={value}
          onValueChange={onValueChange}
          onSubmit={() => ready && !busy && onSubmit()}
          isLoading={busy}
          maxHeight={220}
          className="glass rounded-[26px] border-white/80 p-2 shadow-[inset_0_1px_0_rgb(255_255_255/0.9),0_1px_2px_rgb(15_23_42/0.06),0_12px_40px_rgb(15_23_42/0.10)]"
        >
          <AnimatePresence initial={false} mode="popLayout">
            {image && (
              <motion.div
                key={image}
                layout
                initial={{ opacity: 0, scale: 0.6, filter: "blur(8px)" }}
                animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.6, filter: "blur(6px)", transition: { duration: 0.15 } }}
                transition={SPRING}
                className="relative m-1.5 mb-0 inline-block origin-bottom-left"
              >
                <div className="relative size-20 overflow-hidden rounded-2xl border border-black/[0.06] bg-muted shadow-sm">
                  {/* eslint-disable-next-line @next/next/no-img-element -- exportació estàtica: sense optimitzador */}
                  <img src={image} alt="Foto del problema" className="size-full object-cover" />
                  {imageBusy && <span className="shimmer absolute inset-0 bg-white/20" />}
                </div>
                {onRemoveImage && !imageBusy && (
                  <button
                    type="button"
                    onClick={onRemoveImage}
                    aria-label="Treu la foto"
                    className="absolute -top-1.5 -right-1.5 flex size-6 items-center justify-center rounded-full bg-foreground text-background shadow-md ring-2 ring-white transition-transform hover:scale-105"
                  >
                    <X className="size-3.5" strokeWidth={2.5} />
                  </button>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div layout="position">
            <PromptInputTextarea
              placeholder={placeholder}
              onPaste={onPaste}
              autoFocus={autoFocus}
              className="min-h-[52px] px-3 pt-3 text-[16px] leading-relaxed placeholder:text-(--app-field-placeholder)"
            />
          </motion.div>

          <motion.div layout="position" className="flex items-center justify-between gap-2 px-1 pt-1">
            <div className="flex items-center gap-1">
              {onImage && (
                <>
                  <button
                    type="button"
                    onClick={() => fileRef.current?.click()}
                    className="flex h-9 items-center gap-1.5 rounded-full px-3 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-black/5 hover:text-foreground"
                  >
                    <ImagePlus className="size-4" />
                    <span className="hidden sm:inline">Foto</span>
                  </button>
                  <input
                    ref={fileRef}
                    type="file"
                    // Sense image/heic: Safari convertiria les fotos a HEIC (WebKit 303803)
                    accept="image/png,image/jpeg,image/webp,image/*"
                    capture="environment"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) onImage(file);
                      e.target.value = "";
                    }}
                  />
                </>
              )}
            </div>
            {busy && onStop ? (
              <button
                type="button"
                onClick={onStop}
                aria-label="Atura"
                className="flex size-9 items-center justify-center rounded-full bg-foreground text-background transition-opacity hover:opacity-90"
              >
                <Square className="size-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={onSubmit}
                disabled={!ready || busy}
                aria-label="Envia"
                className="flex size-9 items-center justify-center rounded-full bg-foreground text-background transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-95 disabled:bg-black/15 disabled:text-white"
              >
                <ArrowUp className="size-4.5" strokeWidth={2.5} />
              </button>
            )}
          </motion.div>
        </PromptInput>
      </motion.div>
    </>
  );
}

"use client";

import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";

const SCENE = "/static/cube.splinecode";
const WASM = "/spline";

type State = "loading" | "ready" | "fallback";

export function ResendCube({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [state, setState] = useState<State>("loading");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let disposed = false;
    let app: { dispose: () => void } | null = null;

    (async () => {
      try {
        // Es carrega a part: no alenteix la resta de la landing
        const { Application } = await import("@splinetool/runtime");
        if (disposed) return;
        // WebGL sempre: amb WebGPU (que el motor tria sol si el navegador en té) el cub
        // sortia en blanc de manera intermitent a Safari
        const instance = new Application(canvas, { wasmPath: WASM, renderer: "webgl" });
        app = instance;
        await instance.load(SCENE);
        if (!disposed) setState("ready");
      } catch {
        // Sense WebGL o l'escena no es pot carregar: el bucle de vídeo
        if (!disposed) setState("fallback");
      }
    })();

    return () => {
      disposed = true;
      app?.dispose();
    };
  }, []);

  return (
    <div className={cn("relative", className)}>
      <canvas
        ref={canvasRef}
        aria-label="Cub 3D"
        className={cn(
          "absolute inset-0 size-full transition-opacity duration-700 ease-out",
          state === "ready" ? "opacity-100" : "opacity-0",
          state === "fallback" && "hidden",
        )}
      />
      {state === "fallback" && (
        <div className="absolute inset-0 flex items-center justify-center mix-blend-lighten">
          <video
            autoPlay
            loop
            muted
            playsInline
            poster="/static/cube-fallback.jpg"
            width={400}
            height={400}
            className="size-[min(100%,400px)] object-contain"
          >
            <source src="/static/cube.mp4" type="video/mp4" />
          </video>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

/**
 * Consulta la placa cada `everyMs` mentre la pestanya és visible. Si falla,
 * `data` es queda amb l'últim valor bo i `error` passa a true.
 */
export function useLive<T>(fetcher: () => Promise<T>, everyMs = 4000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () => {
      if (document.visibilityState !== "visible") return;
      fetcher().then(
        (value) => alive && (setData(value), setError(false)),
        () => alive && setError(true),
      );
    };
    load();
    const timer = setInterval(load, everyMs);
    document.addEventListener("visibilitychange", load);
    return () => {
      alive = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", load);
    };
    // El fetcher es crea a cada render: només es vol una subscripció
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [everyMs]);

  return { data, error };
}

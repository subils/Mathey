"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect } from "react";
import { isUnknownStudent } from "./api";
import { clearSession, useSession } from "./session";

/**
 * La sessió de l'alumne per a les pantalles de l'app. Sense sessió, torna a
 * l'onboarding (/app/). `onApiError` reconeix l'error «alumne desconegut» (la
 * placa s'ha reiniciat amb una state.db nova): esborra la sessió i hi torna.
 */
export function useStudent() {
  const router = useRouter();
  const session = useSession();

  useEffect(() => {
    if (session === null) router.replace("/app/");
  }, [session, router]);

  const onApiError = useCallback(
    (error: unknown) => {
      if (isUnknownStudent(error)) {
        clearSession();
        router.replace("/app/");
        return true;
      }
      return false;
    },
    [router],
  );

  return { session, onApiError };
}

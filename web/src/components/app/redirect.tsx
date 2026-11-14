"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Ruta antiga → ruta nova, conservant la query (?id=…). L'exportació estàtica no té redireccions de servidor. */
export function Redirect({ to }: { to: string }) {
  const router = useRouter();
  useEffect(() => {
    router.replace(to + window.location.search);
  }, [router, to]);
  return null;
}

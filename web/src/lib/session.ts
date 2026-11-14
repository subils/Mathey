"use client";

import { useSyncExternalStore } from "react";
import type { Session } from "./api";

// L'alumne es guarda al navegador només per no haver d'entrar cada vegada.
// Les dades de veritat (intents, Elo) viuen a la placa: aquí només n'hi ha una còpia.
const KEY = "mathey-session";
const listeners = new Set<() => void>();

let cachedRaw: string | null = null;
let cachedSession: Session | null = null;

function read(): string | null {
  try {
    return window.localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export function loadSession(): Session | null {
  const raw = read();
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    try {
      cachedSession = raw ? (JSON.parse(raw) as Session) : null;
    } catch {
      cachedSession = null;
    }
  }
  return cachedSession;
}

function notify() {
  listeners.forEach((listener) => listener());
}

export function saveSession(session: Session) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify({ ...session, matrix: undefined }));
  } catch {
    /* sense emmagatzematge: només caldrà tornar a entrar */
  }
  notify();
}

export function clearSession() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* res */
  }
  notify();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/** La sessió guardada. `undefined` mentre es renderitza fora del navegador. */
export function useSession(): Session | null | undefined {
  return useSyncExternalStore(subscribe, loadSession, () => undefined);
}

/** Segons des d'un instant, fora del render (per al temps de resposta). */
export const now = () => performance.now();

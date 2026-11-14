// Cursos i nivells. Les cadenes de GRADES han de coincidir exactament amb
// GRADE_LEVEL de mentor/config.py (el backend les valida).
export const GRADES = [
  { value: "5è", label: "5è", long: "5è de primària" },
  { value: "6è", label: "6è", long: "6è de primària" },
  { value: "1r ESO", label: "1r ESO", long: "1r d'ESO" },
  { value: "2n ESO", label: "2n ESO", long: "2n d'ESO" },
] as const;

export type Grade = (typeof GRADES)[number]["value"];

/** Nivell del mentor (0–3) → nom del curs. */
export const LEVEL_NAMES = GRADES.map((g) => g.long);

export const levelName = (level: number | null | undefined) =>
  level === null || level === undefined ? "—" : (LEVEL_NAMES[level] ?? `nivell ${level}`);

export const MAX_LEVEL = 3;

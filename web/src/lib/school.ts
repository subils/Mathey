// Cursos. Les cadenes de GRADES han de coincidir exactament amb GRADE_LEVEL de
// mentor/config.py (el backend les valida). El curs només fixa l'Elo inicial.
export const GRADES = [
  { value: "5è", label: "5è", long: "5è de primària" },
  { value: "6è", label: "6è", long: "6è de primària" },
  { value: "1r ESO", label: "1r ESO", long: "1r d'ESO" },
  { value: "2n ESO", label: "2n ESO", long: "2n d'ESO" },
] as const;

export type Grade = (typeof GRADES)[number]["value"];

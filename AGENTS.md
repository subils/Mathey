# Regles del projecte — Mathey (Datathon FME 2026, repte Qualcomm)

Per a qualsevol persona o agent que toqui aquest repo. Llegeix primer
[docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) i [docs/ROADMAP.md](docs/ROADMAP.md).

## Regles que no es trenquen

1. **Tot corre a la placa i sense xarxa.** Cap servei al núvol al producte: ni
   Vercel, ni Supabase, ni CDN, ni fonts remotes, ni analítica. La demo es fa
   amb el Wi-Fi apagat.
2. **Cap dada de M3Kang al repo.** Ni `train.jsonl`, ni `val.jsonl`, ni imatges,
   ni bases de dades amb el text dels problemes. La llicència és només per a recerca.
3. **`predict.py` no es trenca.** Una lletra A–E per problema, 60 s com a màxim,
   sense xarxa, determinista. El mentor i l'app viuen a part de `copilot/`.
4. **El model no és font de veritat matemàtica.** No resol ni explica solucions.
   Tot el text que genera passa un control per codi abans d'arribar a l'alumne.
5. **En directe, tot passa a la placa.** El contingut per endavant (pistes,
   solucions, trampes, temes, versions fàcils) el generen agents al portàtil i
   es guarda a la placa; tot el que es genera durant la sessió de l'alumne surt
   del model de la placa. Cap contingut sense verificar arriba a l'alumne.
6. **Cada número que es publica ve d'una execució registrada**, amb el seu commit.
7. **La documentació es manté al dia en el mateix canvi** que toca el comportament.

## Ordres del fundador

- 14/11/2026: el frontend és Next.js amb exportació estàtica servit per la placa,
  i les dades són SQLite a la placa. Decisió aprovada després de descartar
  Vercel i Supabase per incompatibles amb l'enunciat.
- 14/11/2026: l'objectiu és guanyar el repte; el pla de 24 hores és a `docs/ROADMAP.md`.
- 14/11/2026, ~13:40: els mentors han donat el vistiplau (segons l'equip) a
  preparar les pistes fora de la placa. Les genera un agent; ho porta Subils
  (zona Dades i lògica). La definició del producte és a `docs/PRODUCTE.md`.
- 14/11/2026: el material per a l'equip, en català planer i sense palla; Notion
  amb poques pàgines, cadascuna justificada.
- 14/11/2026, 18:20: **el producte es diu Mathey** (abans «Mentor Cangur»). El
  paquet Python continua sent `mentor/`.
- 14/11/2026, 18:20: segons el fundador, l'equip **té autorització, de moment,
  per tenir públics els fitxers amb problemes de M3Kang** que hi ha al
  repositori (`data/problems_elo.json`). La regla 2 queda en suspens per a aquests
  fitxers; abans de publicar-ne de nous o de l'entrega final, torneu-ho a confirmar.
- 14/11/2026: tot el projecte viu en un únic repositori GitHub, `Mathey`, amb
  l'arrel local a `/Users/gsubils/Desktop/Mathey`; no es creen repositoris Git
  ni submòduls dins de cap subcarpeta.
- 14/11/2026, 18:40: **cada canvi es fa commit i push de seguida** (abans fer
  `git pull --rebase`), perquè els companys treballen sobre el mateix repositori
  i han de tenir sempre la versió al dia.

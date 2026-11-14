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
- 14/11/2026, ~19:00: **al mode 2 (xat «Porta el teu problema») la IA de la
  placa intenta resoldre el problema propi de l'alumne** i l'acosta pas a pas a
  una solució final. És una excepció a la regla 4 **limitada a aquest mode**: la
  web ho presenta sempre com a «proposta de la IA de la placa, pot equivocar-se».
  Al Repte Cangur (mode 1) la regla 4 es manté sencera.
- 14/11/2026, ~19:00: **frontend nou amb el llenguatge visual de Faktu**
  (`~/Desktop/Faktu`).
  - Mode clar, vidre i tipografia Geist (local).
  - Landing a `/`, servida només per la placa; l'app és a `/app/`.
  - Aceternity UI: **només components gratuïts**, sense comprar All-Access.
- 14/11/2026, ~19:30: **de moment s'elimina per complet tota la funcionalitat
  per al professor**: vista del mestre, secció de la landing i `GET /api/teacher`.
  El producte és només per a l'alumne.
- 14/11/2026, ~19:30: **sense placa, la web ha de funcionar igualment en «mode
  demo»**, i ho ha d'indicar. Ha de ser navegable sencera per poder dissenyar.
  Ho fa `web/src/lib/demo.ts`, amb problemes inventats, no de M3Kang.
- 14/11/2026, ~21:30: **l'avís del mode demo ha de ser discret**: res d'insígnies
  taronges. El logo dels navbars porta «BETA» en molt petit a baix a la dreta, i
  en mode demo aquesta etiqueta és la que s'explica en clicar-hi.
- 14/11/2026, ~20:00: segons el fundador, **Resend ha autoritzat l'equip a fer
  servir el disseny de resend.com**, inclòs el cub 3D del seu hero.
  - Els fitxers originals són a `web/public/static/`: `cube.splinecode`, `cube.mp4`,
    `cube-fallback.jpg`, `texture-btn.png` i `landing-page/` (`bg-hero-1.jpg`,
    `bg-light.avif`).
  - El primer requadre de la landing és el hero de Resend tal qual: fons negre,
    les seves capes de llum i el seu CSS (`globals.css`, bloc «Hero de resend.com»).
  - Es pinten amb `@splinetool/runtime`; els `.wasm` són a `web/public/spline/`,
    sense CDN.
  - Crèdit al peu de la landing.
- 14/11/2026, ~20:30: **el color principal és el taronja**, no el blau.
- 14/11/2026, ~20:45: **tots els tons de taronja surten de zernio.com**: marca `#eb3514`
  (hover `#d12c0e`) i la gamma del seu degradat, del `#fff5e6` al `#3b0d02`
  (`globals.css`).
- 14/11/2026, ~20:45: **el cangur no salta ni sura**: sempre quiet (treu
  professionalitat). Només el carregador el fa saltar mentre s'espera.
- 14/11/2026, ~20:30: **la matriu LED no es mostra a la web** (ni a la landing ni a
  l'app): només es veu a l'Arduino.
- 14/11/2026, ~20:30: **landing amb poc text i molt aire**: textos curts (si es pot
  explicar en 3 passos, no en 6), components separats i il·lustracions abstractes
  animades, al nivell de Faktu.
- 14/11/2026, 18:40: **cada canvi es fa commit i push de seguida** (abans fer
  `git pull --rebase`), perquè els companys treballen sobre el mateix repositori
  i han de tenir sempre la versió al dia.

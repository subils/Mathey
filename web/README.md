# Mathey — la web

Next.js 16 amb **exportació estàtica** (`output: 'export'`). La serveix la placa
(port 7000) i funciona **sense internet**: cap CDN, cap font remota, cap analítica.
Totes les dades venen de `/api` (el mentor en Python). Contracte:
[docs/ARQUITECTURA.md §5](../docs/ARQUITECTURA.md).

## Engegar-la

```bash
python3 scripts/dev_server.py   # (des de l'arrel) API a http://127.0.0.1:7000; també serveix web/out
pnpm dev                        # web a http://localhost:3000, crida l'API del 7000
pnpm build                      # exporta a web/out (és el que es desplega a la placa)
pnpm lint
```

Al Mac, feu servir `127.0.0.1` i no `localhost:7000` (AirPlay escolta al 7000).

## Rutes

| Ruta | Què és |
|---|---|
| `/` | Landing (pitch i aula) |
| `/app/` | Onboarding o hub |
| `/app/repte/` | Mode 1 · Repte Cangur (`?id=` opcional) |
| `/app/xat/` | Mode 2 · Porta el teu problema (la IA resol pas a pas, en streaming) |
| `/app/progres/` | Progrés de l'alumne |
| `/placa/` | Sala de màquines |

## Mode demo (sense placa)

Si l'API no respon, la web passa sola al **mode demo**: `src/lib/demo.ts` fa de
backend dins del navegador, amb el mateix contracte que `/api`.
- Fa servir 8 problemes inventats per nosaltres (no de M3Kang).
- L'Elo, les ajudes, la matriu, l'OCR i el xat són simulats.
- A la barra surt «Mode demo» (`components/app/demo-badge.tsx`); en clicar-hi es
  pot tornar a buscar la placa.
- `?demo=1` el força.

Així es pot navegar i dissenyar sense l'Arduino: n'hi ha prou amb `pnpm dev`, sense
`dev_server.py`.

## Disseny

Llenguatge visual de **Faktu** (`~/Desktop/Faktu`), en mode clar.

- **Tokens:** `src/app/globals.css`.
  - Colors: fons `#f0f1f0`, tinta `#1a1a1a`, accent `#0171e3`.
  - Radis i moviment, i el degradat superior del `body`.
- **Materials:**
  - `.navbar-glass` (el navbar de Faktu) i `.glass` (compositor, xips): blur + saturate i una llum interior.
  - `DoubleCard` (`components/ui/surface.tsx`): la targeta de doble capa de Faktu, amb els gradients malva i sàlvia.
- **Tipografia:** Geist Sans i Geist Mono amb el paquet `geist` (`next/font/local`).
  - Titulars amb tracking negatiu.
  - Entradetes en pes 300.
  - Etiquetes superiors a 10 px en majúscules.
- **Moviment:** «sense talls, però ràpid», amb la corba `cubic-bezier(.16,1,.3,1)`.
  - `Reveal` a la landing.
  - `motion` a l'app.
  - Es respecta `prefers-reduced-motion`.
- **Cap emoji a la interfície.** Icones de `lucide-react`.
- **El cangur:** `components/brand/` (separat de `branding/Mathey logo.svg`). `HoppingKangaroo` és el carregador.

## On és cada cosa

| Carpeta | Contingut |
|---|---|
| `src/lib/api.ts` | L'únic lloc que sap on és l'API. `ownChat` llegeix l'NDJSON del xat |
| `src/lib/session.ts`, `use-student.ts` | Sessió de l'alumne al navegador; si la placa no el coneix, torna a l'onboarding |
| `src/components/app/` | Barra de l'app, targetes de mode, matriu LED |
| `src/components/chat/` | Compositor (enganxar, arrossegar, càmera), markdown amb KaTeX, «la placa està pensant» |
| `src/components/marketing/` | Navbar, hero i seccions de la landing |
| `src/components/ui/` | Botó, camps, superfícies; prompt-kit (MIT) i Aceternity (només gratuïts) |

## Regles

- No importeu mai `data/problems_elo.json` ni cap respost a la web: la resposta
  correcta no viatja al navegador fins que l'alumne l'encerta o demana el graó 5.
- Sense `next/image` (no hi ha servidor), sense `next/font/google`, sense rutes
  dinàmiques (l'`id` va a la query).

/* eslint-disable @next/next/no-img-element -- exportació estàtica: sense optimitzador d'imatges */
import { ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { ResendCube } from "./resend-cube";

/**
 * Hero: el marc de Faktu (8–12 px al voltant d'un panell arrodonit) amb el hero
 * - fons #000 amb les seves dues capes de llum, amb les mateixes classes i màscares:
 *   «Floor background» (bg-hero-1.jpg, opacity-80) i «Light ray background»
 *   (bg-light.avif, -top-20), totes dues des de `md`;
 * - text a l'esquerra amb el degradat i els grisos del seu tema fosc, la píndola
 *   «rainbow-border» i el botó de vidre amb textura;
 * - el seu cub 3D a la dreta (a dalt al mòbil).
 */
export function Hero() {
  return (
    <section id="hero" className="relative h-[100svh] min-h-[640px] w-full">
      <div className="relative h-full w-full p-2 md:p-3">
        <div className="relative isolate h-full w-full overflow-hidden rounded-2xl bg-[#000] text-[#f0f0f0]">
          <img
            alt=""
            aria-hidden
            width={1920}
            height={1080}
            decoding="async"
            src="/static/landing-page/bg-hero-1.jpg"
            className="pointer-events-none absolute top-0 right-0 left-0 mx-auto hidden h-screen w-full opacity-80 transition-opacity duration-500 select-none md:block"
            style={{ maskImage: "linear-gradient(to top, transparent 15%, black 25%)", maskComposite: "exclude" }}
          />
          <img
            alt=""
            aria-hidden
            width={1920}
            height={1080}
            decoding="async"
            src="/static/landing-page/bg-light.avif"
            className="pointer-events-none absolute -top-20 right-0 left-0 mx-auto hidden h-screen w-full transition-all duration-500 select-none md:block"
            style={{ maskImage: "linear-gradient(to top, transparent 15%, black 25%)", maskComposite: "exclude" }}
          />

          <div className="relative z-20 mx-auto flex h-full max-w-5xl flex-col items-center justify-start px-6 pt-24 pb-8 md:max-w-7xl md:flex-row md:justify-between md:pt-16 md:pb-12">
            <div className="order-2 max-w-3xl origin-[center_left] animate-hero-text-slide-up-fade sm:shrink-0 md:order-1 lg:pl-16">
              <div className="flex items-center justify-center md:inline-flex">
                <Link
                  href="/#com-funciona"
                  className="rainbow-border relative mb-8 inline-flex items-center justify-center rounded-full text-sm leading-none after:absolute after:inset-0 after:-z-10 after:block after:rounded-full"
                >
                  <span className="m-[1px] inline-flex items-center gap-1 rounded-full px-3 py-1 whitespace-nowrap">
                    Datathon FME 2026
                    <ChevronRight className="size-3" strokeWidth={2.5} />
                  </span>
                </Link>
              </div>

              <h1 className="effect-font-styling effect-font-gradient relative pb-3 text-center text-[2.875rem] leading-[100%] font-medium tracking-[-0.035em] sm:text-[4rem] md:text-left md:text-[5rem] lg:text-[6rem]">
                Matemàtiques
                <br />
                socràtiques
              </h1>
              <p className="relative mt-2 mb-8 max-w-[30rem] text-center text-base leading-7 font-normal text-[#a1a4a5] md:text-left md:text-[1.125rem] md:leading-[1.5]">
                Com Sòcrates, no et donem la resposta: et fem la pregunta justa perquè la trobis tu.
              </p>
              <div className="flex flex-col justify-center gap-4 md:flex-row md:justify-start">
                <Link
                  href="/app/"
                  className="relative inline-flex h-12 items-center justify-center gap-1 rounded-2xl border-[2px] border-white/5 bg-[linear-gradient(104deg,rgba(253,253,253,0.05)_5%,rgba(240,240,228,0.1)_100%)] bg-origin-border px-5 text-base font-semibold text-white shadow-sm backdrop-blur-[25px] transition-all duration-200 ease-in-out select-none after:pointer-events-none after:absolute after:top-[-2px] after:left-[-2px] after:h-[calc(100%+4px)] after:w-[calc(100%+4px)] after:rounded-[1rem] after:bg-[url('/static/texture-btn.png')] after:bg-repeat hover:bg-white/90 hover:text-black hover:shadow-button focus-visible:bg-white/90 focus-visible:text-black focus-visible:ring-4 focus-visible:ring-white/30 focus-visible:outline-hidden"
                >
                  Comença
                </Link>
                <Link
                  href="/#com-funciona"
                  className="relative inline-flex h-12 items-center justify-center gap-1 rounded-2xl border border-transparent bg-transparent px-5 text-base font-semibold text-[#a1a4a5] transition duration-200 ease-in-out select-none hover:text-[#f0f0f0] focus-visible:ring-4 focus-visible:ring-white/10 focus-visible:outline-hidden"
                >
                  Com funciona
                </Link>
              </div>
            </div>

            <div className="order-1 md:order-2 md:ml-10 md:max-w-[700px] md:min-w-0 md:flex-1">
              <ResendCube className="h-[240px] w-[240px] md:h-[550px] md:w-full" />
            </div>
          </div>

          <div className="absolute inset-x-0 bottom-6 z-20 hidden justify-center md:flex">
            <ChevronDown className="size-5 animate-bounce text-white/40" />
          </div>
        </div>
      </div>
    </section>
  );
}

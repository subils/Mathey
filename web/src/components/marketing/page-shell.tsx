import { Eyebrow } from "@/components/ui/surface";
import { SiteFooter } from "./sections";
import { SiteNavbar } from "./site-navbar";

/** Pàgines públiques fora del producte (/placa/): el navbar i el peu de la landing. */
export function PageShell({
  eyebrow,
  title,
  lead,
  aside,
  children,
}: {
  eyebrow: string;
  title: React.ReactNode;
  lead?: React.ReactNode;
  aside?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-svh overflow-x-clip">
      <SiteNavbar />
      <main className="mx-auto w-full max-w-7xl px-6 pt-32 md:px-10 md:pt-40 lg:px-14">
        <header className="mb-10 flex flex-wrap items-end justify-between gap-6 md:mb-14">
          <div className="flex max-w-2xl flex-col gap-3">
            <Eyebrow>{eyebrow}</Eyebrow>
            <h1 style={{ fontSize: "clamp(30px, 4.4vw, 56px)", fontWeight: 500, letterSpacing: "-0.03em", lineHeight: 1.05 }}>
              {title}
            </h1>
            {lead && <p className="text-[15px] leading-relaxed font-light text-muted-foreground md:text-base">{lead}</p>}
          </div>
          {aside}
        </header>
        {children}
      </main>
      <SiteFooter />
    </div>
  );
}

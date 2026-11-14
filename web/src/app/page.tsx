import { Hero } from "@/components/marketing/hero";
import {
  BoardSection,
  FinalCta,
  HowSection,
  ModesSection,
  SectionDivider,
  SiteFooter,
  TeacherSection,
  TrustBar,
} from "@/components/marketing/sections";
import { SiteNavbar } from "@/components/marketing/site-navbar";

// Landing de Mathey. La serveix la placa, com tota la web: sense internet.
// El producte és a /app/ (onboarding i els dos modes).
export default function Landing() {
  return (
    <div className="min-h-svh overflow-x-clip">
      <SiteNavbar />
      <main>
        <Hero />
        <TrustBar />
        <SectionDivider />
        <HowSection />
        <SectionDivider />
        <ModesSection />
        <SectionDivider />
        <BoardSection />
        <SectionDivider />
        <TeacherSection />
        <SectionDivider />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}

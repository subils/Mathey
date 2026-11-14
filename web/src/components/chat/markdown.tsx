"use client";

import "katex/dist/katex.min.css"; // les fonts de KaTeX s'empaqueten amb la web: sense xarxa
import { createMathPlugin } from "@streamdown/math";
import { Streamdown } from "streamdown";
import { cn } from "@/lib/utils";

// `$…$` dins del text: la IA escriu així les fórmules (prompt de mentor/llm.py).
const plugins = { math: createMathPlugin({ singleDollarTextMath: true }) };

/** Markdown amb fórmules. Amb `streaming`, tanca el que quedi obert a mig tros. */
export function Markdown({
  children,
  streaming = false,
  className,
}: {
  children: string;
  streaming?: boolean;
  className?: string;
}) {
  return (
    <Streamdown
      plugins={plugins}
      mode={streaming ? "streaming" : "static"}
      isAnimating={streaming}
      controls={false}
      className={cn(
        "text-[15.5px] leading-relaxed [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-2 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0 [&_strong]:font-semibold [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1",
        className,
      )}
    >
      {children}
    </Streamdown>
  );
}

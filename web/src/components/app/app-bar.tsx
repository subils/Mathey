"use client";

import { ChevronDown, Flame, LineChart, LogOut, Type } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Mark } from "@/components/brand/logo";
import { DemoBadge } from "./demo-badge";
import { cn } from "@/lib/utils";
import { clearSession, saveSession, useSession } from "@/lib/session";

const MODES = [
  { href: "/app/repte/", label: "Repte Cangur", short: "Repte" },
  { href: "/app/xat/", label: "El meu problema", short: "El meu" },
];

/**
 * Barra de l'app: mínima a propòsit. L'alumne no veu la sala de màquines.
 * Esquerra: el cangur (torna al hub). Centre: el mode. Dreta: ratxa i menú.
 */
export function AppBar() {
  const session = useSession();
  const pathname = usePathname() ?? "";

  return (
    <header className="sticky top-0 z-40 px-3 pt-3 md:px-4">
      <nav className="navbar-glass scrolled mx-auto flex h-[52px] max-w-5xl items-center justify-between gap-2 px-2 md:px-3">
        <Link
          href="/app/"
          className="flex shrink-0 items-center gap-2 rounded-lg px-1.5 py-1 text-foreground transition-colors hover:bg-black/5"
          aria-label="Mathey, inici"
        >
          <Mark className="h-7" />
          <span className="hidden text-[15px] font-semibold tracking-tight sm:inline">Mathey</span>
        </Link>

        {session && <ModeSwitch pathname={pathname} />}

        <div className="flex shrink-0 items-center gap-1.5">
          <DemoBadge />
          {session ? (
            <>
              <StreakChip streak={session.streak ?? 0} />
              <StudentMenu />
            </>
          ) : (
            <Link
              href="/"
              className="rounded-lg px-3 py-1.5 text-[14px] font-medium text-muted-foreground transition-colors hover:bg-black/5 hover:text-foreground"
            >
              Què és Mathey?
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}

function ModeSwitch({ pathname }: { pathname: string }) {
  return (
    <div className="relative flex rounded-xl bg-black/[0.045] p-1" role="tablist" aria-label="Mode">
      {MODES.map((mode) => {
        const active = pathname.startsWith(mode.href.replace(/\/$/, ""));
        return (
          <Link
            key={mode.href}
            href={mode.href}
            role="tab"
            aria-selected={active}
            className={cn(
              "relative z-10 rounded-lg px-3 py-1.5 text-[13px] font-medium whitespace-nowrap transition-colors sm:px-4 sm:text-[14px]",
              active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {active && (
              <motion.span
                layoutId="mode-pill"
                className="absolute inset-0 -z-10 rounded-lg bg-white shadow-[0_1px_2px_rgba(0,0,0,0.06),0_2px_8px_rgba(0,0,0,0.04)]"
                transition={{ type: "spring", visualDuration: 0.28, bounce: 0.15 }}
              />
            )}
            <span className="sm:hidden">{mode.short}</span>
            <span className="hidden sm:inline">{mode.label}</span>
          </Link>
        );
      })}
    </div>
  );
}

function StreakChip({ streak }: { streak: number }) {
  return (
    <span
      title="Ratxa d'encerts al primer intent"
      className={cn(
        "hidden items-center gap-1 rounded-lg px-2 py-1 font-mono text-[13px] font-medium tabular-nums transition-colors sm:inline-flex",
        streak > 0 ? "bg-orange-500/10 text-orange-600" : "text-muted-foreground",
      )}
    >
      <Flame className="size-3.5" />
      {streak}
    </span>
  );
}

function StudentMenu() {
  const session = useSession();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !ref.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  if (!session) return null;
  const initial = session.alias.trim()[0]?.toUpperCase() ?? "?";

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-1.5 rounded-lg py-1 pr-1.5 pl-1 transition-colors hover:bg-black/5 aria-expanded:bg-black/5"
      >
        <span className="flex size-7 items-center justify-center rounded-full bg-foreground text-[13px] font-semibold text-background">
          {initial}
        </span>
        <span className="hidden max-w-28 truncate text-[14px] font-medium md:inline">{session.alias}</span>
        <ChevronDown className="size-3.5 text-muted-foreground" />
      </button>

      <div
        role="menu"
        data-open={open}
        className={cn(
          "absolute top-[calc(100%+8px)] right-0 w-60 origin-top-right rounded-xl border border-black/[0.06] bg-popover p-1.5 shadow-(--app-popup-shadow) transition-[opacity,scale] duration-150 ease-motion-enter",
          open ? "scale-100 opacity-100" : "pointer-events-none scale-[0.96] opacity-0",
        )}
      >
        <div className="px-2.5 pt-1.5 pb-2">
          <p className="truncate text-[14px] font-semibold">{session.alias}</p>
          <p className="text-[12px] text-muted-foreground">
            {session.grade}
            {session.elo !== undefined && <> · Elo <span className="font-mono">{session.elo}</span></>}
          </p>
        </div>
        <div className="my-1 h-px bg-border/70" />
        <MenuItem
          icon={<LineChart />}
          onClick={() => {
            setOpen(false);
            router.push("/app/progres/");
          }}
        >
          El meu progrés
        </MenuItem>
        <MenuItem
          icon={<Type />}
          role="menuitemcheckbox"
          aria-checked={session.easy_mode}
          onClick={() => saveSession({ ...session, easy_mode: !session.easy_mode })}
        >
          <span className="flex-1">Lectura fàcil</span>
          <span
            className={cn(
              "relative h-5 w-9 rounded-full transition-colors",
              session.easy_mode ? "bg-accent" : "bg-black/15",
            )}
          >
            <span
              className={cn(
                "absolute top-0.5 left-0.5 size-4 rounded-full bg-white shadow-sm transition-transform duration-150 ease-motion-move",
                session.easy_mode && "translate-x-4",
              )}
            />
          </span>
        </MenuItem>
        <div className="my-1 h-px bg-border/70" />
        <MenuItem
          icon={<LogOut />}
          onClick={() => {
            clearSession();
            router.push("/app/");
          }}
        >
          Surt
        </MenuItem>
      </div>
    </div>
  );
}

function MenuItem({
  icon,
  children,
  ...props
}: React.ComponentProps<"button"> & { icon: React.ReactNode }) {
  return (
    <button
      role="menuitem"
      className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-[14px] transition-colors hover:bg-black/[0.045] [&_svg]:size-4 [&_svg]:text-muted-foreground"
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}

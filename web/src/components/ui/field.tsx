import { cn } from "@/lib/utils";

// Camps de Faktu (components/ui/campo.ts): fons gairebé blanc que passa a blanc
// en enfocar, vora d'accent i anell d'accent al 20 %.
export const fieldBox =
  "rounded-xl border border-(--app-field-border) bg-(--app-field-bg) text-foreground shadow-(--app-field-shadow) transition-[border-color,background-color,box-shadow] outline-none hover:border-(--app-field-border-hover) focus-visible:border-accent focus-visible:bg-(--app-field-bg-focus) focus-visible:ring-3 focus-visible:ring-(--app-field-ring) aria-invalid:border-destructive disabled:cursor-not-allowed disabled:opacity-60 placeholder:text-(--app-field-placeholder)";

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return <input className={cn(fieldBox, "h-12 w-full min-w-0 px-4 text-base", className)} {...props} />;
}

export function TextArea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(fieldBox, "min-h-24 w-full px-4 py-3 text-base leading-relaxed [field-sizing:content]", className)}
      {...props}
    />
  );
}

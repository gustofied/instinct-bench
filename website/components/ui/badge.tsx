import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeProps = React.ComponentProps<"span"> & {
  variant?: "solid" | "outline" | "ink" | "signal" | "muted";
};

function Badge({ className, variant = "solid", ...props }: BadgeProps) {
  return (
    <span
      data-slot="badge"
      data-variant={variant}
      className={cn(
        "inline-flex h-6 items-center gap-2 border px-2 font-mono text-[9px] uppercase",
        variant === "solid" && "border-marker bg-marker text-white",
        variant === "outline" && "border-marker bg-transparent text-marker",
        variant === "ink" && "border-ink bg-ink text-white",
        variant === "signal" &&
          "border-registration-yellow bg-registration-yellow text-ink",
        variant === "muted" && "border-line bg-faint text-muted",
        className,
      )}
      {...props}
    />
  );
}

export { Badge };

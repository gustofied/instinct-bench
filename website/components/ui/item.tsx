import * as React from "react";

import { cn } from "@/lib/utils";

function ItemGroup({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div data-slot="item-group" className={cn("w-full", className)} {...props} />
  );
}

function Item({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="item"
      className={cn("flex min-w-0 items-center", className)}
      {...props}
    />
  );
}

function ItemContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="item-content"
      className={cn("flex min-w-0 flex-1 flex-col", className)}
      {...props}
    />
  );
}

function ItemTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="item-title"
      className={cn("text-[13px] font-medium leading-5", className)}
      {...props}
    />
  );
}

function ItemDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="item-description"
      className={cn("font-mono text-[9px] text-muted uppercase", className)}
      {...props}
    />
  );
}

export { Item, ItemContent, ItemDescription, ItemGroup, ItemTitle };


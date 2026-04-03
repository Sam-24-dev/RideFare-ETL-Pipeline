import * as TabsPrimitive from "@radix-ui/react-tabs";

import { cn } from "@/lib/utils";

export const Tabs = TabsPrimitive.Root;

type TabsListProps = React.ComponentProps<typeof TabsPrimitive.List>;
type TabsTriggerProps = React.ComponentProps<typeof TabsPrimitive.Trigger>;
type TabsContentProps = React.ComponentProps<typeof TabsPrimitive.Content>;

export function TabsList({ className, ...props }: TabsListProps): React.ReactElement {
  return (
    <TabsPrimitive.List
      className={cn(
        "inline-flex flex-wrap gap-2 rounded-full border border-[var(--color-borde)] bg-white/65 p-1",
        className,
      )}
      {...props}
    />
  );
}

export function TabsTrigger({ className, ...props }: TabsTriggerProps): React.ReactElement {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "rounded-full px-4 py-2 text-sm font-medium text-[var(--color-pizarra)] transition-colors data-[state=active]:bg-[var(--color-obsidiana)] data-[state=active]:text-white",
        className,
      )}
      {...props}
    />
  );
}

export function TabsContent({ className, ...props }: TabsContentProps): React.ReactElement {
  return (
    <TabsPrimitive.Content className={cn("outline-none", className)} {...props} />
  );
}

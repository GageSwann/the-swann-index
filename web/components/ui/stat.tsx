import { cn } from "@/lib/utils"

/** A headline number with its label, for use inside a `<dl>`. */
export function Stat({ label, value, large }: { label: string; value: string; large?: boolean }) {
  return (
    <div>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className={cn("font-bold font-stretch-condensed", large ? "text-3xl" : "text-2xl")}>
        {value}
      </dd>
    </div>
  )
}

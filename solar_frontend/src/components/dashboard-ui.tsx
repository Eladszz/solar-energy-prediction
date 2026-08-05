import type {ReactNode} from 'react';
import {CircleHelp, LoaderCircle, Sparkles} from 'lucide-react';

import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from '@/components/ui/table';

export function SectionHeader({eyebrow, title, description}: {eyebrow?: string; title: string; description: string}) {
  return <div className="mb-6 space-y-2">
    {eyebrow && <p className="text-xs font-bold uppercase tracking-[0.18em] text-sky-700 dark:text-sky-300">{eyebrow}</p>}
    <h2 className="text-2xl font-black tracking-tight text-slate-950 sm:text-3xl dark:text-white">{title}</h2>
    <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">{description}</p>
  </div>;
}

export function HelpTip({label, children}: {label: string; children: ReactNode}) {
  return <span className="group relative inline-flex shrink-0 align-middle">
    <button type="button" aria-label={label} className="inline-flex size-5 items-center justify-center rounded-full text-muted-foreground transition hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring">
      <CircleHelp className="size-4" />
    </button>
    <span role="tooltip" className="pointer-events-none absolute start-1/2 top-7 z-[1000] hidden w-64 -translate-x-1/2 rounded-xl border bg-popover px-3 py-2 text-start text-xs font-normal leading-5 text-popover-foreground shadow-xl group-hover:block group-focus-within:block">
      {children}
    </span>
  </span>;
}

export function MetricCard({label, value, detail, icon, tone = 'sky'}: {
  label: string;
  value: string;
  detail?: string;
  icon: ReactNode;
  tone?: 'sky' | 'amber' | 'emerald' | 'violet' | 'rose';
}) {
  const tones = {
    sky: 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300',
    amber: 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
    emerald: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
    violet: 'bg-violet-100 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300',
    rose: 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300',
  };
  return <Card className="overflow-hidden border-border/70 shadow-sm">
    <CardContent className="flex items-start justify-between gap-4 p-5">
      <div className="min-w-0">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
        <p dir="auto" className="mt-2 break-words text-2xl font-black tracking-tight text-slate-950 dark:text-white">{value}</p>
        {detail && <p dir="auto" className="mt-1 text-xs text-muted-foreground">{detail}</p>}
      </div>
      <span className={`flex size-10 shrink-0 items-center justify-center rounded-2xl ${tones[tone]}`}>{icon}</span>
    </CardContent>
  </Card>;
}

export function EmptyState({title, description}: {title: string; description?: string}) {
  return <div className="flex min-h-72 flex-col items-center justify-center rounded-3xl border border-dashed border-border bg-card/60 p-8 text-center shadow-sm">
    <span className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"><Sparkles className="size-6" /></span>
    <p className="max-w-lg font-semibold text-foreground">{title}</p>
    {description && <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">{description}</p>}
  </div>;
}

export function LoadingBanner({title, description}: {title: string; description: string}) {
  return <div role="status" aria-live="polite" className="mb-5 flex items-center gap-3 rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sky-950 shadow-sm dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-100">
    <LoaderCircle className="size-5 shrink-0 animate-spin text-sky-600 dark:text-sky-300" />
    <div><p className="text-sm font-bold">{title}</p><p className="text-xs text-sky-800/80 dark:text-sky-200/75">{description}</p></div>
  </div>;
}

export function ChartCard({title, help, helpLabel, children, className = ''}: {title: string; help?: string; helpLabel?: string; children: ReactNode; className?: string}) {
  return <Card className={`border-border/70 shadow-sm ${className}`}>
    <CardHeader className="pb-2">
      <CardTitle className="flex items-center gap-2 text-base font-bold">{title}{help && <HelpTip label={helpLabel || title}>{help}</HelpTip>}</CardTitle>
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>;
}

export function DetailsTable({rows, fieldLabel, valueLabel}: {rows: Array<{field: string; value: ReactNode}>; fieldLabel: string; valueLabel: string}) {
  return <div className="overflow-hidden rounded-2xl border bg-card">
    <Table>
      <TableHeader><TableRow><TableHead>{fieldLabel}</TableHead><TableHead>{valueLabel}</TableHead></TableRow></TableHeader>
      <TableBody>{rows.map((row) => <TableRow key={row.field}><TableCell className="font-medium">{row.field}</TableCell><TableCell className="break-words text-muted-foreground">{row.value}</TableCell></TableRow>)}</TableBody>
    </Table>
  </div>;
}

export function ChartTooltipBox({label, lines}: {label?: string; lines: Array<{name: string; value: string; color?: string}>}) {
  return <div className="min-w-40 rounded-xl border bg-background/95 px-3 py-2 text-xs shadow-xl backdrop-blur">
    {label && <p className="mb-1.5 font-bold text-foreground">{label}</p>}
    <div className="space-y-1">{lines.map((line) => <div key={`${line.name}-${line.value}`} className="flex items-center justify-between gap-4">
      <span className="flex items-center gap-1.5 text-muted-foreground">{line.color && <span className="size-2 rounded-full" style={{backgroundColor: line.color}} />}{line.name}</span>
      <span className="font-semibold text-foreground">{line.value}</span>
    </div>)}</div>
  </div>;
}

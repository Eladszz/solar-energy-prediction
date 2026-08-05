import {
  ChartNoAxesCombined,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Settings2,
  X,
} from 'lucide-react';

import {Accordion, AccordionContent, AccordionItem, AccordionTrigger} from '@/components/ui/accordion';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from '@/components/ui/select';
import type {CleanlinessLevel, CurrencyCode, ShadingLevel} from '@/lib/solar-api';
import {formatMoney, formatNumber} from '@/src/formatters';
import type {Copy, Language} from '@/src/i18n';
import {HelpTip} from '@/src/components/dashboard-ui';

export interface ConfigurationValues {
  year: number;
  panelArea: number;
  efficiency: number;
  tilt: number;
  cleanliness: CleanlinessLevel;
  shading: ShadingLevel;
  acCapacity: number;
  gamma: number;
  noct: number;
  tariff: number;
  currency: CurrencyCode;
  capex: number;
}

interface SidebarProps {
  language: Language;
  copy: Copy;
  collapsed: boolean;
  onCollapsedChange: (collapsed: boolean) => void;
  mobileOpen: boolean;
  onMobileOpenChange: (open: boolean) => void;
  values: ConfigurationValues;
  onValuesChange: (values: Partial<ConfigurationValues>) => void;
  onRun: () => void;
  loading: boolean;
}

function NumberField({label, value, onChange, step = 1, help}: {label: string; value: number; onChange: (value: number) => void; step?: number; help?: string}) {
  return <div className="space-y-1.5">
    <div className="flex items-center gap-1.5"><Label>{label}</Label>{help && <HelpTip label={label}>{help}</HelpTip>}</div>
    <Input type="number" step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
  </div>;
}

export function MobileConfigurationBar({copy, onOpen}: {copy: Copy; onOpen: () => void}) {
  return <div className="sticky top-0 z-30 mb-4 flex items-center justify-between gap-3 rounded-2xl border bg-background/95 px-3 py-2 shadow-sm backdrop-blur lg:hidden">
    <Button variant="outline" size="icon" onClick={onOpen} aria-label={copy.openMenu}><Menu /></Button>
    <div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{copy.controls}</p><p className="truncate text-xs text-muted-foreground">{copy.configurationDescription}</p></div>
  </div>;
}

export function DashboardSidebar(props: SidebarProps) {
  const {copy, language, values} = props;
  const isHebrew = language === 'he';
  const setValue = <Key extends keyof ConfigurationValues>(key: Key, value: ConfigurationValues[Key]) => props.onValuesChange({[key]: value});
  const isCollapsed = props.collapsed && !props.mobileOpen;

  return <>
    {props.mobileOpen && <button aria-label={copy.closeMenu} className="fixed inset-0 z-40 bg-slate-950/35 backdrop-blur-[2px] lg:hidden" onClick={() => props.onMobileOpenChange(false)} />}
    <aside className={`fixed inset-y-0 start-0 z-50 flex w-[min(92vw,370px)] shrink-0 flex-col border-e bg-card shadow-2xl transition-[width,transform] duration-200 lg:sticky lg:top-0 lg:z-20 lg:h-screen lg:translate-x-0 lg:shadow-none ${props.mobileOpen ? 'translate-x-0' : isHebrew ? 'translate-x-full' : '-translate-x-full'} ${isCollapsed ? 'lg:w-[84px]' : 'lg:w-[370px]'}`}>
      <div className="flex h-17 items-center justify-between border-b px-4">
        {!isCollapsed && <div><p className="text-xs font-black uppercase tracking-[0.18em] text-sky-700 dark:text-sky-300">{copy.controls}</p><p className="mt-0.5 text-xs text-muted-foreground">{copy.configurationDescription}</p></div>}
        <Button className="lg:hidden" variant="ghost" size="icon" onClick={() => props.onMobileOpenChange(false)} aria-label={copy.closeMenu}><X /></Button>
        <Button className="hidden lg:inline-flex" variant="ghost" size="icon" onClick={() => props.onCollapsedChange(!props.collapsed)} aria-label={isCollapsed ? copy.expandSidebar : copy.collapseSidebar} title={isCollapsed ? copy.expandSidebar : copy.collapseSidebar}>
          {isCollapsed ? (isHebrew ? <PanelLeftClose /> : <PanelLeftOpen />) : (isHebrew ? <PanelLeftOpen /> : <PanelLeftClose />)}
        </Button>
      </div>

      {!isCollapsed && <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">
        <div className="flex items-center gap-2 py-4"><Settings2 className="size-4 text-sky-600" /><h2 className="text-sm font-black">{copy.controls}</h2></div>
        <Accordion defaultValue={['system', 'financial']} className="gap-3">
          <AccordionItem value="system" className="rounded-2xl border bg-background px-3 shadow-sm">
            <AccordionTrigger className="py-3 hover:no-underline"><span className="flex items-center gap-2 font-bold"><ChartNoAxesCombined className="size-4 text-amber-600" />{copy.systemParameters}</span></AccordionTrigger>
            <AccordionContent className="space-y-3 pb-3">
              <div className="grid grid-cols-2 gap-3">
                <NumberField label={copy.forecastYear} value={values.year} onChange={(value) => setValue('year', value)} />
                <NumberField label={copy.panelArea} value={values.panelArea} onChange={(value) => setValue('panelArea', value)} step={0.1} />
                <NumberField label={copy.acCapacity} value={values.acCapacity} onChange={(value) => setValue('acCapacity', value)} step={0.1} />
                <NumberField label={copy.tilt} value={values.tilt} onChange={(value) => setValue('tilt', value)} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5"><Label>{copy.cleanliness}</Label><Select value={values.cleanliness} onValueChange={(value) => setValue('cleanliness', value as CleanlinessLevel)}><SelectTrigger><SelectValue>{copy[values.cleanliness]}</SelectValue></SelectTrigger><SelectContent>{(['clean', 'normal', 'dusty'] as const).map((value) => <SelectItem key={value} value={value}>{copy[value]}</SelectItem>)}</SelectContent></Select></div>
                <div className="space-y-1.5"><Label>{copy.shading}</Label><Select value={values.shading} onValueChange={(value) => setValue('shading', value as ShadingLevel)}><SelectTrigger><SelectValue>{copy[values.shading]}</SelectValue></SelectTrigger><SelectContent>{(['none', 'low', 'medium', 'high'] as const).map((value) => <SelectItem key={value} value={value}>{copy[value]}</SelectItem>)}</SelectContent></Select></div>
              </div>
              <Accordion className="rounded-xl border border-dashed px-3">
                <AccordionItem value="advanced" className="border-none"><AccordionTrigger className="py-2.5 text-xs hover:no-underline">{copy.advancedParameters}</AccordionTrigger><AccordionContent className="grid grid-cols-2 gap-3 pb-3">
                  <NumberField label={copy.panelEfficiency} value={values.efficiency} onChange={(value) => setValue('efficiency', value)} step={0.01} />
                  <NumberField label={copy.temperatureCoefficient} value={values.gamma} onChange={(value) => setValue('gamma', value)} step={0.001} />
                  <NumberField label={copy.noct} value={values.noct} onChange={(value) => setValue('noct', value)} step={0.1} />
                </AccordionContent></AccordionItem>
              </Accordion>
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="financial" className="rounded-2xl border bg-background px-3 shadow-sm">
            <AccordionTrigger className="py-3 hover:no-underline"><span className="flex items-center gap-2 font-bold"><CircleDollarSign className="size-4 text-emerald-600" />{copy.financialInputs}</span></AccordionTrigger>
            <AccordionContent className="space-y-3 pb-3">
              <div className="grid grid-cols-2 gap-3"><NumberField label={copy.tariff} value={values.tariff} onChange={(value) => setValue('tariff', value)} step={0.01} /><NumberField label={copy.capex} value={values.capex} onChange={(value) => setValue('capex', value)} step={100} /></div>
              <div className="space-y-1.5"><Label>{copy.currency}</Label><Select value={values.currency} onValueChange={(value) => setValue('currency', value as CurrencyCode)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{(['ILS', 'USD', 'EUR'] as const).map((value) => <SelectItem key={value} value={value}>{value}</SelectItem>)}</SelectContent></Select></div>
              <div className="rounded-xl bg-emerald-50 p-3 text-xs text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100"><p className="font-bold">{copy.financialSnapshot}</p><p className="mt-1">{formatMoney(values.capex, values.currency, language)} · {formatNumber(values.tariff, language, 2)} / kWh</p></div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        <Button className="mt-4 h-11 w-full bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg shadow-sky-600/20 hover:opacity-90" onClick={props.onRun} disabled={props.loading}>
          {props.loading ? copy.running : copy.runEstimate}{isHebrew ? <ChevronLeft /> : <ChevronRight />}
        </Button>
        <p className="mt-2 px-2 text-center text-[11px] leading-4 text-muted-foreground">{copy.runEstimateHint}</p>
      </div>}
    </aside>
  </>;
}

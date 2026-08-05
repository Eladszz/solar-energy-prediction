import {
  Activity,
  AreaChart,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BatteryCharging,
  CalendarDays,
  CircleDollarSign,
  Clock3,
  CloudSun,
  Gauge,
  GitCompareArrows,
  Landmark,
  Percent,
  PiggyBank,
  ReceiptText,
  Sun,
  Target,
  TrendingUp,
  Zap,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import type {
  CurrencyCode,
  ScenarioComparisonResponse,
  ScenarioComparisonScenarioPayload,
  SimulationResponse,
  YearlyForecastResponse,
} from '@/lib/solar-api';
import {ChartCard, ChartTooltipBox, DetailsTable, EmptyState, MetricCard, SectionHeader} from '@/src/components/dashboard-ui';
import {formatDate, formatEnergy, formatHour, formatMoney, formatNumber, formatPayback, formatPercent, formatPower} from '@/src/formatters';
import type {Copy, Language} from '@/src/i18n';
import {MONTH_LABELS} from '@/src/i18n';

const COLORS = ['#0284c7', '#059669', '#f59e0b', '#8b5cf6', '#e11d48', '#0891b2'];

function axisNumber(value: number, language: Language) {
  return formatNumber(value, language, 0);
}

function percentageTone(value: number): 'emerald' | 'rose' | 'sky' {
  return value > 0 ? 'emerald' : value < 0 ? 'rose' : 'sky';
}

function SectionBadge({children}: {children: string}) {
  return <Badge variant="outline" className="rounded-full bg-background/80 px-3 py-1 font-semibold">{children}</Badge>;
}

export function OverviewView({copy, language, forecast}: {copy: Copy; language: Language; forecast: YearlyForecastResponse | null}) {
  if (!forecast) return <><SectionHeader eyebrow={copy.overview} title={copy.overviewTitle} description={copy.overviewIntro} /><EmptyState title={copy.noYearlyData} description={copy.runEstimateHint} /></>;

  const currency = forecast.financial_assumptions.currency;
  const months = MONTH_LABELS[language];
  const monthly = months.map((month, index) => ({month, energy: forecast.monthly_kwh[index] ?? 0, value: forecast.monthly_estimated_value[index] ?? 0}));
  const seasonIndexes = [[11, 0, 1], [2, 3, 4], [5, 6, 7], [8, 9, 10]];
  const seasonNames = [copy.winter, copy.spring, copy.summer, copy.autumn];
  const seasons = seasonIndexes.map((indexes, index) => {
    const energy = indexes.reduce((sum, monthIndex) => sum + (forecast.monthly_kwh[monthIndex] ?? 0), 0);
    return {season: seasonNames[index], energy, share: forecast.yearly_kwh > 0 ? energy / forecast.yearly_kwh * 100 : 0};
  });
  const details = [
    {field: copy.productionModel, value: forecast.production_model},
    {field: copy.weatherSource, value: forecast.weather_source},
    {field: copy.requestedYear, value: String(forecast.requested_forecast_year)},
    {field: copy.weatherReferenceYear, value: String(forecast.weather_reference_year)},
    {field: copy.valuationBasis, value: forecast.financial_assumptions.valuation_basis},
  ];

  return <>
    <SectionHeader eyebrow={copy.overview} title={copy.overviewTitle} description={copy.overviewIntro} />
    {forecast.fallback_reason && <Alert className="mb-5 border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-900 dark:bg-amber-950/35 dark:text-amber-100"><CloudSun /><AlertTitle>{copy.fallbackTitle}</AlertTitle><AlertDescription>{copy.fallbackDescription} ({forecast.weather_reference_year})</AlertDescription></Alert>}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard label={copy.yearlyEnergy} value={formatEnergy(forecast.yearly_kwh, language)} icon={<Zap />} tone="amber" />
      <MetricCard label={copy.averageMonthlyEnergy} value={formatEnergy(forecast.yearly_kwh / 12, language)} icon={<CalendarDays />} tone="sky" />
      <MetricCard label={copy.averageDailyEnergy} value={formatEnergy(forecast.avg_daily_kwh, language, 1)} icon={<Sun />} tone="emerald" />
      <MetricCard label={copy.specificYield} value={`${formatNumber(forecast.specific_yield_kwh_per_kwp, language, 0)} kWh/kWp`} icon={<Gauge />} tone="violet" />
    </div>

    <div className="mt-6 grid gap-5 xl:grid-cols-2">
      <ChartCard title={copy.monthlyProduction} help={copy.monthlyProductionHelp}>
        <div className="h-[310px]" data-testid="monthly-production-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={monthly} margin={{top: 12, right: 8, left: 4, bottom: 0}}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => axisNumber(value, language)} width={52} tickLine={false} axisLine={false} unit=" kWh" /><Tooltip cursor={{fill: 'rgba(14,165,233,.08)'}} content={({active, payload, label}) => active && payload?.length ? <ChartTooltipBox label={String(label)} lines={[{name: copy.energy, value: formatEnergy(Number(payload[0].value), language), color: '#f59e0b'}]} /> : null} /><Bar dataKey="energy" fill="#f59e0b" radius={[7, 7, 0, 0]} /></BarChart></ResponsiveContainer></div>
      </ChartCard>
      <ChartCard title={copy.monthlyValue} help={copy.monthlyValueHelp}>
        <div className="h-[310px]" data-testid="monthly-value-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={monthly} margin={{top: 12, right: 12, left: 4, bottom: 0}}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => axisNumber(value, language)} width={52} tickLine={false} axisLine={false} /><Tooltip content={({active, payload, label}) => active && payload?.length ? <ChartTooltipBox label={String(label)} lines={[{name: copy.estimatedValue, value: formatMoney(Number(payload[0].value), currency, language), color: '#0284c7'}]} /> : null} /><Line type="monotone" dataKey="value" stroke="#0284c7" strokeWidth={3} dot={{r: 3, fill: '#0284c7'}} activeDot={{r: 6}} /></LineChart></ResponsiveContainer></div>
      </ChartCard>
    </div>

    <div className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_1fr]">
      <ChartCard title={copy.seasonalProduction} help={copy.seasonalProductionHelp}>
        <div className="h-[280px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={seasons} layout="vertical" margin={{top: 8, right: 22, left: 10, bottom: 0}}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" tickFormatter={(value) => axisNumber(value, language)} unit=" kWh" /><YAxis type="category" dataKey="season" width={language === 'he' ? 55 : 64} tickLine={false} axisLine={false} /><Tooltip cursor={{fill: 'rgba(5,150,105,.08)'}} content={({active, payload, label}) => active && payload?.length ? <ChartTooltipBox label={String(label)} lines={[{name: copy.energy, value: formatEnergy(Number(payload[0].value), language), color: '#059669'}, {name: copy.percentOfAnnual, value: formatPercent(Number(payload[0].payload.share), language)}]} /> : null} /><Bar dataKey="energy" fill="#059669" radius={[0, 7, 7, 0]} /></BarChart></ResponsiveContainer></div>
      </ChartCard>
      <div className="space-y-4">
        <MetricCard label={copy.annualSavings} value={formatMoney(forecast.annual_savings, currency, language)} icon={<PiggyBank />} tone="emerald" />
        <MetricCard label={copy.simplePayback} value={formatPayback(forecast.simple_payback_years, language, copy)} icon={<Target />} tone="violet" />
      </div>
    </div>
    <div className="mt-5"><h3 className="mb-3 text-lg font-black">{copy.systemContext}</h3><DetailsTable rows={details} fieldLabel={copy.field} valueLabel={copy.value} /></div>
  </>;
}

export function ForecastView({copy, language, daily}: {copy: Copy; language: Language; daily: SimulationResponse | null}) {
  if (!daily) return <><SectionHeader eyebrow={copy.forecast} title={copy.shortTermTitle} description={copy.shortTermIntro} /><EmptyState title={copy.noDailyData} description={copy.runEstimateHint} /></>;
  const peak = daily.hourly_ac_kw.length ? Math.max(...daily.hourly_ac_kw) : 0;
  const peakIndex = daily.hourly_ac_kw.findIndex((value) => value === peak);
  const peakHour = formatHour(daily.hourly_time[peakIndex], peakIndex);
  const currency = daily.financial_assumptions.currency;
  const chartData = daily.hourly_ac_kw.map((power, index) => ({time: formatHour(daily.hourly_time[index], index), power}));
  const lossPercent = Math.max(0, (1 - daily.system_loss_factor) * 100);
  const dateLabel = formatDate(daily.hourly_time[0], language);
  const details = [
    {field: copy.productionModel, value: daily.production_model},
    {field: copy.weatherSource, value: daily.weather_source},
    {field: copy.timezone, value: daily.timezone},
    {field: copy.coordinates, value: `${formatNumber(daily.location[0], language, 4)}, ${formatNumber(daily.location[1], language, 4)}`},
    {field: copy.valuationBasis, value: daily.financial_assumptions.valuation_basis},
  ];
  return <>
    <SectionHeader eyebrow={copy.forecast} title={copy.shortTermTitle} description={copy.shortTermIntro} />
    <div className="mb-5 flex flex-wrap gap-2"><SectionBadge>{dateLabel}</SectionBadge><SectionBadge>{daily.timezone}</SectionBadge></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <MetricCard label={copy.dailyEnergy} value={formatEnergy(daily.daily_kwh, language, 1)} icon={<BatteryCharging />} tone="amber" />
      <MetricCard label={copy.peakPower} value={formatPower(peak, language)} icon={<Zap />} tone="rose" />
      <MetricCard label={copy.peakHour} value={peakHour} icon={<Clock3 />} tone="sky" />
      <MetricCard label={copy.averagePower} value={formatPower(daily.avg_kw, language)} icon={<Activity />} tone="emerald" />
      <MetricCard label={copy.systemLosses} value={formatPercent(lossPercent, language)} icon={<Percent />} tone="violet" />
    </div>
    <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_260px]">
      <ChartCard title={copy.hourlyPower} help={copy.hourlyPowerHelp}>
        <div className="h-[390px]" data-testid="hourly-power-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{top: 18, right: 18, left: 4, bottom: 0}}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="time" tickLine={false} axisLine={false} interval={2} /><YAxis tickFormatter={(value) => formatNumber(value, language, 1)} unit=" kW" width={52} tickLine={false} axisLine={false} /><Tooltip content={({active, payload, label}) => active && payload?.length ? <ChartTooltipBox label={String(label)} lines={[{name: copy.power, value: formatPower(Number(payload[0].value), language), color: '#059669'}]} /> : null} /><ReferenceLine x={peakHour} stroke="#e11d48" strokeDasharray="5 5" label={{value: copy.peakPower, position: 'top', fill: '#e11d48', fontSize: 11}} /><Line type="monotone" dataKey="power" stroke="#059669" strokeWidth={3} dot={false} activeDot={{r: 6}} /></LineChart></ResponsiveContainer></div>
      </ChartCard>
      <MetricCard label={copy.dailyValue} value={formatMoney(daily.estimated_daily_value, currency, language, 2)} detail={dateLabel} icon={<CircleDollarSign />} tone="emerald" />
    </div>
    <div className="mt-5"><h3 className="mb-3 text-lg font-black">{copy.calculationDetails}</h3><DetailsTable rows={details} fieldLabel={copy.field} valueLabel={copy.value} /></div>
  </>;
}

export interface ScenarioDraft {
  name: string;
  panelArea: number;
  tilt: number;
  acCapacity: number;
  capex: number;
}

export function ScenariosView({copy, language, currency, draft, onDraftChange, scenarios, onAdd, onRemove, onCompare, comparison, loading}: {
  copy: Copy;
  language: Language;
  currency: CurrencyCode;
  draft: ScenarioDraft;
  onDraftChange: (draft: Partial<ScenarioDraft>) => void;
  scenarios: ScenarioComparisonScenarioPayload[];
  onAdd: () => void;
  onRemove: (name: string) => void;
  onCompare: () => void;
  comparison: ScenarioComparisonResponse | null;
  loading: boolean;
}) {
  const months = MONTH_LABELS[language];
  const displayName = (result: ScenarioComparisonResponse['results'][number], index: number) => index === 0 ? copy.baseSystem : result.scenario.name;
  const monthlyData = comparison ? months.map((month, monthIndex) => Object.assign({month}, ...comparison.results.map((result, resultIndex) => ({[displayName(result, resultIndex)]: result.monthly_kwh[monthIndex] ?? 0})))) : [];
  const annualData = comparison?.results.map((result, index) => ({name: displayName(result, index), energy: result.yearly_kwh, value: result.annual_savings})) ?? [];
  return <>
    <SectionHeader eyebrow={copy.scenarios} title={copy.scenariosTitle} description={copy.scenariosIntro} />
    <Card className="border-border/70 shadow-sm"><CardHeader><CardTitle className="flex items-center gap-2"><GitCompareArrows className="size-5 text-violet-600" />{copy.scenarioBuilder}</CardTitle></CardHeader><CardContent>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <ScenarioField label={copy.scenarioName} value={draft.name} onChange={(value) => onDraftChange({name: value})} />
        <ScenarioField label={copy.scenarioArea} type="number" value={draft.panelArea} onChange={(value) => onDraftChange({panelArea: Number(value)})} />
        <ScenarioField label={copy.scenarioTilt} type="number" value={draft.tilt} onChange={(value) => onDraftChange({tilt: Number(value)})} />
        <ScenarioField label={copy.scenarioAc} type="number" value={draft.acCapacity} onChange={(value) => onDraftChange({acCapacity: Number(value)})} />
        <ScenarioField label={copy.scenarioCapex} type="number" value={draft.capex} onChange={(value) => onDraftChange({capex: Number(value)})} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2"><Button variant="secondary" onClick={onAdd}>{copy.addScenario}</Button><Button onClick={onCompare} disabled={loading || scenarios.length === 0}>{loading ? copy.running : copy.compareScenarios}</Button></div>
      <div className="mt-5"><h3 className="text-sm font-black">{copy.configuredScenarios}</h3>{scenarios.length === 0 ? <p className="mt-2 rounded-xl border border-dashed p-4 text-sm text-muted-foreground">{copy.scenarioEmpty}</p> : <div className="mt-2 grid gap-2 md:grid-cols-2">{scenarios.map((scenario) => <div key={scenario.name} className="flex items-center justify-between gap-3 rounded-xl border bg-muted/25 px-3 py-2"><div><p className="font-bold">{scenario.name}</p><p className="text-xs text-muted-foreground">{formatNumber(scenario.panel_area, language, 1)} m² · {formatPower(scenario.ac_capacity_kw, language, 1)} · {formatMoney(scenario.system_capex, currency, language)}</p></div><Button variant="ghost" size="sm" onClick={() => onRemove(scenario.name)}>{copy.remove}</Button></div>)}</div>}</div>
    </CardContent></Card>

    {!comparison ? <div className="mt-5"><EmptyState title={copy.noScenarioData} description={copy.scenariosIntro} /></div> : <>
      {comparison.fallback_reason && <Alert className="mt-5 border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/35"><CloudSun /><AlertTitle>{copy.fallbackTitle}</AlertTitle><AlertDescription>{copy.fallbackDescription} ({comparison.weather_reference_year})</AlertDescription></Alert>}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <ChartCard title={copy.scenarioMonthlyEnergy} help={copy.scenarioMonthlyEnergyHelp} className="xl:col-span-2"><div className="h-[350px]" data-testid="scenario-monthly-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={monthlyData} margin={{top: 12, right: 16, left: 4, bottom: 0}}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" /><YAxis tickFormatter={(value) => axisNumber(value, language)} unit=" kWh" width={55} /><Tooltip formatter={(value) => formatEnergy(Number(value), language)} /><Legend />{comparison.results.map((result, index) => <Line key={result.scenario.name} type="monotone" dataKey={displayName(result, index)} stroke={COLORS[index % COLORS.length]} strokeWidth={index === 0 ? 3 : 2} strokeDasharray={index === 0 ? '6 4' : undefined} dot={false} />)}</LineChart></ResponsiveContainer></div></ChartCard>
        <ChartCard title={copy.scenarioAnnualEnergy}><div className="h-[300px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={annualData}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" /><YAxis tickFormatter={(value) => axisNumber(value, language)} unit=" kWh" width={55} /><Tooltip formatter={(value) => formatEnergy(Number(value), language)} /><Bar dataKey="energy" fill="#8b5cf6" radius={[7, 7, 0, 0]} /></BarChart></ResponsiveContainer></div></ChartCard>
        <ChartCard title={copy.scenarioAnnualValue}><div className="h-[300px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={annualData}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" /><YAxis tickFormatter={(value) => axisNumber(value, language)} width={55} /><Tooltip formatter={(value) => formatMoney(Number(value), currency, language)} /><Bar dataKey="value" fill="#059669" radius={[7, 7, 0, 0]} /></BarChart></ResponsiveContainer></div></ChartCard>
      </div>
      <h3 className="mb-3 mt-6 text-lg font-black">{copy.scenarioResults}</h3>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{comparison.results.map((result, index) => <Card key={result.scenario.name} className={`border-border/70 shadow-sm ${index === 0 ? 'border-sky-300 bg-sky-50/60 dark:border-sky-900 dark:bg-sky-950/20' : ''}`}><CardHeader className="pb-2"><div className="flex items-center justify-between gap-3"><CardTitle className="text-base">{displayName(result, index)}</CardTitle>{index === 0 && <Badge>{copy.baseSystem}</Badge>}</div></CardHeader><CardContent className="space-y-3">
        <p className="text-2xl font-black">{formatEnergy(result.yearly_kwh, language)}</p><p className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">{formatMoney(result.annual_savings, currency, language)} · {formatPayback(result.simple_payback_years, language, copy)}</p>
        <div className="grid grid-cols-2 gap-2 text-xs"><DeltaPill label={copy.energyDelta} value={result.deviation_percent} language={language} /><DeltaPill label={copy.valueDelta} value={result.value_deviation_percent} language={language} /></div>
      </CardContent></Card>)}</div>
    </>}
  </>;
}

function ScenarioField({label, value, onChange, type = 'text'}: {label: string; value: string | number; onChange: (value: string) => void; type?: 'text' | 'number'}) {
  return <div className="space-y-1.5"><Label>{label}</Label><Input type={type} value={value} onChange={(event) => onChange(event.target.value)} /></div>;
}

function DeltaPill({label, value, language}: {label: string; value: number; language: Language}) {
  const Icon = value > 0 ? ArrowUpRight : value < 0 ? ArrowDownRight : ArrowRight;
  const colors = percentageTone(value) === 'emerald' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200' : percentageTone(value) === 'rose' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-200' : 'bg-sky-100 text-sky-800 dark:bg-sky-950/50 dark:text-sky-200';
  return <div className={`rounded-xl p-2 ${colors}`}><p className="opacity-80">{label}</p><p className="mt-1 flex items-center gap-1 font-black"><Icon className="size-3.5" />{formatPercent(value, language, 1, true)}</p></div>;
}

export function FinanceView({copy, language, forecast}: {copy: Copy; language: Language; forecast: YearlyForecastResponse | null}) {
  if (!forecast) return <><SectionHeader eyebrow={copy.finance} title={copy.financeTitle} description={copy.financeIntro} /><EmptyState title={copy.noFinanceData} description={copy.runEstimateHint} /></>;
  const currency = forecast.financial_assumptions.currency;
  const monthly = MONTH_LABELS[language].map((month, index) => ({month, value: forecast.monthly_estimated_value[index] ?? 0}));
  const rows = [
    {field: copy.tariff, value: `${formatMoney(forecast.financial_assumptions.electricity_price_per_kwh, currency, language, 2)} / kWh`},
    {field: copy.systemCost, value: formatMoney(forecast.financial_assumptions.system_capex, currency, language)},
    {field: copy.valuationBasis, value: forecast.financial_assumptions.valuation_basis},
    {field: copy.savingsBasis, value: forecast.financial_assumptions.annual_savings_basis},
    {field: copy.paybackBasis, value: forecast.financial_assumptions.payback_basis},
  ];
  return <>
    <SectionHeader eyebrow={copy.finance} title={copy.financeTitle} description={copy.financeIntro} />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard label={copy.annualValue} value={formatMoney(forecast.yearly_estimated_value, currency, language)} icon={<Landmark />} tone="sky" />
      <MetricCard label={copy.annualSavings} value={formatMoney(forecast.annual_savings, currency, language)} icon={<PiggyBank />} tone="emerald" />
      <MetricCard label={copy.simplePayback} value={formatPayback(forecast.simple_payback_years, language, copy)} icon={<Target />} tone="violet" />
      <MetricCard label={copy.averageMonthlyValue} value={formatMoney(forecast.avg_monthly_estimated_value, currency, language)} icon={<ReceiptText />} tone="amber" />
    </div>
    <div className="mt-6 grid gap-5 xl:grid-cols-[1.35fr_1fr]">
      <ChartCard title={copy.monthlyValue} help={copy.monthlyValueHelp}><div className="h-[340px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={monthly}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" /><YAxis tickFormatter={(value) => axisNumber(value, language)} width={55} /><Tooltip formatter={(value) => formatMoney(Number(value), currency, language)} /><Bar dataKey="value" fill="#059669" radius={[7, 7, 0, 0]} /></BarChart></ResponsiveContainer></div></ChartCard>
      <div><h3 className="mb-3 text-lg font-black">{copy.financialContext}</h3><DetailsTable rows={rows} fieldLabel={copy.field} valueLabel={copy.value} /></div>
    </div>
  </>;
}

export function MethodologyView({copy}: {copy: Copy}) {
  const cards = [
    {title: copy.physicalModelTitle, text: copy.physicalModelText, icon: <AreaChart />, color: 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'},
    {title: copy.weatherTitle, text: copy.weatherText, icon: <CloudSun />, color: 'bg-sky-100 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300'},
    {title: copy.financeMethodTitle, text: copy.financeMethodText, icon: <TrendingUp />, color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'},
    {title: copy.scopeTitle, text: copy.scopeText, icon: <Target />, color: 'bg-violet-100 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300'},
  ];
  return <>
    <SectionHeader eyebrow={copy.methodology} title={copy.methodologyTitle} description={copy.methodologyIntro} />
    <div className="mb-6 grid gap-3 md:grid-cols-4">{[copy.flowInputs, copy.flowWeather, copy.flowPhysical, copy.flowOutputs].map((step, index) => <div key={step} className="relative rounded-2xl border bg-card p-4 text-center text-sm font-bold shadow-sm"><span className="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-sky-600 text-xs text-white">{index + 1}</span>{step}{index < 3 && <ArrowRight className="absolute -end-5 top-1/2 z-10 hidden size-5 -translate-y-1/2 text-muted-foreground md:block rtl:rotate-180" />}</div>)}</div>
    <div className="grid gap-5 md:grid-cols-2">{cards.map((card) => <Card key={card.title} className="border-border/70 shadow-sm"><CardContent className="flex gap-4 p-6"><span className={`flex size-11 shrink-0 items-center justify-center rounded-2xl ${card.color}`}>{card.icon}</span><div><h3 className="font-black">{card.title}</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">{card.text}</p></div></CardContent></Card>)}</div>
  </>;
}

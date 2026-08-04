import {useState} from 'react';
import {MapContainer, Marker, TileLayer, useMapEvents} from 'react-leaflet';
import {Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Input} from '@/components/ui/input';
import {Label} from '@/components/ui/label';
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from '@/components/ui/select';
import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs';
import {APP_DEFAULTS} from '@/lib/defaults';
import {
  apiPost,
  type CleanlinessLevel,
  type CurrencyCode,
  type PVRequestPayload,
  type ScenarioComparisonRequestPayload,
  type ScenarioComparisonResponse,
  type ScenarioComparisonScenarioPayload,
  type ShadingLevel,
  type SimulationResponse,
  type YearlyForecastResponse,
} from '@/lib/solar-api';

L.Marker.prototype.options.icon = L.icon({iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41]});
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
type Position = {lat: number; lng: number};

function MapPicker({position, onChange}: {position: Position; onChange: (position: Position) => void}) {
  useMapEvents({click: (event) => onChange(event.latlng)});
  return <Marker position={position} />;
}

async function geocode(address: string): Promise<Position | null> {
  const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`);
  if (!response.ok) throw new Error('Location search is unavailable.');
  const data = await response.json() as Array<{lat: string; lon: string}>;
  return data[0] ? {lat: Number(data[0].lat), lng: Number(data[0].lon)} : null;
}

function money(value: number, currency: string): string {
  return `${value.toLocaleString(undefined, {maximumFractionDigits: 0})} ${currency}`;
}

export default function App() {
  const [position, setPosition] = useState<Position>({lat: 32.0853, lng: 34.7818});
  const [address, setAddress] = useState('');
  const [year, setYear] = useState(new Date().getFullYear());
  const [panelArea, setPanelArea] = useState(APP_DEFAULTS.panelAreaSqm);
  const [efficiency, setEfficiency] = useState(APP_DEFAULTS.panelEfficiency);
  const [tilt, setTilt] = useState(APP_DEFAULTS.tiltDegrees);
  const [cleanliness, setCleanliness] = useState<CleanlinessLevel>(APP_DEFAULTS.cleanliness);
  const [shading, setShading] = useState<ShadingLevel>(APP_DEFAULTS.shading);
  const [acCapacity, setAcCapacity] = useState(APP_DEFAULTS.acCapacityKw);
  const [gamma, setGamma] = useState(APP_DEFAULTS.gamma);
  const [noct, setNoct] = useState(APP_DEFAULTS.noctC);
  const [tariff, setTariff] = useState(APP_DEFAULTS.electricityPricePerKwh);
  const [currency, setCurrency] = useState<CurrencyCode>(APP_DEFAULTS.currency);
  const [capex, setCapex] = useState(APP_DEFAULTS.systemCapex);
  const [forecast, setForecast] = useState<YearlyForecastResponse | null>(null);
  const [daily, setDaily] = useState<SimulationResponse | null>(null);
  const [comparison, setComparison] = useState<ScenarioComparisonResponse | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioComparisonScenarioPayload[]>([]);
  const [scenarioName, setScenarioName] = useState('Option 1');
  const [scenarioArea, setScenarioArea] = useState(APP_DEFAULTS.panelAreaSqm * 1.2);
  const [scenarioTilt, setScenarioTilt] = useState(APP_DEFAULTS.tiltDegrees);
  const [scenarioAc, setScenarioAc] = useState(APP_DEFAULTS.acCapacityKw);
  const [scenarioCapex, setScenarioCapex] = useState(APP_DEFAULTS.systemCapex);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const payload = (): PVRequestPayload => ({
    latitude: position.lat, longitude: position.lng, year, tilt, panel_area: panelArea,
    panel_efficiency: efficiency, cleanliness, shading, ac_capacity_kw: acCapacity,
    gamma, noct, electricity_price_per_kwh: tariff, currency, system_capex: capex,
  });

  const runForecast = async () => {
    setLoading(true); setError(null); setComparison(null);
    const request = payload();
    const [yearlyResult, dailyResult] = await Promise.allSettled([
      apiPost<YearlyForecastResponse>('/forecast/yearly', request),
      apiPost<SimulationResponse>('/simulate', request),
    ]);
    setForecast(yearlyResult.status === 'fulfilled' ? yearlyResult.value : null);
    setDaily(dailyResult.status === 'fulfilled' ? dailyResult.value : null);
    const messages = [yearlyResult, dailyResult].filter((result) => result.status === 'rejected').map((result) => String((result as PromiseRejectedResult).reason));
    if (messages.length) setError(messages.join(' '));
    setLoading(false);
  };

  const searchLocation = async () => {
    try {
      setError(null);
      const result = await geocode(address);
      if (!result) setError('Location not found.'); else setPosition(result);
    } catch (caught) { setError(caught instanceof Error ? caught.message : 'Location search failed.'); }
  };

  const addScenario = () => {
    const name = scenarioName.trim();
    if (!name) return setError('Scenario name is required.');
    if (name.toLocaleLowerCase() === 'base system' || scenarios.some((item) => item.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      return setError('Scenario names must be unique.');
    }
    setScenarios([...scenarios, {
      name, tilt: scenarioTilt, panel_area: scenarioArea, panel_efficiency: efficiency,
      cleanliness, shading, ac_capacity_kw: scenarioAc, gamma, noct, system_capex: scenarioCapex,
    }]);
    setScenarioName(`Option ${scenarios.length + 2}`); setComparison(null); setError(null);
  };

  const runComparison = async () => {
    if (!scenarios.length) return setError('Add at least one alternative scenario.');
    setLoading(true); setError(null);
    const base = payload();
    const baseScenario: ScenarioComparisonScenarioPayload = {
      name: 'Base System', tilt: base.tilt, panel_area: base.panel_area,
      panel_efficiency: base.panel_efficiency, cleanliness: base.cleanliness, shading: base.shading,
      ac_capacity_kw: base.ac_capacity_kw, gamma: base.gamma, noct: base.noct, system_capex: base.system_capex,
    };
    const request: ScenarioComparisonRequestPayload = {
      context: {latitude: base.latitude, longitude: base.longitude, year: base.year, electricity_price_per_kwh: base.electricity_price_per_kwh, currency: base.currency},
      scenarios: [baseScenario, ...scenarios],
    };
    try { setComparison(await apiPost('/scenarios/compare', request)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Scenario comparison failed.'); }
    finally { setLoading(false); }
  };

  const monthlyData = forecast ? MONTHS.map((month, index) => ({month, energy: forecast.monthly_kwh[index], value: forecast.monthly_estimated_value[index]})) : [];
  const dailyData = daily ? daily.hourly_ac_kw.map((power, index) => ({time: daily.hourly_time[index]?.slice(11, 16) || `${index}:00`, power})) : [];
  const comparisonData = comparison ? MONTHS.map((month, index) => Object.assign({month}, ...comparison.results.map((result) => ({[result.scenario.name]: result.monthly_kwh[index]})))) : [];

  return <div className="min-h-screen bg-background text-foreground">
    <header className="border-b p-5"><h1 className="text-2xl font-bold">Solar Energy Estimator</h1><p className="text-sm text-muted-foreground">Simplified physical PV production, scenarios, and financial analysis</p></header>
    <main className="grid gap-6 p-6 lg:grid-cols-[360px_1fr]">
      <aside className="space-y-4">
        <Card><CardHeader><CardTitle>Location</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="flex gap-2"><Input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Address, city, country"/><Button onClick={searchLocation}>Find</Button></div>
          <div className="h-64 overflow-hidden rounded-md"><MapContainer center={position} zoom={10} key={`${position.lat}-${position.lng}`} className="h-full"><TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><MapPicker position={position} onChange={setPosition}/></MapContainer></div>
          <p className="text-xs text-muted-foreground">{position.lat.toFixed(4)}, {position.lng.toFixed(4)}</p>
        </CardContent></Card>
        <Card><CardHeader><CardTitle>System and finance</CardTitle></CardHeader><CardContent className="grid grid-cols-2 gap-3">
          <Field label="Forecast year" value={year} set={setYear}/><Field label="Panel area (m²)" value={panelArea} set={setPanelArea}/>
          <Field label="Efficiency" value={efficiency} set={setEfficiency} step={0.01}/><Field label="Tilt (°)" value={tilt} set={setTilt}/>
          <Field label="AC capacity (kW)" value={acCapacity} set={setAcCapacity}/><Field label="Temperature coefficient" value={gamma} set={setGamma} step={0.001}/>
          <Field label="NOCT (°C)" value={noct} set={setNoct}/><Field label="Tariff / kWh" value={tariff} set={setTariff} step={0.01}/>
          <div><Label>Cleanliness</Label><Select value={cleanliness} onValueChange={(v) => setCleanliness(v as CleanlinessLevel)}><SelectTrigger><SelectValue/></SelectTrigger><SelectContent>{['clean','normal','dusty'].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent></Select></div>
          <div><Label>Shading</Label><Select value={shading} onValueChange={(v) => setShading(v as ShadingLevel)}><SelectTrigger><SelectValue/></SelectTrigger><SelectContent>{['none','low','medium','high'].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent></Select></div>
          <div><Label>Currency</Label><Select value={currency} onValueChange={(v) => setCurrency(v as CurrencyCode)}><SelectTrigger><SelectValue/></SelectTrigger><SelectContent>{['ILS','USD','EUR'].map(v=><SelectItem key={v} value={v}>{v}</SelectItem>)}</SelectContent></Select></div>
          <Field label="System CAPEX" value={capex} set={setCapex}/>
          <Button className="col-span-2" onClick={runForecast} disabled={loading}>{loading ? 'Running…' : 'Run estimate'}</Button>
        </CardContent></Card>
      </aside>
      <section className="space-y-4">
        {error && <Alert variant="destructive"><AlertTitle>Request issue</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
        <Tabs defaultValue="overview"><TabsList><TabsTrigger value="overview">Overview</TabsTrigger><TabsTrigger value="daily">Day</TabsTrigger><TabsTrigger value="scenarios">Scenarios</TabsTrigger></TabsList>
          <TabsContent value="overview" className="space-y-4">{!forecast ? <Empty/> : <>
            {forecast.fallback_reason && <Alert><AlertTitle>Archive year reused</AlertTitle><AlertDescription>{forecast.fallback_reason}</AlertDescription></Alert>}
            <div className="grid gap-3 md:grid-cols-3"><Metric label="Yearly energy" value={`${forecast.yearly_kwh.toLocaleString()} kWh`}/><Metric label="Annual value" value={money(forecast.annual_savings, currency)}/><Metric label="Simple payback" value={forecast.simple_payback_years == null ? 'Not viable' : `${forecast.simple_payback_years} years`}/></div>
            <Card><CardHeader><CardTitle>Monthly production</CardTitle></CardHeader><CardContent className="h-80"><ResponsiveContainer><BarChart data={monthlyData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip/><Bar dataKey="energy" fill="#2563eb" name="kWh"/></BarChart></ResponsiveContainer></CardContent></Card>
            <Card><CardContent className="pt-6 text-sm"><p>Model: {forecast.production_model}</p><p>Weather: {forecast.weather_source}, reference year {forecast.weather_reference_year}</p><p>Loss and financial assumptions are included in the returned estimate.</p></CardContent></Card>
          </>}</TabsContent>
          <TabsContent value="daily">{!daily ? <Empty/> : <><div className="grid gap-3 md:grid-cols-3"><Metric label="Daily energy" value={`${daily.daily_kwh} kWh`}/><Metric label="Peak power" value={`${Math.max(...daily.hourly_ac_kw).toFixed(2)} kW`}/><Metric label="Daily value" value={money(daily.estimated_daily_value, currency)}/></div><Card className="mt-4"><CardHeader><CardTitle>Hourly AC power</CardTitle></CardHeader><CardContent className="h-80"><ResponsiveContainer><LineChart data={dailyData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="time"/><YAxis/><Tooltip/><Line dataKey="power" stroke="#059669" dot={false}/></LineChart></ResponsiveContainer></CardContent></Card></>}</TabsContent>
          <TabsContent value="scenarios" className="space-y-4"><Card><CardHeader><CardTitle>Add alternative scenario</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-5"><div><Label>Name</Label><Input value={scenarioName} onChange={(e)=>setScenarioName(e.target.value)}/></div><Field label="Area (m²)" value={scenarioArea} set={setScenarioArea}/><Field label="Tilt (°)" value={scenarioTilt} set={setScenarioTilt}/><Field label="AC (kW)" value={scenarioAc} set={setScenarioAc}/><Field label="CAPEX" value={scenarioCapex} set={setScenarioCapex}/><Button onClick={addScenario}>Add scenario</Button><Button onClick={runComparison} disabled={loading || !scenarios.length}>Compare</Button></CardContent></Card>
            <div className="text-sm">{scenarios.map((scenario) => <p key={scenario.name}>{scenario.name}: {scenario.panel_area} m², {scenario.ac_capacity_kw} kW AC</p>)}</div>
            {comparison && <><Card><CardHeader><CardTitle>Monthly scenario production</CardTitle></CardHeader><CardContent className="h-80"><ResponsiveContainer><LineChart data={comparisonData}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip/><Legend/>{comparison.results.map((result,index)=><Line key={result.scenario.name} dataKey={result.scenario.name} stroke={['#2563eb','#059669','#f59e0b','#dc2626'][index%4]} dot={false}/>)}</LineChart></ResponsiveContainer></CardContent></Card><div className="grid gap-3 md:grid-cols-2">{comparison.results.map((result)=><Metric key={result.scenario.name} label={result.scenario.name} value={`${result.yearly_kwh.toLocaleString()} kWh · ${money(result.annual_savings, currency)}`}/>)}</div></>}
          </TabsContent>
        </Tabs>
      </section>
    </main>
  </div>;
}

function Field({label, value, set, step=1}: {label: string; value: number; set: (value: number) => void; step?: number}) {
  return <div><Label>{label}</Label><Input type="number" step={step} value={value} onChange={(event) => set(Number(event.target.value))}/></div>;
}
function Metric({label, value}: {label: string; value: string; key?: string}) { return <Card><CardHeader><CardTitle className="text-sm">{label}</CardTitle></CardHeader><CardContent className="text-xl font-bold">{value}</CardContent></Card>; }
function Empty() { return <div className="rounded-lg border p-12 text-center text-muted-foreground">Run an estimate to see results.</div>; }

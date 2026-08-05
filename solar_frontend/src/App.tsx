import {useEffect, useMemo, useState} from 'react';
import {Languages, Moon, Sun, X} from 'lucide-react';

import {Alert, AlertDescription, AlertTitle} from '@/components/ui/alert';
import {Button} from '@/components/ui/button';
import {APP_DEFAULTS} from '@/lib/defaults';
import {
  apiPost,
  type PVRequestPayload,
  type ScenarioComparisonRequestPayload,
  type ScenarioComparisonResponse,
  type ScenarioComparisonScenarioPayload,
  type SimulationResponse,
  type YearlyForecastResponse,
} from '@/lib/solar-api';
import {
  DashboardSidebar,
  MobileConfigurationBar,
  type ConfigurationValues,
} from '@/src/components/dashboard-sidebar';
import {DashboardTabs} from '@/src/components/dashboard-tabs';
import {
  FinanceView,
  ForecastView,
  MethodologyView,
  OverviewView,
  ScenariosView,
  type ScenarioDraft,
} from '@/src/components/dashboard-views';
import {LoadingBanner} from '@/src/components/dashboard-ui';
import {LocationMap, type Position} from '@/src/components/location-map';
import {UI_COPY, type Language, type SectionId} from '@/src/i18n';

type LoadingAction = 'estimate' | 'comparison' | null;

const INITIAL_POSITION: Position = {lat: 32.0853, lng: 34.7818};

const INITIAL_CONFIGURATION: ConfigurationValues = {
  year: new Date().getFullYear(),
  panelArea: APP_DEFAULTS.panelAreaSqm,
  efficiency: APP_DEFAULTS.panelEfficiency,
  tilt: APP_DEFAULTS.tiltDegrees,
  cleanliness: APP_DEFAULTS.cleanliness,
  shading: APP_DEFAULTS.shading,
  acCapacity: APP_DEFAULTS.acCapacityKw,
  gamma: APP_DEFAULTS.gamma,
  noct: APP_DEFAULTS.noctC,
  tariff: APP_DEFAULTS.electricityPricePerKwh,
  currency: APP_DEFAULTS.currency,
  capex: APP_DEFAULTS.systemCapex,
};

function initialLanguage(): Language {
  if (typeof window === 'undefined') return 'en';
  return window.localStorage.getItem('solar-language') === 'he' ? 'he' : 'en';
}

function initialTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.localStorage.getItem('solar-theme') === 'dark' ? 'dark' : 'light';
}

async function geocode(address: string): Promise<Position | null> {
  const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(address)}`);
  if (!response.ok) throw new Error('geocode-unavailable');
  const body = await response.json() as Array<{lat: string; lon: string}>;
  return body[0] ? {lat: Number(body[0].lat), lng: Number(body[0].lon)} : null;
}

export default function App() {
  const [language, setLanguage] = useState<Language>(initialLanguage);
  const [theme, setTheme] = useState<'light' | 'dark'>(initialTheme);
  const [activeSection, setActiveSection] = useState<SectionId>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [position, setPosition] = useState<Position>(INITIAL_POSITION);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [configuration, setConfiguration] = useState<ConfigurationValues>(INITIAL_CONFIGURATION);
  const [forecast, setForecast] = useState<YearlyForecastResponse | null>(null);
  const [daily, setDaily] = useState<SimulationResponse | null>(null);
  const [comparison, setComparison] = useState<ScenarioComparisonResponse | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioComparisonScenarioPayload[]>([]);
  const [scenarioDraft, setScenarioDraft] = useState<ScenarioDraft>({
    name: `${UI_COPY[initialLanguage()].optionPrefix} 1`,
    panelArea: APP_DEFAULTS.panelAreaSqm * (1 + APP_DEFAULTS.scenarioPanelAreaDeltaPercent / 100),
    tilt: APP_DEFAULTS.tiltDegrees,
    acCapacity: APP_DEFAULTS.acCapacityKw,
    capex: APP_DEFAULTS.systemCapex,
  });
  const [loadingAction, setLoadingAction] = useState<LoadingAction>(null);
  const [error, setError] = useState<string | null>(null);
  const copy = UI_COPY[language];
  const loading = loadingAction !== null;

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
    window.localStorage.setItem('solar-language', language);
  }, [language]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    window.localStorage.setItem('solar-theme', theme);
  }, [theme]);

  const payload = useMemo<PVRequestPayload>(() => ({
    latitude: position.lat,
    longitude: position.lng,
    year: configuration.year,
    tilt: configuration.tilt,
    panel_area: configuration.panelArea,
    panel_efficiency: configuration.efficiency,
    cleanliness: configuration.cleanliness,
    shading: configuration.shading,
    ac_capacity_kw: configuration.acCapacity,
    gamma: configuration.gamma,
    noct: configuration.noct,
    electricity_price_per_kwh: configuration.tariff,
    currency: configuration.currency,
    system_capex: configuration.capex,
  }), [configuration, position]);

  const validateConfiguration = (): string | null => {
    if (!Number.isFinite(position.lat) || !Number.isFinite(position.lng)) return copy.locationRequired;
    if (configuration.panelArea <= 0) return copy.invalidArea;
    if (configuration.acCapacity <= 0) return copy.invalidCapacity;
    if (configuration.efficiency <= 0 || configuration.efficiency > 1) return copy.invalidEfficiency;
    if (configuration.capex < 0) return copy.invalidCapex;
    if (configuration.tariff < 0) return copy.invalidTariff;
    return null;
  };

  const runEstimate = async () => {
    const validationError = validateConfiguration();
    if (validationError) { setError(validationError); return; }
    setLoadingAction('estimate');
    setError(null);
    const [yearlyResult, dailyResult] = await Promise.allSettled([
      apiPost<YearlyForecastResponse>('/forecast/yearly', payload),
      apiPost<SimulationResponse>('/simulate', payload),
    ]);
    const issues: string[] = [];
    if (yearlyResult.status === 'fulfilled') setForecast(yearlyResult.value);
    else { setForecast(null); issues.push(language === 'he' ? `${copy.forecastFailed}: ${copy.apiFailureDetail}` : `${copy.forecastFailed}: ${errorText(yearlyResult.reason)}`); }
    if (dailyResult.status === 'fulfilled') setDaily(dailyResult.value);
    else { setDaily(null); issues.push(language === 'he' ? `${copy.dailyFailed}: ${copy.apiFailureDetail}` : `${copy.dailyFailed}: ${errorText(dailyResult.reason)}`); }
    setComparison(null);
    if (issues.length) setError(issues.join(' '));
    if (yearlyResult.status === 'fulfilled') setActiveSection('overview');
    else if (dailyResult.status === 'fulfilled') setActiveSection('forecast');
    setLoadingAction(null);
  };

  const searchLocation = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const result = await geocode(searchQuery);
      if (result) { setPosition(result); setComparison(null); }
      else setError(copy.locationNotFound);
    } catch {
      setError(copy.locationSearchFailed);
    } finally {
      setSearching(false);
    }
  };

  const addScenario = () => {
    const name = scenarioDraft.name.trim();
    if (!name) { setError(copy.scenarioNameRequired); return; }
    const reservedNames = ['base system', 'מערכת בסיס'];
    if (reservedNames.includes(name.toLocaleLowerCase()) || scenarios.some((scenario) => scenario.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      setError(copy.scenarioNameUnique);
      return;
    }
    if (scenarioDraft.panelArea <= 0) { setError(copy.invalidArea); return; }
    if (scenarioDraft.acCapacity <= 0) { setError(copy.invalidCapacity); return; }
    if (scenarioDraft.capex < 0) { setError(copy.invalidCapex); return; }
    const next: ScenarioComparisonScenarioPayload = {
      name,
      tilt: scenarioDraft.tilt,
      panel_area: scenarioDraft.panelArea,
      panel_efficiency: configuration.efficiency,
      cleanliness: configuration.cleanliness,
      shading: configuration.shading,
      ac_capacity_kw: scenarioDraft.acCapacity,
      gamma: configuration.gamma,
      noct: configuration.noct,
      system_capex: scenarioDraft.capex,
    };
    setScenarios((current) => [...current, next]);
    setScenarioDraft((current) => ({...current, name: `${copy.optionPrefix} ${scenarios.length + 2}`}));
    setComparison(null);
    setError(null);
  };

  const runComparison = async () => {
    const validationError = validateConfiguration();
    if (validationError) { setError(validationError); return; }
    if (!scenarios.length) { setError(copy.scenarioRequired); return; }
    setLoadingAction('comparison');
    setError(null);
    const baseScenario: ScenarioComparisonScenarioPayload = {
      name: 'Base System',
      tilt: payload.tilt,
      panel_area: payload.panel_area,
      panel_efficiency: payload.panel_efficiency,
      cleanliness: payload.cleanliness,
      shading: payload.shading,
      ac_capacity_kw: payload.ac_capacity_kw,
      gamma: payload.gamma,
      noct: payload.noct,
      system_capex: payload.system_capex,
    };
    const request: ScenarioComparisonRequestPayload = {
      context: {
        latitude: payload.latitude,
        longitude: payload.longitude,
        year: payload.year,
        electricity_price_per_kwh: payload.electricity_price_per_kwh,
        currency: payload.currency,
      },
      scenarios: [baseScenario, ...scenarios],
    };
    try {
      setComparison(await apiPost<ScenarioComparisonResponse>('/scenarios/compare', request));
    } catch (caught) {
      setComparison(null);
      setError(language === 'he' ? `${copy.comparisonFailed} ${copy.apiFailureDetail}` : `${copy.comparisonFailed} ${errorText(caught)}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const switchLanguage = () => {
    const nextLanguage = language === 'he' ? 'en' : 'he';
    const optionNumber = scenarioDraft.name.match(/^(?:Option|אפשרות)\s+(\d+)$/)?.[1];
    if (optionNumber) setScenarioDraft((current) => ({...current, name: `${UI_COPY[nextLanguage].optionPrefix} ${optionNumber}`}));
    setLanguage(nextLanguage);
  };

  const content = (() => {
    switch (activeSection) {
      case 'overview': return <OverviewView copy={copy} language={language} forecast={forecast} />;
      case 'forecast': return <ForecastView copy={copy} language={language} daily={daily} />;
      case 'scenarios': return <ScenariosView copy={copy} language={language} currency={configuration.currency} draft={scenarioDraft} onDraftChange={(changes) => setScenarioDraft((current) => ({...current, ...changes}))} scenarios={scenarios} onAdd={addScenario} onRemove={(name) => {setScenarios((current) => current.filter((scenario) => scenario.name !== name)); setComparison(null);}} onCompare={runComparison} comparison={comparison} loading={loadingAction === 'comparison'} />;
      case 'finance': return <FinanceView copy={copy} language={language} forecast={forecast} />;
      case 'methodology': return <MethodologyView copy={copy} />;
    }
  })();

  return <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(14,165,233,0.08),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(245,158,11,0.06),transparent_28%)] text-foreground" dir={language === 'he' ? 'rtl' : 'ltr'}>
    <div className="flex min-h-screen">
      <DashboardSidebar
        language={language}
        copy={copy}
        collapsed={sidebarCollapsed}
        onCollapsedChange={setSidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onMobileOpenChange={setMobileSidebarOpen}
        values={configuration}
        onValuesChange={(changes) => {setConfiguration((current) => ({...current, ...changes})); setComparison(null);}}
        onRun={runEstimate}
        loading={loadingAction === 'estimate'}
      />

      <div className="min-w-0 flex-1">
        <header className="border-b bg-background/85 backdrop-blur-xl">
          <div className="flex min-h-24 items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/20"><Sun className="size-6" /></span>
              <div className="min-w-0"><h1 className="truncate text-xl font-black tracking-tight sm:text-2xl">{copy.appTitle}</h1><p className="mt-0.5 hidden max-w-3xl text-xs text-muted-foreground sm:block lg:text-sm">{copy.appSubtitle}</p></div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Button variant="outline" onClick={switchLanguage}><Languages />{copy.languageButton}</Button>
              <Button variant="outline" size="icon" onClick={() => setTheme((current) => current === 'light' ? 'dark' : 'light')} aria-label={copy.themeToggle} title={copy.themeToggle}>{theme === 'light' ? <Moon /> : <Sun />}</Button>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1600px] px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
          <MobileConfigurationBar copy={copy} onOpen={() => setMobileSidebarOpen(true)} />
          <LocationMap
            language={language}
            copy={copy}
            position={position}
            onPositionChange={(next) => {setPosition(next); setComparison(null);}}
            panelArea={configuration.panelArea}
            onPanelAreaChange={(panelArea) => {setConfiguration((current) => ({...current, panelArea})); setComparison(null);}}
            searchQuery={searchQuery}
            onSearchQueryChange={setSearchQuery}
            onSearch={searchLocation}
            searching={searching}
          />
          <DashboardTabs copy={copy} activeSection={activeSection} onChange={setActiveSection}>
            {error && <Alert variant="destructive" className="mb-5 bg-background shadow-sm" role="alert"><AlertTitle>{copy.requestIssue}</AlertTitle><AlertDescription className="pe-8">{error}</AlertDescription><Button variant="ghost" size="icon-sm" className="absolute end-3 top-3" onClick={() => setError(null)} aria-label={copy.dismiss}><X /></Button></Alert>}
            {loading && <LoadingBanner title={copy.loadingTitle} description={copy.loadingDescription} />}
            <div className={loading ? 'pointer-events-none opacity-70 transition-opacity' : 'transition-opacity'}>{content}</div>
          </DashboardTabs>
        </main>
      </div>
    </div>
  </div>;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

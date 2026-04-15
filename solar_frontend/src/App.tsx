/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef, useState, type CSSProperties, type MouseEvent as ReactMouseEvent, type MutableRefObject } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { DollarSign, GripVertical, Info, MapPin, Moon, PanelLeftClose, PanelLeftOpen, Settings, Sun } from 'lucide-react';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  apiPost,
  type BenchmarkApproachType,
  type AccuracyEvaluationResponse,
  type BenchmarkEvaluationPayload,
  type BenchmarkEvaluationResponse,
  type CleanlinessLevel,
  type CurrencyCode,
  type ModelType,
  type PVRequestPayload,
  type ScenarioComparisonRequestPayload,
  type ScenarioComparisonResponse,
  type ScenarioComparisonScenarioPayload,
  type ShadingLevel,
  type SimulationResponse,
  type YearlyForecastResponse,
} from '@/lib/solar-api';

if (typeof window !== 'undefined') {
  (window as { type?: string }).type = '';
}

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const CHART_COLORS = ['#2563eb', '#059669', '#f59e0b', '#dc2626', '#7c3aed'];
const DEFAULT_FEED_IN_TARIFF_ILS = 0.48;
const DEFAULT_CURRENCY: CurrencyCode = 'ILS';
const DEFAULT_SIDEBAR_WIDTH = 368;
const MIN_SIDEBAR_WIDTH = 304;
const MAX_SIDEBAR_WIDTH = 560;
const COLLAPSED_SIDEBAR_WIDTH = 72;
const FORECAST_APPROACH_COPY: Record<
  ModelType,
  { label: string; shortLabel: string; description: string }
> = {
  physical: {
    label: 'Physics-based forecast',
    shortLabel: 'Physics-based',
    description: 'Uses panel setup, tilt, and weather assumptions to estimate output.',
  },
  ml: {
    label: 'History-based forecast',
    shortLabel: 'History-based',
    description: 'Learns patterns from past years to estimate future output.',
  },
};

type MapPosition = { lat: number; lng: number };
type ScenarioRequest = { name: string; payload: PVRequestPayload };
type BenchmarkSummaryRow = {
  id: string;
  label: string;
  monthlyMape: number;
  monthlyMaeKwh: number;
  yearlyMape: number;
  yearlyMaeKwh: number;
  biasPercent: number;
  biasKwh: number;
  absBiasPercent: number;
  fallbackCount: number;
  fallbackSummary: string;
  biasDirection: string;
};

type RankedBenchmarkSummaryRow = BenchmarkSummaryRow & {
  overallRankScore: number;
  yearlyErrorRank: number;
  monthlyErrorRank: number;
  biasRank: number;
};

type AccuracyQuality = AccuracyEvaluationResponse['quality'];
type ScenarioOptionRow = {
  id: string;
  label: string;
  isBaseline: boolean;
  yearlyKwh: number;
  annualSavings: number;
  simplePaybackYears: number | null;
  paybackDeltaYears: number | null;
  capex: number;
  currency: CurrencyCode;
  energyDeltaPercent: number;
  energyDeltaKwh: number;
  savingsDeltaPercent: number;
  savingsDeltaValue: number;
};
type ScenarioRecommendationMode = 'payback' | 'savings';

const PREDEFINED_LOCATIONS = [
  { id: 'telaviv', label: 'Tel Aviv, Israel', lat: 32.0853, lng: 34.7818 },
  { id: 'newyork', label: 'New York, USA', lat: 40.7128, lng: -74.006 },
  { id: 'london', label: 'London, UK', lat: 51.5074, lng: -0.1278 },
  { id: 'tokyo', label: 'Tokyo, Japan', lat: 35.6762, lng: 139.6503 },
  { id: 'sydney', label: 'Sydney, Australia', lat: -33.8688, lng: 151.2093 },
  { id: 'berlin', label: 'Berlin, Germany', lat: 52.52, lng: 13.405 },
  { id: 'paris', label: 'Paris, France', lat: 48.8566, lng: 2.3522 },
  { id: 'sanfrancisco', label: 'San Francisco, USA', lat: 37.7749, lng: -122.4194 },
];

function formatPaybackYears(paybackYears: number | null | undefined): string {
  if (paybackYears == null || Number.isNaN(paybackYears)) {
    return 'Not viable';
  }
  return `${formatReadableNumber(paybackYears, 1)} years`;
}

function formatHourlyLabel(value: string, fallbackIndex: number): string {
  if (!value) {
    return `${fallbackIndex.toString().padStart(2, '0')}:00`;
  }
  if (value.includes('T')) {
    return value.split('T')[1]?.slice(0, 5) || value;
  }
  return value.slice(0, 5);
}

function formatSimulationDateLabel(value: string): string {
  if (!value) {
    return 'Next forecast day';
  }

  const datePart = value.includes('T') ? value.split('T')[0] : value.slice(0, 10);
  const [year, month, day] = datePart.split('-').map((segment) => Number(segment));

  if ([year, month, day].every((part) => Number.isFinite(part))) {
    return new Date(year, month - 1, day).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  return datePart;
}

function estimateAreaM2FromBounds(bounds: L.LatLngBounds) {
  const lat1 = bounds.getSouth();
  const lat2 = bounds.getNorth();
  const lon1 = bounds.getWest();
  const lon2 = bounds.getEast();

  const metersPerDegLat = 111000;
  const metersPerDegLon = 111000 * Math.cos(((lat1 + lat2) / 2) * (Math.PI / 180));

  const width = Math.abs(lon2 - lon1) * metersPerDegLon;
  const height = Math.abs(lat2 - lat1) * metersPerDegLat;

  return width * height;
}

async function geocodeAddress(address: string) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`,
    );
    const data = await response.json();
    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
        address: (data[0].display_name as string | undefined) || address,
      };
    }
  } catch (error) {
    console.error('Geocoding failed', error);
  }
  return null;
}

async function reverseGeocode(lat: number, lon: number) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`,
    );
    const data = await response.json();
    if (data && data.display_name) {
      return data.display_name as string;
    }
  } catch (error) {
    console.error('Reverse geocoding failed', error);
  }
  return null;
}

function buildBenchmarkPayload(
  basePayload: PVRequestPayload,
  benchmarkYears: number,
  evaluationYear: number,
): BenchmarkEvaluationPayload {
  return {
    latitude: basePayload.latitude,
    longitude: basePayload.longitude,
    year: evaluationYear,
    benchmark_years: benchmarkYears,
    tilt: basePayload.tilt,
    panel_area: basePayload.panel_area,
    panel_efficiency: basePayload.panel_efficiency,
    cleanliness: basePayload.cleanliness,
    shading: basePayload.shading,
    ac_capacity_kw: basePayload.ac_capacity_kw,
    gamma: basePayload.gamma,
    noct: basePayload.noct,
    system_capex: basePayload.system_capex,
    training_years: basePayload.training_years,
  };
}

function buildScenarioComparisonPayload(
  basePayload: PVRequestPayload,
  scenarioRequests: ScenarioRequest[],
): ScenarioComparisonRequestPayload {
  const scenarios: ScenarioComparisonScenarioPayload[] = [
    {
      name: 'Base System',
      tilt: basePayload.tilt,
      panel_area: basePayload.panel_area,
      panel_efficiency: basePayload.panel_efficiency,
      cleanliness: basePayload.cleanliness,
      shading: basePayload.shading,
      ac_capacity_kw: basePayload.ac_capacity_kw,
      gamma: basePayload.gamma,
      noct: basePayload.noct,
      system_capex: basePayload.system_capex,
    },
    ...scenarioRequests.map((scenario) => ({
      name: scenario.name,
      tilt: scenario.payload.tilt,
      panel_area: scenario.payload.panel_area,
      panel_efficiency: scenario.payload.panel_efficiency,
      cleanliness: scenario.payload.cleanliness,
      shading: scenario.payload.shading,
      ac_capacity_kw: scenario.payload.ac_capacity_kw,
      gamma: scenario.payload.gamma,
      noct: scenario.payload.noct,
      system_capex: scenario.payload.system_capex,
    })),
  ];

  return {
    context: {
      latitude: basePayload.latitude,
      longitude: basePayload.longitude,
      year: basePayload.year,
      model_type: basePayload.model_type,
      training_years: basePayload.training_years,
      electricity_price_per_kwh: basePayload.electricity_price_per_kwh,
      currency: basePayload.currency,
    },
    scenarios,
  };
}

function getSliderNumber(value: number | undefined, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function getSliderValue(value: number | undefined, fallback: number): number {
  return getSliderNumber(value, fallback);
}

function getSliderChangeValue(value: number | readonly number[] | undefined, fallback: number): number {
  if (typeof value === 'number') {
    return getSliderNumber(value, fallback);
  }
  if (Array.isArray(value)) {
    return getSliderNumber(value[0], fallback);
  }
  return fallback;
}

function formatSidebarNumber(value: number | string | undefined, digits = 1): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return '--';
  }
  if (Number.isInteger(parsed)) {
    return String(parsed);
  }
  return parsed.toFixed(digits).replace(/\.?0+$/, '');
}

function formatReadableNumber(value: number | string | undefined, digits = 1): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return '--';
  }

  return parsed.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: Number.isInteger(parsed) ? 0 : digits,
  });
}

function formatReadableKwh(value: number | string | undefined, digits = 0): string {
  return `${formatReadableNumber(value, digits)} kWh`;
}

function formatReadableCurrency(value: number | string | undefined, currency: CurrencyCode | string, digits = 0): string {
  return `${formatReadableNumber(value, digits)} ${currency}`;
}

function formatSignedNumber(value: number | string | undefined, digits = 1): string {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return '--';
  }

  const formatted = formatSidebarNumber(parsed, digits);
  if (parsed > 0) {
    return `+${formatted}`;
  }
  return formatted;
}

function getForecastApproachLabel(modelType: ModelType): string {
  return FORECAST_APPROACH_COPY[modelType].label;
}

function getForecastApproachShortLabel(modelType: ModelType): string {
  return FORECAST_APPROACH_COPY[modelType].shortLabel;
}

function getForecastApproachDescription(modelType: ModelType): string {
  return FORECAST_APPROACH_COPY[modelType].description;
}

function getBenchmarkApproachLabel(approachType: BenchmarkApproachType, fallbackLabel: string): string {
  if (approachType === 'physical' || approachType === 'ml') {
    return getForecastApproachLabel(approachType);
  }
  return fallbackLabel;
}

function formatLearningYearsUsed(years: number[] | undefined): string {
  return years && years.length > 0 ? years.join(', ') : 'Not used';
}

function describeBiasDirection(biasPercent: number): string {
  if (!Number.isFinite(biasPercent) || Math.abs(biasPercent) < 1) {
    return 'Bias is close to neutral';
  }
  return biasPercent > 0 ? 'Tends to overpredict' : 'Tends to underpredict';
}

function formatFallbackSummary(fallbackYears: number[]): string {
  if (fallbackYears.length === 0) {
    return 'No backup logic used';
  }
  if (fallbackYears.length === 1) {
    return `1 year: ${fallbackYears[0]}`;
  }
  return `${fallbackYears.length} years: ${fallbackYears.join(', ')}`;
}

function buildBenchmarkRankMap(
  rows: BenchmarkSummaryRow[],
  valueSelector: (row: BenchmarkSummaryRow) => number,
): Map<string, number> {
  return new Map(
    [...rows]
      .sort((left, right) => valueSelector(left) - valueSelector(right))
      .map((row, index) => [row.id, index + 1]),
  );
}

function getAccuracyQualityDescription(quality: AccuracyQuality): string {
  if (quality === 'EXCELLENT') {
    return 'Monthly error stayed under 10%.';
  }
  if (quality === 'GOOD') {
    return 'Monthly error stayed under 25%, but there is still noticeable spread month to month.';
  }
  return 'Monthly error reached 25% or more, so the forecast should be used with caution.';
}

function getAccuracyQualityClassName(quality: AccuracyQuality): string {
  if (quality === 'EXCELLENT') {
    return 'text-emerald-600';
  }
  if (quality === 'GOOD') {
    return 'text-amber-600';
  }
  return 'text-rose-600';
}

function buildAccuracyTakeaway(quality: AccuracyQuality, biasPercent: number): { headline: string; description: string } {
  const biasDirection = describeBiasDirection(biasPercent);
  const biasDirectionLower = biasDirection.toLowerCase();

  if (quality === 'EXCELLENT') {
    return {
      headline: 'This method matched the selected year closely',
      description:
        Math.abs(biasPercent) < 5
          ? 'Monthly and yearly misses stayed low, and the forecast stayed close to neutral overall.'
          : `Monthly and yearly misses stayed low, although it still ${biasDirectionLower}.`,
    };
  }

  if (quality === 'GOOD') {
    return {
      headline: 'This method was directionally useful, but monthly swings still matter',
      description:
        biasDirection === 'Bias is close to neutral'
          ? 'The forecast followed the overall year reasonably well without a strong high or low tendency.'
          : `The forecast followed the overall year reasonably well, but it still ${biasDirectionLower}.`,
    };
  }

  return {
    headline: 'This method struggled on the selected year',
    description:
      biasDirection === 'Bias is close to neutral'
        ? 'The forecast missed the archived pattern by a wide margin even without a strong high or low tendency.'
        : `The forecast missed the archived pattern by a wide margin and ${biasDirectionLower}.`,
  };
}

function formatPaybackDelta(actual: number | null | undefined, predicted: number | null | undefined): string {
  if (actual == null || predicted == null || Number.isNaN(actual) || Number.isNaN(predicted)) {
    return 'Not comparable';
  }
  return `${formatSignedNumber(predicted - actual, 1)} years`;
}

function formatCurrencyAmount(value: number | string | undefined, currency: CurrencyCode | string, digits = 1): string {
  return `${formatSidebarNumber(value, digits)} ${currency}`;
}

function formatSignedPercent(value: number | undefined, digits = 2): string {
  return `${formatSignedNumber(value, digits)}%`;
}

function formatSignedCurrency(value: number | undefined, currency: CurrencyCode | string, digits = 1): string {
  return `${formatSignedNumber(value, digits)} ${currency}`;
}

function getDeltaToneClass(value: number | null | undefined, positiveIsGood = true): string {
  if (value == null || !Number.isFinite(value) || Math.abs(value) < 0.005) {
    return 'text-muted-foreground';
  }

  const isGood = positiveIsGood ? value > 0 : value < 0;
  return isGood ? 'text-emerald-600' : 'text-rose-600';
}

function formatWeatherReferenceLabel(weatherReferenceYear: number | null | undefined): string {
  return weatherReferenceYear == null ? 'Model-generated weather profile' : `Archived weather from ${weatherReferenceYear}`;
}

function selectScenarioRecommendation(
  rows: ScenarioOptionRow[],
): { mode: ScenarioRecommendationMode; row: ScenarioOptionRow | null } {
  const viablePaybackRows = rows.filter(
    (row) => row.simplePaybackYears != null && Number.isFinite(row.simplePaybackYears),
  );

  if (viablePaybackRows.length > 0) {
    const row = viablePaybackRows.reduce((best, current) => {
      if (!best) {
        return current;
      }

      const paybackDifference = (current.simplePaybackYears ?? Infinity) - (best.simplePaybackYears ?? Infinity);
      if (Math.abs(paybackDifference) > 0.1) {
        return paybackDifference < 0 ? current : best;
      }
      if (current.annualSavings !== best.annualSavings) {
        return current.annualSavings > best.annualSavings ? current : best;
      }
      if (current.yearlyKwh !== best.yearlyKwh) {
        return current.yearlyKwh > best.yearlyKwh ? current : best;
      }
      return best;
    }, viablePaybackRows[0]);

    return { mode: 'payback', row };
  }

  if (rows.length === 0) {
    return { mode: 'payback', row: null };
  }

  const row = rows.reduce((best, current) => {
    if (!best) {
      return current;
    }
    if (current.annualSavings !== best.annualSavings) {
      return current.annualSavings > best.annualSavings ? current : best;
    }
    if (current.yearlyKwh !== best.yearlyKwh) {
      return current.yearlyKwh > best.yearlyKwh ? current : best;
    }
    return best;
  }, rows[0]);

  return { mode: 'savings', row };
}

function MapViewportSync({
  position,
  zoom = 18,
}: {
  position: MapPosition;
  zoom?: number;
}) {
  const map = useMap();

  useEffect(() => {
    map.flyTo([position.lat, position.lng], zoom, {
      animate: true,
      duration: 0.8,
    });
  }, [map, position.lat, position.lng, zoom]);

  return null;
}

function LocationMarker({
  position,
  setPosition,
  setAddress,
  clearShapes,
  isDrawingRef,
  setSelectedLocationId,
}: {
  position: MapPosition | null;
  setPosition: (value: MapPosition) => void;
  setAddress: (value: string | null) => void;
  clearShapes: () => void;
  isDrawingRef: MutableRefObject<boolean>;
  setSelectedLocationId: (value: string) => void;
}) {
  useMapEvents({
    click(event) {
      if (isDrawingRef.current) {
        return;
      }

      clearShapes();
      setPosition(event.latlng);
      setSelectedLocationId('custom');
      reverseGeocode(event.latlng.lat, event.latlng.lng).then((address) => {
        if (address) {
          setAddress(address);
        }
      });
    },
  });

  if (position === null) {
    return null;
  }

  return (
    <Marker position={position}>
      <Popup>Selected Location</Popup>
    </Marker>
  );
}

export default function App() {
  const currentYear = new Date().getFullYear();
  const lastCompleteYear = currentYear - 1;

  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [selectedLocationId, setSelectedLocationId] = useState('');
  const [position, setPosition] = useState<MapPosition | null>(null);
  const [detectedAddress, setDetectedAddress] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const [forecastYear, setForecastYear] = useState<string | number>(currentYear);
  const [panelArea, setPanelArea] = useState<string | number>(80);
  const [acCapacityKw, setAcCapacityKw] = useState<string | number>(15);
  const [modelType, setModelType] = useState<ModelType>('physical');
  const [trainingYears, setTrainingYears] = useState(3);
  const [electricityPrice, setElectricityPrice] = useState<string | number>(DEFAULT_FEED_IN_TARIFF_ILS);
  const [currency, setCurrency] = useState<CurrencyCode>(DEFAULT_CURRENCY);
  const [systemCapex, setSystemCapex] = useState<string | number>(25000);

  const [panelEfficiency, setPanelEfficiency] = useState(0.2);
  const [tilt, setTilt] = useState(30);
  const [cleanliness, setCleanliness] = useState<CleanlinessLevel>('normal');
  const [shading, setShading] = useState<ShadingLevel>('low');
  const [gamma, setGamma] = useState<string | number>(0.004);
  const [noct, setNoct] = useState<string | number>(45);
  const [benchmarkYears, setBenchmarkYears] = useState(3);

  const [forecastData, setForecastData] = useState<YearlyForecastResponse | null>(null);
  const [dailySimulation, setDailySimulation] = useState<SimulationResponse | null>(null);
  const [accuracyResult, setAccuracyResult] = useState<AccuracyEvaluationResponse | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkEvaluationResponse | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ScenarioComparisonResponse | null>(null);
  const [scenarioRequests, setScenarioRequests] = useState<ScenarioRequest[]>([]);

  const [scenarioName, setScenarioName] = useState('Option 1');
  const [scenarioPanelAreaDelta, setScenarioPanelAreaDelta] = useState(20);
  const [scenarioTilt, setScenarioTilt] = useState(30);
  const [scenarioAcCapacity, setScenarioAcCapacity] = useState<string | number>(15);
  const [scenarioCapex, setScenarioCapex] = useState<string | number>(25000);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isSidebarResizing, setIsSidebarResizing] = useState(false);

  const featureGroupRef = useRef<L.FeatureGroup | null>(null);
  const isDrawingRef = useRef(false);
  const sidebarResizeStateRef = useRef<{ startX: number; startWidth: number } | null>(null);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  useEffect(() => {
    if (!isSidebarResizing) {
      return;
    }

    const handleMouseMove = (event: MouseEvent) => {
      if (!sidebarResizeStateRef.current) {
        return;
      }

      const deltaX = event.clientX - sidebarResizeStateRef.current.startX;
      const nextWidth = Math.min(
        MAX_SIDEBAR_WIDTH,
        Math.max(MIN_SIDEBAR_WIDTH, sidebarResizeStateRef.current.startWidth + deltaX),
      );
      setSidebarWidth(nextWidth);
    };

    const handleMouseUp = () => {
      sidebarResizeStateRef.current = null;
      setIsSidebarResizing(false);
      document.body.style.removeProperty('cursor');
      document.body.style.removeProperty('user-select');
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.removeProperty('cursor');
      document.body.style.removeProperty('user-select');
    };
  }, [isSidebarResizing]);

  const selectedForecastYear = Number.isFinite(Number(forecastYear)) ? Number(forecastYear) : currentYear;
  const evaluationYear = Math.min(selectedForecastYear, lastCompleteYear);

  const clearShapes = () => {
    featureGroupRef.current?.clearLayers();
  };

  const handleSidebarResizeStart = (event: ReactMouseEvent<HTMLButtonElement>) => {
    if (sidebarCollapsed || window.innerWidth < 768) {
      return;
    }

    sidebarResizeStateRef.current = {
      startX: event.clientX,
      startWidth: sidebarWidth,
    };
    setIsSidebarResizing(true);
  };

  const handleCreated = (event: { layer: L.Layer & { getBounds: () => L.LatLngBounds } }) => {
    const layer = event.layer;

    featureGroupRef.current?.eachLayer((currentLayer) => {
      if (currentLayer !== layer) {
        featureGroupRef.current?.removeLayer(currentLayer);
      }
    });

    const bounds = layer.getBounds();
    const area = estimateAreaM2FromBounds(bounds);
    const center = bounds.getCenter();

    setPanelArea(Number(area.toFixed(2)));
    setPosition({ lat: center.lat, lng: center.lng });
    setSelectedLocationId('custom');

    reverseGeocode(center.lat, center.lng).then((address) => {
      if (address) {
        setDetectedAddress(address);
      }
    });
  };

  const handleSearchLocation = async () => {
    if (!searchQuery.trim()) {
      return;
    }

    setIsSearching(true);
    const coords = await geocodeAddress(searchQuery);

    if (coords) {
      setPosition({ lat: coords.lat, lng: coords.lon });
      setSelectedLocationId('custom');
      setDetectedAddress(coords.address);
      clearShapes();
    } else {
      alert('Location not found. Please try a different search term.');
    }

    setIsSearching(false);
  };

  const validateInputs = () => {
    if (!position) {
      return 'Select a valid location before running a backend request.';
    }
    if (Number(panelArea) <= 0) {
      return 'Panel area must be greater than zero.';
    }
    if (Number(acCapacityKw) <= 0) {
      return 'Inverter AC capacity must be greater than zero.';
    }
    if (Number(systemCapex) < 0) {
      return 'System CAPEX cannot be negative.';
    }
    return null;
  };

  const buildPayload = (): PVRequestPayload => ({
    latitude: position?.lat ?? 0,
    longitude: position?.lng ?? 0,
    year: Number(forecastYear) || currentYear,
    tilt,
    panel_area: Number(panelArea),
    panel_efficiency: panelEfficiency,
    cleanliness,
    shading,
    ac_capacity_kw: Number(acCapacityKw),
    gamma: Number(gamma),
    noct: Number(noct),
    model_type: modelType,
    electricity_price_per_kwh: Number(electricityPrice),
    currency,
    system_capex: Number(systemCapex),
    training_years: trainingYears,
  });

  const handleRunForecast = async () => {
    const validationMessage = validateInputs();
    if (validationMessage) {
      setApiError(validationMessage);
      return;
    }

    setIsLoading(true);
    setApiError(null);

    try {
      const payload = buildPayload();
      const [forecastResponse, simulationResponse] = await Promise.allSettled([
        apiPost<YearlyForecastResponse>('/forecast/yearly', payload),
        apiPost<SimulationResponse>('/simulate', payload),
      ]);

      const errors: string[] = [];

      if (forecastResponse.status === 'fulfilled') {
        setForecastData(forecastResponse.value);
      } else {
        setForecastData(null);
        errors.push(`Forecast failed: ${forecastResponse.reason instanceof Error ? forecastResponse.reason.message : 'Unknown error'}`);
      }

      if (simulationResponse.status === 'fulfilled') {
        setDailySimulation(simulationResponse.value);
      } else {
        setDailySimulation(null);
        errors.push(`Daily simulation failed: ${simulationResponse.reason instanceof Error ? simulationResponse.reason.message : 'Unknown error'}`);
      }

      setAccuracyResult(null);
      setBenchmarkResult(null);
      setComparisonResult(null);

      if (errors.length > 0) {
        setApiError(errors.join(' '));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunAccuracy = async () => {
    const validationMessage = validateInputs();
    if (validationMessage) {
      setApiError(validationMessage);
      return;
    }

    setIsLoading(true);
    setApiError(null);

    try {
      const payload = { ...buildPayload(), year: evaluationYear };
      const response = await apiPost<AccuracyEvaluationResponse>('/evaluation/accuracy', payload);
      setAccuracyResult(response);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : 'Accuracy request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    const validationMessage = validateInputs();
    if (validationMessage) {
      setApiError(validationMessage);
      return;
    }

    setIsLoading(true);
    setApiError(null);

    try {
      const payload = buildBenchmarkPayload(buildPayload(), benchmarkYears, evaluationYear);
      const response = await apiPost<BenchmarkEvaluationResponse>('/evaluation/benchmark', payload);
      setBenchmarkResult(response);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : 'Benchmark request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddScenario = () => {
    const validationMessage = validateInputs();
    if (validationMessage) {
      setApiError(validationMessage);
      return;
    }
    if (Number(scenarioAcCapacity) <= 0) {
      setApiError('Option AC capacity must be greater than zero.');
      return;
    }
    if (Number(scenarioCapex) < 0) {
      setApiError('Option CAPEX cannot be negative.');
      return;
    }

    const payload = buildPayload();
    payload.panel_area = Number((payload.panel_area * (1 + scenarioPanelAreaDelta / 100)).toFixed(2));
    payload.tilt = scenarioTilt;
    payload.ac_capacity_kw = Number(scenarioAcCapacity);
    payload.system_capex = Number(scenarioCapex);

    setScenarioRequests((current) => [...current, { name: scenarioName.trim() || `Option ${current.length + 1}`, payload }]);
    setScenarioName(`Option ${scenarioRequests.length + 2}`);
    setComparisonResult(null);
    setApiError(null);
  };

  const handleRunComparison = async () => {
    const validationMessage = validateInputs();
    if (validationMessage) {
      setApiError(validationMessage);
      return;
    }
    if (scenarioRequests.length === 0) {
      setApiError('Add at least one alternative option before running comparison.');
      return;
    }

    setIsLoading(true);
    setApiError(null);

    try {
      const payload = buildScenarioComparisonPayload(buildPayload(), scenarioRequests);
      const response = await apiPost<ScenarioComparisonResponse>('/scenarios/compare', payload);
      setComparisonResult(response);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : 'System options comparison failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleScenarioPanelAreaDeltaChange = (value: number | readonly number[]) => {
    setScenarioPanelAreaDelta(getSliderChangeValue(value, 20));
  };

  const handleScenarioTiltChange = (value: number | readonly number[]) => {
    setScenarioTilt(getSliderChangeValue(value, 30));
  };

  const handleBenchmarkYearsChange = (value: number | readonly number[]) => {
    setBenchmarkYears(getSliderChangeValue(value, 3));
  };

  const handleTrainingYearsChange = (value: number | readonly number[]) => {
    setTrainingYears(getSliderChangeValue(value, 3));
  };

  const handlePanelEfficiencyChange = (value: number | readonly number[]) => {
    setPanelEfficiency(getSliderChangeValue(value, 0.2));
  };

  const handleTiltChange = (value: number | readonly number[]) => {
    setTilt(getSliderChangeValue(value, 30));
  };

  const comparisonChartData = comparisonResult
    ? MONTH_NAMES.map((month, monthIndex) => {
        const row: Record<string, string | number> = { name: month };
        comparisonResult.results.forEach((result) => {
          row[result.scenario.name] = result.monthly_kwh[monthIndex] ?? 0;
        });
        return row;
      })
    : [];

  const benchmarkEnergyChartData = benchmarkResult
    ? benchmarkResult.evaluation_years.map((year) => {
        const row: Record<string, string | number> = { year: String(year) };
        const actualReference = benchmarkResult.approaches[0]?.yearly_results.find((result) => result.year === year);
        row['Historical reference'] = actualReference?.actual_yearly_kwh ?? 0;
        benchmarkResult.approaches.forEach((approach) => {
          const displayLabel = getBenchmarkApproachLabel(approach.approach, approach.label);
          row[displayLabel] = approach.yearly_results.find((result) => result.year === year)?.predicted_yearly_kwh ?? 0;
        });
        return row;
      })
    : [];

  const benchmarkMetricChartData = benchmarkResult
    ? benchmarkResult.approaches.map((approach) => ({
        approach: getBenchmarkApproachLabel(approach.approach, approach.label),
        'Avg monthly error (kWh)': approach.metrics.monthly_mae_kwh,
        'Avg yearly error (kWh)': approach.metrics.yearly_mae_kwh,
        'Average bias (kWh)': approach.metrics.bias_kwh,
      }))
    : [];

  const benchmarkSummaryRows: BenchmarkSummaryRow[] = benchmarkResult
    ? benchmarkResult.approaches.map((approach) => ({
        id: approach.approach,
        label: getBenchmarkApproachLabel(approach.approach, approach.label),
        monthlyMape: approach.metrics.monthly_mape_percent,
        monthlyMaeKwh: approach.metrics.monthly_mae_kwh,
        yearlyMape: approach.metrics.yearly_mape_percent,
        yearlyMaeKwh: approach.metrics.yearly_mae_kwh,
        biasPercent: approach.metrics.bias_percent,
        biasKwh: approach.metrics.bias_kwh,
        absBiasPercent: Math.abs(approach.metrics.bias_percent),
        fallbackCount: approach.fallback_years.length,
        fallbackSummary: formatFallbackSummary(approach.fallback_years),
        biasDirection: describeBiasDirection(approach.metrics.bias_percent),
      }))
    : [];

  const yearlyErrorRanks = buildBenchmarkRankMap(benchmarkSummaryRows, (row) => row.yearlyMaeKwh);
  const monthlyErrorRanks = buildBenchmarkRankMap(benchmarkSummaryRows, (row) => row.monthlyMaeKwh);
  const biasRanks = buildBenchmarkRankMap(benchmarkSummaryRows, (row) => row.absBiasPercent);

  const rankedBenchmarkSummaryRows: RankedBenchmarkSummaryRow[] = benchmarkSummaryRows.map((row) => {
    const yearlyErrorRank = yearlyErrorRanks.get(row.id) ?? benchmarkSummaryRows.length;
    const monthlyErrorRank = monthlyErrorRanks.get(row.id) ?? benchmarkSummaryRows.length;
    const biasRank = biasRanks.get(row.id) ?? benchmarkSummaryRows.length;

    return {
      ...row,
      yearlyErrorRank,
      monthlyErrorRank,
      biasRank,
      overallRankScore: yearlyErrorRank + monthlyErrorRank + biasRank,
    };
  });

  const recommendedBenchmark = rankedBenchmarkSummaryRows.reduce<RankedBenchmarkSummaryRow | null>((best, row) => {
    if (!best) {
      return row;
    }
    if (row.overallRankScore < best.overallRankScore) {
      return row;
    }
    if (row.overallRankScore === best.overallRankScore && row.yearlyMaeKwh < best.yearlyMaeKwh) {
      return row;
    }
    if (
      row.overallRankScore === best.overallRankScore &&
      row.yearlyMaeKwh === best.yearlyMaeKwh &&
      row.absBiasPercent < best.absBiasPercent
    ) {
      return row;
    }
    return best;
  }, null);
  const benchmarkWindowStart = benchmarkResult?.evaluation_years[0] ?? Math.max(2000, evaluationYear - benchmarkYears + 1);
  const benchmarkWindowEnd = benchmarkResult?.evaluation_years[benchmarkResult.evaluation_years.length - 1] ?? evaluationYear;
  const benchmarkWindowLabel = benchmarkWindowStart === benchmarkWindowEnd ? String(benchmarkWindowEnd) : `${benchmarkWindowStart}-${benchmarkWindowEnd}`;
  const benchmarkTrainingWindowLabel = `Using ${benchmarkResult?.training_window_years ?? trainingYears} past years for learning`;
  const accuracyMonthlyEnergyChartData = accuracyResult
    ? MONTH_NAMES.map((month, index) => ({
        name: month,
        Forecast: accuracyResult.predicted_monthly_kwh[index] ?? 0,
        Actual: accuracyResult.actual_monthly_kwh[index] ?? 0,
      }))
    : [];
  const accuracyMonthlyErrorChartData = accuracyResult
    ? MONTH_NAMES.map((month, index) => ({
        name: month,
        'Forecast error (kWh)': Number(
          ((accuracyResult.predicted_monthly_kwh[index] ?? 0) - (accuracyResult.actual_monthly_kwh[index] ?? 0)).toFixed(1),
        ),
      }))
    : [];
  const accuracyTakeaway = accuracyResult
    ? buildAccuracyTakeaway(accuracyResult.quality, accuracyResult.bias_percent)
    : null;
  const accuracyQualityDescription = accuracyResult ? getAccuracyQualityDescription(accuracyResult.quality) : '';
  const accuracyQualityClassName = accuracyResult ? getAccuracyQualityClassName(accuracyResult.quality) : 'text-foreground';
  const accuracyBiasDirection = accuracyResult ? describeBiasDirection(accuracyResult.bias_percent) : 'Bias is close to neutral';
  const selectedForecastApproachLabel = getForecastApproachLabel(modelType);
  const accuracyMethodLabel = accuracyResult
    ? getForecastApproachLabel(accuracyResult.model_type_used)
    : selectedForecastApproachLabel;
  const accuracyWeatherBasisLabel = accuracyResult
    ? formatWeatherReferenceLabel(accuracyResult.weather_reference_year)
    : 'Not available';
  const accuracyTrainingYearsLabel = accuracyResult
    ? formatLearningYearsUsed(accuracyResult.training_years_used)
    : 'Not available';
  const accuracyComparisonRows = accuracyResult
    ? [
        {
          metric: 'Yearly energy',
          actual: `${formatSidebarNumber(accuracyResult.actual_yearly_kwh)} kWh`,
          forecast: `${formatSidebarNumber(accuracyResult.predicted_yearly_kwh)} kWh`,
          difference: `${formatSignedNumber(accuracyResult.bias_kwh)} kWh (${formatSignedNumber(accuracyResult.bias_percent, 2)}%)`,
        },
        {
          metric: 'Annual savings',
          actual: `${formatSidebarNumber(accuracyResult.actual_annual_savings)} ${accuracyResult.financial_assumptions.currency}`,
          forecast: `${formatSidebarNumber(accuracyResult.predicted_annual_savings)} ${accuracyResult.financial_assumptions.currency}`,
          difference: `${formatSignedNumber(
            accuracyResult.predicted_annual_savings - accuracyResult.actual_annual_savings,
          )} ${accuracyResult.financial_assumptions.currency}`,
        },
        {
          metric: 'Simple payback',
          actual: formatPaybackYears(accuracyResult.actual_simple_payback_years),
          forecast: formatPaybackYears(accuracyResult.predicted_simple_payback_years),
          difference: formatPaybackDelta(
            accuracyResult.actual_simple_payback_years,
            accuracyResult.predicted_simple_payback_years,
          ),
        },
      ]
    : [];
  const currentBasePayload = buildPayload();
  const comparisonRequestedModelLabel = selectedForecastApproachLabel;
  const comparisonModelLabel = comparisonResult
    ? getForecastApproachLabel(comparisonResult.model_type_used)
    : comparisonRequestedModelLabel;
  const comparisonWeatherBasisLabel = comparisonResult
    ? formatWeatherReferenceLabel(comparisonResult.weather_reference_year)
    : forecastData
      ? formatWeatherReferenceLabel(forecastData.weather_reference_year)
      : 'Resolved when you run comparison';
  const comparisonSharedContextRows = [
    { label: 'Forecast year', value: String(currentBasePayload.year) },
    { label: 'Forecast approach', value: comparisonModelLabel },
    { label: 'Weather reference', value: comparisonWeatherBasisLabel },
    { label: 'Tariff', value: `${formatSidebarNumber(currentBasePayload.electricity_price_per_kwh, 2)} ${currency}/kWh` },
    {
      label: 'Base system reference',
      value:
        `${formatSidebarNumber(currentBasePayload.panel_area)} m² · ` +
        `${formatSidebarNumber(currentBasePayload.tilt)}° · ` +
        `${formatSidebarNumber(currentBasePayload.ac_capacity_kw)} kW · ` +
        `${formatCurrencyAmount(currentBasePayload.system_capex, currency, 0)}`,
    },
    {
      label: 'Inherited settings',
      value:
        `${formatSidebarNumber(currentBasePayload.panel_efficiency * 100, 0)}% efficiency · ` +
        `${cleanliness} cleanliness · ` +
        `${shading} shading · ` +
        `gamma ${formatSidebarNumber(currentBasePayload.gamma, 3)} · ` +
        `NOCT ${formatSidebarNumber(currentBasePayload.noct, 1)}°C`,
    },
  ];
  const configuredScenarioRows = scenarioRequests.map((scenario, index) => ({
    id: `${scenario.name}-${index}`,
    label: scenario.name,
    panelArea: scenario.payload.panel_area,
    panelAreaDelta: scenario.payload.panel_area - currentBasePayload.panel_area,
    tilt: scenario.payload.tilt,
    tiltDelta: scenario.payload.tilt - currentBasePayload.tilt,
    acCapacityKw: scenario.payload.ac_capacity_kw,
    acCapacityDelta: scenario.payload.ac_capacity_kw - currentBasePayload.ac_capacity_kw,
    capex: scenario.payload.system_capex,
    capexDelta: scenario.payload.system_capex - currentBasePayload.system_capex,
  }));
  const comparisonOptionRows: ScenarioOptionRow[] = comparisonResult
    ? comparisonResult.results.map((result, index) => ({
        id: `${result.scenario.name}-${index}`,
        label: result.scenario.name,
        isBaseline: index === 0,
        yearlyKwh: result.yearly_kwh,
        annualSavings: result.annual_savings,
        simplePaybackYears: result.simple_payback_years ?? null,
        paybackDeltaYears: result.payback_delta_years ?? null,
        capex: result.scenario.system_capex,
        currency: result.financial_assumptions.currency,
        energyDeltaPercent: result.deviation_percent,
        energyDeltaKwh: result.yearly_kwh - comparisonResult.baseline_yearly_kwh,
        savingsDeltaPercent: result.value_deviation_percent,
        savingsDeltaValue: result.annual_savings - comparisonResult.baseline_annual_savings,
      }))
    : [];
  const recommendedScenarioSelection = selectScenarioRecommendation(comparisonOptionRows);
  const recommendedScenario = recommendedScenarioSelection.row;
  const recommendedScenarioIndex = recommendedScenario
    ? comparisonOptionRows.findIndex((row) => row.id === recommendedScenario.id)
    : -1;
  const comparisonRecommendationTitle =
    recommendedScenarioSelection.mode === 'payback' ? 'Recommended Option' : 'Best Savings Option';
  const bestPaybackScenario = comparisonOptionRows
    .filter((row) => row.simplePaybackYears != null && Number.isFinite(row.simplePaybackYears))
    .reduce<ScenarioOptionRow | null>((best, current) => {
      if (!best) {
        return current;
      }
      return (current.simplePaybackYears ?? Infinity) < (best.simplePaybackYears ?? Infinity) ? current : best;
    }, null);
  const highestSavingsScenario = comparisonOptionRows.reduce<ScenarioOptionRow | null>((best, current) => {
    if (!best) {
      return current;
    }
    return current.annualSavings > best.annualSavings ? current : best;
  }, null);
  const mostEnergyScenario = comparisonOptionRows.reduce<ScenarioOptionRow | null>((best, current) => {
    if (!best) {
      return current;
    }
    return current.yearlyKwh > best.yearlyKwh ? current : best;
  }, null);
  const comparisonRecommendationSummary = recommendedScenario
    ? recommendedScenarioSelection.mode === 'payback'
      ? recommendedScenario.isBaseline
        ? 'Base System still offers the shortest simple payback under the shared forecast assumptions.'
        : `${recommendedScenario.label} offers the shortest simple payback under the shared forecast assumptions.`
      : recommendedScenario.isBaseline
        ? 'No option has a viable simple payback, and Base System still produces the highest annual savings.'
        : `No option has a viable simple payback, so the recommendation falls back to the highest annual savings.`
    : 'Run the option comparison to generate a recommendation.';
  const comparisonRecommendationDetail = recommendedScenario
    ? recommendedScenario.isBaseline
      ? `Base System remains the reference option with ${formatSidebarNumber(recommendedScenario.yearlyKwh)} kWh/year, ${formatCurrencyAmount(
          recommendedScenario.annualSavings,
          recommendedScenario.currency,
        )} in annual savings, and ${formatPaybackYears(recommendedScenario.simplePaybackYears)} simple payback.`
      : `${recommendedScenario.label} changes yearly energy by ${formatSignedNumber(
          recommendedScenario.energyDeltaKwh,
        )} kWh, annual savings by ${formatSignedCurrency(
          recommendedScenario.savingsDeltaValue,
          recommendedScenario.currency,
        )}, and ${
          recommendedScenario.paybackDeltaYears == null
            ? 'does not deliver a comparable simple payback under the current CAPEX/tariff assumptions'
            : `shifts payback by ${formatSignedNumber(recommendedScenario.paybackDeltaYears, 1)} years`
        } versus Base System.`
    : 'Add at least one alternative option to compare against Base System.';
  const comparisonTechnicalRows = comparisonResult
    ? [
        {
          field: 'Requested forecast approach',
          value: getForecastApproachLabel(comparisonResult.model_type_requested),
        },
        {
          field: 'Forecast approach used',
          value: getForecastApproachLabel(comparisonResult.model_type_used),
        },
        {
          field: 'Weather reference used',
          value: formatWeatherReferenceLabel(comparisonResult.weather_reference_year),
        },
        {
          field: 'Past years used for learning',
          value: formatLearningYearsUsed(comparisonResult.training_years_used),
        },
        {
          field: 'Backup forecast note',
          value: comparisonResult.fallback_reason || 'No backup forecast method used',
        },
        { field: 'Data source', value: comparisonResult.data_source },
      ]
    : [];
  const locationSummary = position
    ? detectedAddress || `${position.lat.toFixed(4)}, ${position.lng.toFixed(4)}`
    : 'Choose a city, search an address, or click the map.';
  const systemSummary =
    `${formatSidebarNumber(panelArea)} m² · ` +
    `${formatSidebarNumber(acCapacityKw)} kW · ` +
    `${getForecastApproachShortLabel(modelType)}`;
  const financialSummary = `${formatSidebarNumber(electricityPrice, 2)} ${currency}/kWh · CAPEX ${formatSidebarNumber(systemCapex)} ${currency}`;
  const overviewSummaryText = forecastData
    ? `For ${forecastData.forecast_year}, this site is expected to generate about ${formatReadableKwh(
        forecastData.yearly_kwh,
      )}/year, save about ${formatReadableCurrency(
        forecastData.annual_savings,
        forecastData.financial_assumptions.currency,
      )} per year, and ${
        forecastData.simple_payback_years == null
          ? 'not currently reach a viable simple payback'
          : `reach simple payback in about ${formatReadableNumber(forecastData.simple_payback_years, 1)} years`
      } using the ${getForecastApproachLabel(forecastData.model_type_used)}.`
    : '';
  const overviewContextRows = forecastData
    ? [
        { label: 'Forecast year', value: String(forecastData.forecast_year) },
        { label: 'Forecast approach used', value: getForecastApproachLabel(forecastData.model_type_used) },
        { label: 'Weather reference', value: formatWeatherReferenceLabel(forecastData.weather_reference_year) },
        {
          label: 'Tariff assumption',
          value: `${formatReadableNumber(forecastData.financial_assumptions.electricity_price_per_kwh, 2)} ${forecastData.financial_assumptions.currency}/kWh`,
        },
        {
          label: 'System CAPEX',
          value: formatReadableCurrency(forecastData.financial_assumptions.system_capex, forecastData.financial_assumptions.currency),
        },
        ...(forecastData.training_years_used.length > 0
          ? [
              {
                label: 'Past years used for learning',
                value: formatLearningYearsUsed(forecastData.training_years_used),
              },
            ]
          : []),
      ]
    : [];
  const overviewMonthlyEnergyChartData = forecastData
    ? MONTH_NAMES.map((month, index) => ({
        name: month,
        value: forecastData.monthly_kwh[index] ?? 0,
      }))
    : [];
  const overviewMonthlyValueChartData = forecastData
    ? MONTH_NAMES.map((month, index) => ({
        name: month,
        value: forecastData.monthly_estimated_value[index] ?? 0,
      }))
    : [];
  const overviewSeasonalProductionData = forecastData
    ? [
        { name: 'Jan-Mar', monthIndexes: [0, 1, 2] },
        { name: 'Apr-Jun', monthIndexes: [3, 4, 5] },
        { name: 'Jul-Sep', monthIndexes: [6, 7, 8] },
        { name: 'Oct-Dec', monthIndexes: [9, 10, 11] },
      ].map((quarter) => {
        const kwh = quarter.monthIndexes.reduce((sum, monthIndex) => sum + (forecastData.monthly_kwh[monthIndex] ?? 0), 0);
        const sharePercent = forecastData.yearly_kwh > 0 ? (kwh / forecastData.yearly_kwh) * 100 : 0;

        return {
          name: quarter.name,
          kwh,
          sharePercent,
        };
      })
    : [];
  const overviewTechnicalRows = forecastData
    ? [
        { field: 'Requested forecast approach', value: getForecastApproachLabel(forecastData.model_type_requested) },
        { field: 'Forecast approach used', value: getForecastApproachLabel(forecastData.model_type_used) },
        { field: 'Weather reference', value: formatWeatherReferenceLabel(forecastData.weather_reference_year) },
        { field: 'Data source', value: forecastData.data_source },
        { field: 'Valuation basis', value: forecastData.financial_assumptions.valuation_basis },
        { field: 'Annual savings basis', value: forecastData.financial_assumptions.annual_savings_basis },
        { field: 'Payback basis', value: forecastData.financial_assumptions.payback_basis },
        ...(forecastData.training_years_used.length > 0
          ? [
              {
                field: 'Past years used for learning',
                value: formatLearningYearsUsed(forecastData.training_years_used),
              },
            ]
          : []),
      ]
    : [];
  const dailySimulationDateLabel = dailySimulation
    ? formatSimulationDateLabel(dailySimulation.hourly_time[0] ?? '')
    : 'Not available';
  const dailyPeakPower = dailySimulation && dailySimulation.hourly_ac_kw.length > 0 ? Math.max(...dailySimulation.hourly_ac_kw) : null;
  const dailyPeakIndex =
    dailySimulation && dailyPeakPower != null
      ? dailySimulation.hourly_ac_kw.findIndex((power) => power === dailyPeakPower)
      : -1;
  const dailyPeakHourLabel =
    dailySimulation && dailyPeakIndex >= 0
      ? formatHourlyLabel(dailySimulation.hourly_time[dailyPeakIndex], dailyPeakIndex)
      : 'Not available';
  const dailyLossPercent = dailySimulation ? Math.max(0, (1 - dailySimulation.system_loss_factor) * 100) : null;
  const dailySummaryText = dailySimulation
    ? `For ${dailySimulationDateLabel}, this site is expected to generate about ${formatReadableKwh(
        dailySimulation.daily_kwh,
        1,
      )}, be worth about ${formatReadableCurrency(
        dailySimulation.estimated_daily_value,
        dailySimulation.financial_assumptions.currency,
        2,
      )}, and peak around ${dailyPeakHourLabel} at roughly ${formatReadableNumber(dailyPeakPower, 2)} kW.`
    : '';
  const dailyHourlyChartData = dailySimulation
    ? dailySimulation.hourly_ac_kw.map((power, index) => ({
        time: formatHourlyLabel(dailySimulation.hourly_time[index], index),
        power,
      }))
    : [];
  const dailyContextRows = dailySimulation
    ? [
        { label: 'Simulated day', value: dailySimulationDateLabel },
        { label: 'Timezone', value: dailySimulation.timezone },
        { label: 'Data source', value: dailySimulation.data_source },
        {
          label: 'Tariff assumption',
          value: `${formatReadableNumber(
            dailySimulation.financial_assumptions.electricity_price_per_kwh,
            2,
          )} ${dailySimulation.financial_assumptions.currency}/kWh`,
        },
        { label: 'Valuation basis', value: dailySimulation.financial_assumptions.valuation_basis },
      ]
    : [];
  const dailyTechnicalRows = dailySimulation
    ? [
        { field: 'Simulated day', value: dailySimulationDateLabel },
        { field: 'Raw system loss factor', value: formatReadableNumber(dailySimulation.system_loss_factor, 3) },
        {
          field: 'Location coordinates',
          value: `${formatReadableNumber(dailySimulation.location[0], 4)}, ${formatReadableNumber(dailySimulation.location[1], 4)}`,
        },
        { field: 'Timezone', value: dailySimulation.timezone },
        { field: 'Data source', value: dailySimulation.data_source },
        { field: 'Valuation basis', value: dailySimulation.financial_assumptions.valuation_basis },
      ]
    : [];
  const sidebarStyle = {
    '--sidebar-width': `${sidebarCollapsed ? COLLAPSED_SIDEBAR_WIDTH : sidebarWidth}px`,
  } as CSSProperties;

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b bg-card">
        <div className="flex w-full items-start justify-between gap-6 px-6 py-6 md:px-8 md:py-8">
          <div className="min-w-0 flex-1">
            <h1 className="flex items-center gap-3 text-3xl font-black tracking-tight sm:text-4xl lg:text-5xl xl:text-6xl">
              <Sun className="h-8 w-8 shrink-0 text-yellow-500 sm:h-10 sm:w-10 lg:h-12 lg:w-12" />
              <span>Solar Energy Prediction System</span>
            </h1>
            <p className="mt-3 max-w-4xl text-sm text-muted-foreground sm:text-base">
              Configure the site, tune system and financial assumptions, then compare production and payback outcomes.
            </p>
          </div>
          <Button variant="outline" size="icon" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          </Button>
        </div>
      </header>

      <div className="flex flex-1 flex-col md:flex-row">
        <div
          className="relative w-full shrink-0 border-b bg-card md:w-[var(--sidebar-width)] md:border-b-0 md:border-r"
          style={sidebarStyle}
        >
          {sidebarCollapsed ? (
            <div className="flex items-center justify-between gap-3 p-3 md:h-full md:flex-col md:justify-start md:p-2">
              <Button
                variant="outline"
                size="icon"
                className="shrink-0"
                onClick={() => setSidebarCollapsed(false)}
                aria-label="Expand sidebar"
                title="Expand sidebar"
              >
                <PanelLeftOpen className="h-4 w-4" />
              </Button>
              <div className="min-w-0 md:pt-2 md:[writing-mode:vertical-rl]">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Controls</p>
              </div>
            </div>
          ) : (
            <div className="flex h-full min-h-0 w-full flex-col gap-4 overflow-y-auto p-4">
              <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-background/70 px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold">Collapse sidebar</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarCollapsed(true)}
                  aria-label="Minimize sidebar"
                  title="Minimize sidebar"
                >
                  <PanelLeftClose className="h-4 w-4" />
                </Button>
              </div>
              <Accordion type="multiple" defaultValue={['location', 'system', 'financial']} className="gap-3">
                <AccordionItem value="location" className="rounded-2xl border border-border/70 bg-background/70 px-3 shadow-sm">
                  <AccordionTrigger className="py-3 hover:no-underline">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 rounded-xl bg-sky-100 p-2 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300">
                        <MapPin className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold">Location</p>
                        <p className="mt-1 truncate text-xs text-muted-foreground">{locationSummary}</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pb-3">
                    <div className="space-y-2">
                      <Label>Quick Cities</Label>
                      <Select
                        value={selectedLocationId}
                        onValueChange={(value) => {
                          setSelectedLocationId(value);
                          if (value !== 'custom') {
                            const selected = PREDEFINED_LOCATIONS.find((location) => location.id === value);
                            if (selected) {
                              setPosition({ lat: selected.lat, lng: selected.lng });
                              setDetectedAddress(selected.label);
                              clearShapes();
                            }
                          }
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a preset city" />
                        </SelectTrigger>
                        <SelectContent>
                          {PREDEFINED_LOCATIONS.map((location) => (
                            <SelectItem key={location.id} value={location.id}>
                              {location.label}
                            </SelectItem>
                          ))}
                          <SelectItem value="custom">Custom Location (Map)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="rounded-xl border border-dashed border-border/70 bg-muted/25 p-3">
                      <Label>Search Exact Address</Label>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Enter street, house number, city, and country for a more accurate result.
                      </p>
                      <div className="mt-3 flex gap-2">
                        <Input
                          placeholder="e.g. 1600 Amphitheatre Parkway, Mountain View, CA"
                          value={searchQuery}
                          onChange={(event) => setSearchQuery(event.target.value)}
                          onKeyDown={(event) => event.key === 'Enter' && handleSearchLocation()}
                        />
                        <Button variant="secondary" onClick={handleSearchLocation} disabled={isSearching}>
                          {isSearching ? '...' : 'Find'}
                        </Button>
                      </div>
                    </div>

                    <div>
                      <Label className="text-muted-foreground">Detected Address</Label>
                      {detectedAddress ? (
                        <Alert className="mt-2 border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/20">
                          <AlertDescription className="text-sm">{detectedAddress}</AlertDescription>
                        </Alert>
                      ) : (
                        <p className="mt-2 text-sm text-muted-foreground">No address selected yet.</p>
                      )}
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="system" className="rounded-2xl border border-border/70 bg-background/70 px-3 shadow-sm">
                  <AccordionTrigger className="py-3 hover:no-underline">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 rounded-xl bg-amber-100 p-2 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
                        <Settings className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold">System Parameters</p>
                        <p className="mt-1 truncate text-xs text-muted-foreground">{systemSummary}</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pb-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>Forecast Year</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">
                            The year for which you want to predict solar energy production.
                          </PopoverContent>
                        </Popover>
                      </div>
                      <Input type="number" value={forecastYear} onChange={(event) => setForecastYear(event.target.value)} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>Panel Area (m²)</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">
                            The total surface area of the solar panels. You can draw a shape on the map to estimate this automatically.
                          </PopoverContent>
                        </Popover>
                      </div>
                      <Input type="number" value={panelArea} onChange={(event) => setPanelArea(event.target.value)} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>Inverter AC Capacity (kW)</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">
                            The maximum AC power output of the inverter. This caps the maximum power the system can deliver to the grid.
                          </PopoverContent>
                        </Popover>
                      </div>
                      <Input type="number" value={acCapacityKw} onChange={(event) => setAcCapacityKw(event.target.value)} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>Forecast Approach</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">
                            <p className="mb-2">
                              <strong>Physics-based forecast:</strong> Uses panel setup, tilt, and weather assumptions to estimate output.
                            </p>
                            <p>
                              <strong>History-based forecast:</strong> Learns patterns from past years to estimate future output using machine learning behind the scenes.
                            </p>
                          </PopoverContent>
                        </Popover>
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        {(['physical', 'ml'] as const).map((approach) => {
                          const isSelected = modelType === approach;

                          return (
                            <button
                              key={approach}
                              type="button"
                              aria-pressed={isSelected}
                              onClick={() => setModelType(approach)}
                              className={
                                `rounded-xl border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 ` +
                                (isSelected
                                  ? 'border-primary bg-primary/5 text-foreground shadow-sm'
                                  : 'border-border/70 bg-background hover:border-primary/40 hover:bg-muted/30')
                              }
                            >
                              <div className="space-y-2">
                                <div className="flex items-start justify-between gap-2">
                                  <span className="font-medium">{getForecastApproachLabel(approach)}</span>
                                  {isSelected ? <Badge variant="secondary">Selected</Badge> : null}
                                </div>
                                <p className="text-sm text-muted-foreground">{getForecastApproachDescription(approach)}</p>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {modelType === 'ml' ? (
                      <div className="space-y-2 rounded-xl border border-dashed border-border/70 bg-muted/20 p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <Label>Past Years Used For Learning</Label>
                            <p className="mt-1 text-xs text-muted-foreground">
                              More years gives a steadier forecast. Fewer years reacts more to recent patterns.
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">3 years is a good starting point for most sites.</p>
                          </div>
                          <span className="text-sm text-muted-foreground">{trainingYears}</span>
                        </div>
                        <Slider
                          min={1}
                          max={10}
                          step={1}
                          value={getSliderValue(trainingYears, 3)}
                          onValueChange={handleTrainingYearsChange}
                        />
                      </div>
                    ) : null}

                    <Accordion type="single" collapsible className="rounded-xl border border-border/70 bg-muted/15 px-3">
                      <AccordionItem value="advanced-system" className="border-none">
                        <AccordionTrigger className="py-3 hover:no-underline">
                          <div className="min-w-0">
                            <p className="text-sm font-medium">Advanced System Tuning</p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              Expand efficiency, tilt, cleanliness, shading, and thermal parameters.
                            </p>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="space-y-4 pb-3">
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <div className="flex items-center gap-2">
                                <Label>Panel Efficiency</Label>
                                <Popover>
                                  <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                                    <Info className="h-3 w-3 text-muted-foreground" />
                                  </PopoverTrigger>
                                  <PopoverContent className="w-80 text-sm">
                                    The percentage of sunlight the panels can convert into usable electricity.
                                  </PopoverContent>
                                </Popover>
                              </div>
                              <span className="text-sm text-muted-foreground">{panelEfficiency.toFixed(2)}</span>
                            </div>
                            <Slider min={0.1} max={0.3} step={0.01} value={getSliderValue(panelEfficiency, 0.2)} onValueChange={handlePanelEfficiencyChange} />
                          </div>

                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <div className="flex items-center gap-2">
                                <Label>Tilt Angle (°)</Label>
                                <Popover>
                                  <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                                    <Info className="h-3 w-3 text-muted-foreground" />
                                  </PopoverTrigger>
                                  <PopoverContent className="w-80 text-sm">
                                    The angle of the solar panels relative to the horizontal ground.
                                  </PopoverContent>
                                </Popover>
                              </div>
                              <span className="text-sm text-muted-foreground">{tilt}</span>
                            </div>
                            <Slider min={0} max={60} step={1} value={getSliderValue(tilt, 30)} onValueChange={handleTiltChange} />
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Label>Panel Cleanliness</Label>
                              <Popover>
                                <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                                  <Info className="h-3 w-3 text-muted-foreground" />
                                </PopoverTrigger>
                                <PopoverContent className="w-80 text-sm">
                                  Accounts for energy loss due to dust, dirt, or snow on the panels.
                                </PopoverContent>
                              </Popover>
                            </div>
                            <Select value={cleanliness} onValueChange={(value) => setCleanliness(value as CleanlinessLevel)}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="clean">clean</SelectItem>
                                <SelectItem value="normal">normal</SelectItem>
                                <SelectItem value="dusty">dusty</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Label>Shading Level</Label>
                              <Popover>
                                <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                                  <Info className="h-3 w-3 text-muted-foreground" />
                                </PopoverTrigger>
                                <PopoverContent className="w-80 text-sm">
                                  Accounts for energy loss due to shadows from nearby buildings or trees.
                                </PopoverContent>
                              </Popover>
                            </div>
                            <Select value={shading} onValueChange={(value) => setShading(value as ShadingLevel)}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="none">none</SelectItem>
                                <SelectItem value="low">low</SelectItem>
                                <SelectItem value="medium">medium</SelectItem>
                                <SelectItem value="high">high</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Label>Temperature Coefficient (gamma)</Label>
                              <Popover>
                                <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                                  <Info className="h-3 w-3 text-muted-foreground" />
                                </PopoverTrigger>
                                <PopoverContent className="w-80 text-sm">
                                  The rate at which panel efficiency drops as temperature rises above standard conditions.
                                </PopoverContent>
                              </Popover>
                            </div>
                            <Input type="number" step="0.0001" value={gamma} onChange={(event) => setGamma(event.target.value)} />
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Label>NOCT (°C)</Label>
                              <Popover>
                                <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                                  <Info className="h-3 w-3 text-muted-foreground" />
                                </PopoverTrigger>
                                <PopoverContent className="w-80 text-sm">
                                  Nominal Operating Cell Temperature. The temperature the cells reach under standard conditions.
                                </PopoverContent>
                              </Popover>
                            </div>
                            <Input type="number" step="1" value={noct} onChange={(event) => setNoct(event.target.value)} />
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="financial" className="rounded-2xl border border-border/70 bg-background/70 px-3 shadow-sm">
                  <AccordionTrigger className="py-3 hover:no-underline">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 rounded-xl bg-emerald-100 p-2 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                        <DollarSign className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold">Financial Parameters</p>
                        <p className="mt-1 truncate text-xs text-muted-foreground">{financialSummary}</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pb-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>Electricity Price / Feed-in Tariff</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">
                            The price per kWh of electricity. This is used to estimate yearly value and annual savings.
                          </PopoverContent>
                        </Popover>
                      </div>
                      <Input
                        type="number"
                        step="0.01"
                        value={electricityPrice}
                        onChange={(event) => setElectricityPrice(event.target.value)}
                      />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>Currency</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">The currency used for financial estimations.</PopoverContent>
                        </Popover>
                      </div>
                      <Select value={currency} onValueChange={(value) => setCurrency(value as CurrencyCode)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ILS">ILS</SelectItem>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="EUR">EUR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>System CAPEX</Label>
                        <Popover>
                          <PopoverTrigger className="inline-flex h-4 w-4 items-center justify-center rounded-full p-0 hover:bg-accent hover:text-accent-foreground">
                            <Info className="h-3 w-3 text-muted-foreground" />
                          </PopoverTrigger>
                          <PopoverContent className="w-80 text-sm">
                            Used by the backend to estimate annual savings and simple payback.
                          </PopoverContent>
                        </Popover>
                      </div>
                      <Input type="number" step="100" value={systemCapex} onChange={(event) => setSystemCapex(event.target.value)} />
                    </div>

                    <div className="rounded-xl border border-dashed border-border/70 bg-muted/20 p-3">
                      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Summary</p>
                      <p className="mt-2 text-sm text-foreground">
                        {formatSidebarNumber(electricityPrice, 2)} {currency}/kWh valuation with a CAPEX assumption of{' '}
                        {formatSidebarNumber(systemCapex)} {currency}.
                      </p>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              <Button className="w-full" size="lg" onClick={handleRunForecast} disabled={!position || isLoading}>
                {isLoading ? 'Running...' : 'Run Solar Production Forecast'}
              </Button>
            </div>
          )}

          {!sidebarCollapsed && (
            <button
              type="button"
              onMouseDown={handleSidebarResizeStart}
              className={`absolute inset-y-0 right-0 z-20 hidden w-4 -translate-x-1/2 cursor-col-resize items-center justify-center md:flex ${
                isSidebarResizing ? 'bg-primary/10' : 'bg-transparent'
              }`}
              aria-label="Resize sidebar"
              title="Resize sidebar"
            >
              <span className="flex h-20 w-2 items-center justify-center rounded-full border border-border/70 bg-background/90 shadow-sm">
                <GripVertical className="h-4 w-4 text-muted-foreground" />
              </span>
            </button>
          )}
        </div>

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 md:p-8">
            {apiError && (
            <Alert variant="destructive" className="mb-6">
              <AlertTitle>Backend request issue</AlertTitle>
              <AlertDescription>{apiError}</AlertDescription>
            </Alert>
          )}

          {!position ? (
            <Alert className="mb-6">
              <AlertTitle>Location Required</AlertTitle>
              <AlertDescription>Enter an address in the sidebar to show the map and enable forecasting.</AlertDescription>
            </Alert>
          ) : (
            <div className="relative z-0 mb-6 h-[360px] overflow-hidden rounded-xl border">
              <MapContainer center={[position.lat, position.lng]} zoom={18} style={{ height: '100%', width: '100%' }}>
                <MapViewportSync position={position} />
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <FeatureGroup ref={featureGroupRef}>
                  <EditControl
                    position="topright"
                    onCreated={handleCreated}
                    onDrawStart={() => {
                      isDrawingRef.current = true;
                    }}
                    onDrawStop={() => {
                      setTimeout(() => {
                        isDrawingRef.current = false;
                      }, 100);
                    }}
                    draw={{
                      rectangle: true,
                      polygon: true,
                      circle: false,
                      circlemarker: false,
                      marker: false,
                      polyline: false,
                    }}
                  />
                </FeatureGroup>
                <LocationMarker
                  position={position}
                  setPosition={setPosition}
                  setAddress={setDetectedAddress}
                  clearShapes={clearShapes}
                  isDrawingRef={isDrawingRef}
                  setSelectedLocationId={setSelectedLocationId}
                />
              </MapContainer>
            </div>
          )}

          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="mb-4 flex h-auto flex-wrap">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="daily">Daily Simulation</TabsTrigger>
              <TabsTrigger value="accuracy">Accuracy Check</TabsTrigger>
              <TabsTrigger value="benchmark">Forecast Comparison</TabsTrigger>
              <TabsTrigger value="scenarios">System Options</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {!forecastData ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  Run the forecast to see expected yearly energy, savings, and payback for this site.
                </div>
              ) : (
                <>
                  {forecastData.fallback_reason && (
                    <Alert>
                      <AlertTitle>Backup forecast approach used</AlertTitle>
                      <AlertDescription>{forecastData.fallback_reason}</AlertDescription>
                    </Alert>
                  )}

                  <Card className="border-primary/25 bg-primary/5">
                    <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <CardTitle>Forecast Summary</CardTitle>
                        <CardDescription>Decision-first overview of yearly output and financial return.</CardDescription>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="secondary">Year {forecastData.forecast_year}</Badge>
                          <Badge variant="outline">{getForecastApproachLabel(forecastData.model_type_used)}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg leading-7 text-foreground">{overviewSummaryText}</p>
                    </CardContent>
                  </Card>

                  <div className="space-y-3">
                    <div>
                      <h3 className="text-lg font-semibold">Primary Outcomes</h3>
                      <p className="text-sm text-muted-foreground">The main numbers most users care about first.</p>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-muted-foreground">Yearly Energy</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatReadableKwh(forecastData.yearly_kwh)}</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-muted-foreground">Estimated Annual Savings</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">
                            {formatReadableCurrency(forecastData.annual_savings, forecastData.financial_assumptions.currency)}
                          </div>
                          <p className="mt-2 text-xs text-muted-foreground">{forecastData.financial_assumptions.annual_savings_basis}</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-muted-foreground">Simple Payback</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatPaybackYears(forecastData.simple_payback_years)}</div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
                    <Card>
                      <CardHeader>
                        <CardTitle>Forecast Context</CardTitle>
                        <CardDescription>These assumptions shape the yearly forecast shown above.</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableBody>
                            {overviewContextRows.map((row) => (
                              <TableRow key={row.label}>
                                <TableCell className="font-medium">{row.label}</TableCell>
                                <TableCell>{row.value}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Performance Details</CardTitle>
                        <CardDescription>Helpful supporting metrics for quick energy benchmarking.</CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-3">
                        <div className="rounded-lg border bg-background/70 p-3">
                          <p className="text-xs uppercase tracking-wide text-muted-foreground">Specific Yield</p>
                          <p className="mt-1 text-lg font-semibold">{formatReadableNumber(forecastData.specific_yield_kwh_per_kwp, 1)} kWh/kWp</p>
                        </div>
                        <div className="rounded-lg border bg-background/70 p-3">
                          <p className="text-xs uppercase tracking-wide text-muted-foreground">Average Daily Energy</p>
                          <p className="mt-1 text-lg font-semibold">{formatReadableKwh(forecastData.avg_daily_kwh, 1)}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle>Monthly Energy Forecast</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={overviewMonthlyEnergyChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip formatter={(value) => [formatReadableKwh(Number(value)), 'Energy']} />
                            <Bar dataKey="value" fill="#eab308" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Estimated Monthly Electricity Value</CardTitle>
                        <CardDescription>
                          Estimated money by month based on the current tariff and valuation assumptions.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={overviewMonthlyValueChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip
                              formatter={(value) => [
                                formatReadableCurrency(Number(value), forecastData.financial_assumptions.currency),
                                'Estimated value',
                              ]}
                            />
                            <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Seasonal Production Split</CardTitle>
                      <CardDescription>This view shows where annual output is concentrated across the year.</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={overviewSeasonalProductionData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip
                            content={({ active, payload, label }) => {
                              if (!active || !payload?.length) {
                                return null;
                              }

                              const row = payload[0]?.payload as { kwh: number; sharePercent: number };

                              return (
                                <div className="rounded-md border bg-background px-3 py-2 text-sm shadow-sm">
                                  <p className="font-medium">{label}</p>
                                  <p>{formatReadableKwh(row.kwh)}</p>
                                  <p className="text-muted-foreground">{formatReadableNumber(row.sharePercent, 1)}% of yearly production</p>
                                </div>
                              );
                            }}
                          />
                          <Bar dataKey="kwh" fill="#0f766e" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                    <AccordionItem value="overview-details" className="border-none">
                      <AccordionTrigger className="py-4 text-left hover:no-underline">
                        <div>
                          <p className="font-semibold">Technical Details</p>
                          <p className="text-sm font-normal text-muted-foreground">
                            Open this section for method details, data source, and financial assumptions.
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Field</TableHead>
                              <TableHead>Value</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {overviewTechnicalRows.map((row) => (
                              <TableRow key={row.field}>
                                <TableCell>{row.field}</TableCell>
                                <TableCell>{row.value}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </>
              )}
            </TabsContent>

            <TabsContent value="daily" className="space-y-6">
              {!dailySimulation ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  Run the forecast to see the next day's hourly solar output and estimated daily value.
                </div>
              ) : (
                <>
                  <Card className="border-primary/25 bg-primary/5">
                    <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <CardTitle>One-Day Forecast Summary</CardTitle>
                        <CardDescription>Decision-first view of the next forecasted day for this site.</CardDescription>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="secondary">{dailySimulationDateLabel}</Badge>
                          <Badge variant="outline">{dailySimulation.timezone}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg leading-7 text-foreground">{dailySummaryText}</p>
                    </CardContent>
                  </Card>

                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Daily Energy</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatReadableKwh(dailySimulation.daily_kwh, 1)}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Estimated Daily Value</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {formatReadableCurrency(
                            dailySimulation.estimated_daily_value,
                            dailySimulation.financial_assumptions.currency,
                            2,
                          )}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Peak Power</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatReadableNumber(dailyPeakPower, 2)} kW</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Peak Hour</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{dailyPeakHourLabel}</div>
                        <p className="mt-2 text-xs text-muted-foreground">Shown in local site time.</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Estimated System Losses</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatReadableNumber(dailyLossPercent, 1)}%</div>
                        <p className="mt-2 text-xs text-muted-foreground">
                          Includes shading, cleanliness, wiring, and inverter effects.
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Daily Forecast Context</CardTitle>
                      <CardDescription>Supporting details for how the one-day forecast is interpreted.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableBody>
                          {dailyContextRows.map((row) => (
                            <TableRow key={row.label}>
                              <TableCell className="font-medium">{row.label}</TableCell>
                              <TableCell>{row.value}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Hourly Power Forecast</CardTitle>
                      <CardDescription>Local-time AC output for the simulated day.</CardDescription>
                    </CardHeader>
                    <CardContent className="h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={dailyHourlyChartData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="time" />
                          <YAxis />
                          <Tooltip formatter={(value) => [`${formatReadableNumber(Number(value), 2)} kW`, 'AC Power']} />
                          {dailyPeakHourLabel !== 'Not available' ? (
                            <ReferenceLine
                              x={dailyPeakHourLabel}
                              stroke="#f59e0b"
                              strokeDasharray="4 4"
                              label={{ value: 'Peak hour', position: 'top', fill: '#a16207', fontSize: 12 }}
                            />
                          ) : null}
                          <Line type="monotone" dataKey="power" stroke="#10b981" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                    <AccordionItem value="daily-details" className="border-none">
                      <AccordionTrigger className="py-4 text-left hover:no-underline">
                        <div>
                          <p className="font-semibold">Technical Details</p>
                          <p className="text-sm font-normal text-muted-foreground">
                            Open this section for raw loss, source, and forecast context fields.
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Field</TableHead>
                              <TableHead>Value</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {dailyTechnicalRows.map((row) => (
                              <TableRow key={row.field}>
                                <TableCell>{row.field}</TableCell>
                                <TableCell>{row.value}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </>
              )}
            </TabsContent>

            <TabsContent value="accuracy" className="space-y-6">
              <div className="flex flex-col gap-4 rounded-lg border bg-muted/30 p-4 md:flex-row md:items-end md:justify-between">
                <div className="space-y-2">
                  <div>
                    <h3 className="font-medium">Past-Year Accuracy Check</h3>
                    <p className="text-sm text-muted-foreground">
                      Test the selected forecast approach on a completed year we already know.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">Year {evaluationYear}</Badge>
                    <Badge variant="outline">{selectedForecastApproachLabel}</Badge>
                  </div>
                </div>
                <Button onClick={handleRunAccuracy} disabled={!position || isLoading}>
                  {isLoading ? 'Running...' : 'Run Accuracy Check'}
                </Button>
              </div>

              {selectedForecastYear > lastCompleteYear && (
                <Alert>
                  <AlertTitle>Using last complete archive year</AlertTitle>
                  <AlertDescription>
                    You selected {selectedForecastYear}, but archived actual weather is currently complete only through {lastCompleteYear},
                    so this check runs against {evaluationYear}.
                  </AlertDescription>
                </Alert>
              )}

              {!accuracyResult ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  Run the accuracy check to compare the forecast against archived actual weather for the selected site.
                </div>
              ) : (
                <>
                  {accuracyResult.fallback_reason && (
                    <Alert>
                      <AlertTitle>Backup method used</AlertTitle>
                      <AlertDescription>{accuracyResult.fallback_reason}</AlertDescription>
                    </Alert>
                  )}

                  <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
                    <Card className="border-primary/25 bg-primary/5">
                      <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-2">
                          <CardTitle>Overall Takeaway</CardTitle>
                          <CardDescription>
                            Accuracy check for {accuracyResult.year} using {accuracyMethodLabel}.
                          </CardDescription>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary">Checked year {accuracyResult.year}</Badge>
                            <Badge variant="outline">{accuracyMethodLabel}</Badge>
                          </div>
                        </div>
                        <div className="space-y-1 md:text-right">
                          <p className="text-xs uppercase tracking-wide text-muted-foreground">Accuracy rating</p>
                          <p className={`text-2xl font-semibold ${accuracyQualityClassName}`}>{accuracyResult.quality}</p>
                          <p className="text-xs text-muted-foreground">{accuracyQualityDescription}</p>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <p className="text-3xl font-semibold tracking-tight">{accuracyTakeaway?.headline}</p>
                          <p className="mt-2 text-sm text-muted-foreground">{accuracyTakeaway?.description}</p>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-3">
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Avg monthly miss</p>
                            <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(accuracyResult.monthly_mae_kwh)} kWh</p>
                            <p className="text-xs text-muted-foreground">{formatSidebarNumber(accuracyResult.mape_percent, 2)}% monthly error</p>
                          </div>
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Yearly miss</p>
                            <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(accuracyResult.yearly_mae_kwh)} kWh</p>
                            <p className="text-xs text-muted-foreground">{formatSidebarNumber(accuracyResult.yearly_mape_percent, 2)}% yearly error</p>
                          </div>
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Bias</p>
                            <p className="mt-1 text-lg font-semibold">{formatSignedNumber(accuracyResult.bias_kwh)} kWh</p>
                            <p className="text-xs text-muted-foreground">
                              {formatSignedNumber(accuracyResult.bias_percent, 2)}% · {accuracyBiasDirection}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>How To Read This Check</CardTitle>
                        <CardDescription>
                          Archived actual weather is the reference. Forecast values show what the selected approach would have predicted.
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-3 text-sm text-muted-foreground">
                          <li>Lower monthly and yearly misses mean the method matched the completed year more closely.</li>
                          <li>Positive bias means overprediction. Negative bias means underprediction.</li>
                          <li>The rating is based on monthly percentage error, while the kWh miss shows the real size of the error.</li>
                        </ul>
                      </CardContent>
                    </Card>
                  </div>

                    <Card>
                      <CardHeader>
                        <CardTitle>Actual Vs Forecast Summary</CardTitle>
                        <CardDescription>
                          Archived actual weather is the reference. Forecast values show what the selected method would have produced.
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Metric</TableHead>
                              <TableHead>Archived Actual</TableHead>
                              <TableHead>Forecast</TableHead>
                              <TableHead>Difference</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {accuracyComparisonRows.map((row) => (
                              <TableRow key={row.metric}>
                                <TableCell className="font-medium">{row.metric}</TableCell>
                                <TableCell>{row.actual}</TableCell>
                                <TableCell>{row.forecast}</TableCell>
                                <TableCell>{row.difference}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

                  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Forecast Approach Used</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyMethodLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Weather Reference Used</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyWeatherBasisLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Past Years Used For Learning</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyTrainingYearsLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">Data Source</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyResult.data_source}</div>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle>Monthly Forecast Vs Actual Energy</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={accuracyMonthlyEnergyChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="Forecast" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                            <Bar dataKey="Actual" fill="#10b981" radius={[2, 2, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Monthly Forecast Error</CardTitle>
                        <CardDescription>Positive means the forecast was too high. Negative means it was too low.</CardDescription>
                      </CardHeader>
                      <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={accuracyMonthlyErrorChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <ReferenceLine y={0} stroke="#94a3b8" />
                            <Bar dataKey="Forecast error (kWh)" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                    <AccordionItem value="accuracy-details" className="border-none">
                      <AccordionTrigger className="py-4 text-left hover:no-underline">
                        <div>
                          <p className="font-semibold">Technical Details</p>
                          <p className="text-sm font-normal text-muted-foreground">
                            Open this section for method metadata, fallback notes, and financial assumptions.
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Field</TableHead>
                              <TableHead>Value</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            <TableRow>
                              <TableCell>Requested forecast approach</TableCell>
                              <TableCell>{getForecastApproachLabel(accuracyResult.model_type_requested)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Forecast approach used</TableCell>
                              <TableCell>{accuracyMethodLabel}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Accuracy rating rule</TableCell>
                              <TableCell>{accuracyQualityDescription}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Weather reference used</TableCell>
                              <TableCell>{accuracyWeatherBasisLabel}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Past years used for learning</TableCell>
                              <TableCell>{accuracyTrainingYearsLabel}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Backup method note</TableCell>
                              <TableCell>{accuracyResult.fallback_reason || 'No backup method used'}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Data source</TableCell>
                              <TableCell>{accuracyResult.data_source}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Valuation basis</TableCell>
                              <TableCell>{accuracyResult.financial_assumptions.valuation_basis}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Annual savings basis</TableCell>
                              <TableCell>{accuracyResult.financial_assumptions.annual_savings_basis}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Payback basis</TableCell>
                              <TableCell>{accuracyResult.financial_assumptions.payback_basis}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>

                        {accuracyResult.ml_metadata && (
                          <div>
                            <p className="mb-2 text-sm font-medium">History-based forecast diagnostics</p>
                            <pre className="overflow-x-auto rounded-md bg-muted p-3 text-xs">
                              {JSON.stringify(accuracyResult.ml_metadata, null, 2)}
                            </pre>
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </>
              )}
            </TabsContent>

            <TabsContent value="benchmark" className="space-y-6">
              <div className="flex flex-col gap-4 rounded-lg border bg-muted/30 p-4 md:flex-row md:items-end md:justify-between">
                <div className="space-y-2">
                  <div>
                    <h3 className="font-medium">Forecast Method Comparison</h3>
                    <p className="text-sm text-muted-foreground">
                      Test each forecasting method against completed historical years ending in {evaluationYear}.
                    </p>
                  </div>
                  <div className="w-full max-w-sm space-y-2">
                    <div className="flex justify-between">
                      <Label>Comparison Window (years)</Label>
                      <span className="text-sm text-muted-foreground">{benchmarkYears}</span>
                    </div>
                    <Slider min={1} max={5} step={1} value={getSliderValue(benchmarkYears, 3)} onValueChange={handleBenchmarkYearsChange} />
                  </div>
                </div>
                <Button onClick={handleRunBenchmark} disabled={!position || isLoading}>
                  {isLoading ? 'Running...' : 'Compare Forecast Methods'}
                </Button>
              </div>

              {!benchmarkResult ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  Run the comparison to see which forecast method best matches completed past years for this site.
                </div>
              ) : (
                <>
                  <Alert>
                    <AlertTitle>How the historical reference is built</AlertTitle>
                    <AlertDescription>{benchmarkResult.reference_note}</AlertDescription>
                  </Alert>

                  <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
                    <Card className="border-primary/25 bg-primary/5">
                      <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-2">
                          <CardTitle>Recommended Method For This Site</CardTitle>
                          <CardDescription>
                            Based on completed years {benchmarkWindowLabel} with the current system settings.
                          </CardDescription>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary">Window {benchmarkWindowLabel}</Badge>
                            <Badge variant="outline">{benchmarkTrainingWindowLabel}</Badge>
                          </div>
                        </div>
                        {recommendedBenchmark ? <Badge className="w-fit">Best overall</Badge> : null}
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <p className="text-3xl font-semibold tracking-tight">{recommendedBenchmark?.label ?? 'No recommendation yet'}</p>
                          <p className="mt-2 text-sm text-muted-foreground">
                            {recommendedBenchmark
                              ? `${recommendedBenchmark.label} ranked best across yearly error, monthly error, and bias.`
                              : 'Run the comparison to generate a recommendation.'}
                          </p>
                        </div>
                        {recommendedBenchmark ? (
                          <div className="grid gap-3 sm:grid-cols-3">
                            <div className="rounded-lg border bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-wide text-muted-foreground">Avg yearly error</p>
                              <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(recommendedBenchmark.yearlyMaeKwh)} kWh</p>
                              <p className="text-xs text-muted-foreground">{formatSidebarNumber(recommendedBenchmark.yearlyMape, 2)}% yearly error</p>
                            </div>
                            <div className="rounded-lg border bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-wide text-muted-foreground">Avg monthly error</p>
                              <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(recommendedBenchmark.monthlyMaeKwh)} kWh</p>
                              <p className="text-xs text-muted-foreground">{formatSidebarNumber(recommendedBenchmark.monthlyMape, 2)}% monthly error</p>
                            </div>
                            <div className="rounded-lg border bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-wide text-muted-foreground">Average bias</p>
                              <p className="mt-1 text-lg font-semibold">{formatSignedNumber(recommendedBenchmark.biasKwh)} kWh</p>
                              <p className="text-xs text-muted-foreground">{recommendedBenchmark.biasDirection}</p>
                            </div>
                          </div>
                        ) : null}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>How To Read This Comparison</CardTitle>
                        <CardDescription>Every method uses the same system settings and the same PV conversion stack.</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-3 text-sm text-muted-foreground">
                          <li>Lower average yearly and monthly error means the method matched completed years more closely.</li>
                          <li>Bias near 0 means the method is not consistently too high or too low.</li>
                          <li>Backup logic means the model had to fall back to a simpler weather reference for one or more years.</li>
                        </ul>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-4 md:grid-cols-3">
                    {benchmarkResult.approaches.map((approach) => (
                      <Card
                        key={approach.approach}
                        className={recommendedBenchmark?.id === approach.approach ? 'border-primary/30 bg-primary/5' : undefined}
                      >
                        <CardHeader>
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <CardTitle>{getBenchmarkApproachLabel(approach.approach, approach.label)}</CardTitle>
                              <CardDescription>{approach.description}</CardDescription>
                            </div>
                            {recommendedBenchmark?.id === approach.approach ? <Badge variant="secondary">Best overall</Badge> : null}
                          </div>
                        </CardHeader>
                        <CardContent className="grid gap-3 sm:grid-cols-2">
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Avg yearly error</p>
                            <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(approach.metrics.yearly_mae_kwh)} kWh</p>
                          </div>
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">Average bias</p>
                            <p className="mt-1 text-lg font-semibold">{formatSignedNumber(approach.metrics.bias_kwh)} kWh</p>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Comparison Summary</CardTitle>
                      <CardDescription>Lower error is better. Bias close to 0 is better.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Approach</TableHead>
                            <TableHead>Avg Yearly Error</TableHead>
                            <TableHead>Avg Monthly Error</TableHead>
                            <TableHead>Yearly Error (%)</TableHead>
                            <TableHead>Bias</TableHead>
                            <TableHead>Backup Logic Used</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {rankedBenchmarkSummaryRows.map((row) => (
                            <TableRow key={row.id}>
                              <TableCell>
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="font-medium">{row.label}</span>
                                  {recommendedBenchmark?.id === row.id ? <Badge variant="secondary">Best overall</Badge> : null}
                                </div>
                              </TableCell>
                              <TableCell>{formatSidebarNumber(row.yearlyMaeKwh)} kWh</TableCell>
                              <TableCell>{formatSidebarNumber(row.monthlyMaeKwh)} kWh</TableCell>
                              <TableCell>{formatSidebarNumber(row.yearlyMape, 2)}%</TableCell>
                              <TableCell>
                                <div>{formatSignedNumber(row.biasKwh)} kWh</div>
                                <div className="text-xs text-muted-foreground">{formatSignedNumber(row.biasPercent, 2)}% · {row.biasDirection}</div>
                              </TableCell>
                              <TableCell>{row.fallbackSummary}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>

                  <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle>Historical Reference Vs Forecasts</CardTitle>
                        <CardDescription>Compare each method's yearly estimate against the shared historical reference.</CardDescription>
                      </CardHeader>
                      <CardContent className="h-[360px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={benchmarkEnergyChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="year" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey="Historical reference" stroke="#111827" strokeWidth={3} />
                            {benchmarkResult.approaches.map((approach, index) => (
                              <Line
                                key={approach.approach}
                                type="monotone"
                                dataKey={getBenchmarkApproachLabel(approach.approach, approach.label)}
                                stroke={CHART_COLORS[index % CHART_COLORS.length]}
                                strokeWidth={2}
                              />
                            ))}
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Forecast Error Comparison</CardTitle>
                        <CardDescription>Errors shown in kWh so the differences are easier to interpret.</CardDescription>
                      </CardHeader>
                      <CardContent className="h-[360px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={benchmarkMetricChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="approach" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <ReferenceLine y={0} stroke="#94a3b8" />
                            <Bar dataKey="Avg monthly error (kWh)" fill="#2563eb" />
                            <Bar dataKey="Avg yearly error (kWh)" fill="#10b981" />
                            <Bar dataKey="Average bias (kWh)" fill="#f59e0b" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                    <AccordionItem value="year-details" className="border-none">
                      <AccordionTrigger className="py-4 text-left hover:no-underline">
                        <div>
                          <p className="font-semibold">Advanced Year-By-Year Details</p>
                          <p className="text-sm font-normal text-muted-foreground">
                            Open this section for the per-year comparison, detailed bias, and backup-logic notes.
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Approach</TableHead>
                              <TableHead>Year</TableHead>
                              <TableHead>Historical Reference</TableHead>
                              <TableHead>Forecast Estimate</TableHead>
                              <TableHead>Absolute Error</TableHead>
                              <TableHead>Yearly Error (%)</TableHead>
                              <TableHead>Bias (kWh)</TableHead>
                              <TableHead>Backup Logic Note</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {benchmarkResult.approaches.flatMap((approach) =>
                              approach.yearly_results.map((result) => (
                                <TableRow key={`${approach.approach}-${result.year}`}>
                                  <TableCell className="font-medium">{getBenchmarkApproachLabel(approach.approach, approach.label)}</TableCell>
                                  <TableCell>{result.year}</TableCell>
                                  <TableCell>{formatSidebarNumber(result.actual_yearly_kwh)} kWh</TableCell>
                                  <TableCell>{formatSidebarNumber(result.predicted_yearly_kwh)} kWh</TableCell>
                                  <TableCell>{formatSidebarNumber(result.yearly_mae_kwh)} kWh</TableCell>
                                  <TableCell>{formatSidebarNumber(result.yearly_mape_percent, 2)}%</TableCell>
                                  <TableCell>{formatSignedNumber(result.yearly_bias_kwh)} kWh</TableCell>
                                  <TableCell>{result.fallback_reason || 'No backup logic used'}</TableCell>
                                </TableRow>
                              )),
                            )}
                          </TableBody>
                        </Table>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </>
              )}
            </TabsContent>

            <TabsContent value="scenarios" className="space-y-6">
              {!forecastData ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  Run the base forecast first. That forecast defines the shared location, forecast approach, and tariff used for every system option.
                </div>
              ) : (
                <>
                  <div className="flex flex-col gap-4 rounded-lg border bg-muted/30 p-4 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div>
                        <h3 className="font-medium">System Options Comparison</h3>
                        <p className="text-sm text-muted-foreground">
                          Same location, same forecast, same tariff. Only system design changes between options.
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="secondary">Base System included automatically</Badge>
                        <Badge variant="outline">{comparisonRequestedModelLabel}</Badge>
                      </div>
                    </div>
                    <p className="max-w-md text-sm text-muted-foreground">
                      Use this tab to compare design tradeoffs quickly without changing the shared weather or pricing context.
                    </p>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
                    <Card>
                      <CardHeader>
                        <CardTitle>Shared Comparison Context</CardTitle>
                        <CardDescription>These assumptions stay fixed for every option when you run the comparison.</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Shared setting</TableHead>
                              <TableHead>Value</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {comparisonSharedContextRows.map((row) => (
                              <TableRow key={row.label}>
                                <TableCell className="font-medium">{row.label}</TableCell>
                                <TableCell>{row.value}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>What Changes Per Option</CardTitle>
                        <CardDescription>Only these inputs change per option in this pass.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <ul className="space-y-3 text-sm text-muted-foreground">
                          <li>Name</li>
                          <li>Panel area change</li>
                          <li>Tilt</li>
                          <li>AC capacity</li>
                          <li>CAPEX</li>
                        </ul>
                        <p className="text-sm text-muted-foreground">
                          Every other system setting inherits from Base System, including panel efficiency, cleanliness, shading, gamma, and NOCT.
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Add Option</CardTitle>
                      <CardDescription>
                        Change only the option-specific fields below. Everything else inherits from Base System.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Option-specific controls in this pass: name, panel area change, tilt, AC capacity, and CAPEX.
                      </p>
                      <div className="flex flex-col items-end gap-4 md:flex-row">
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <Label>Option Name</Label>
                          <Input value={scenarioName} onChange={(event) => setScenarioName(event.target.value)} />
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <div className="flex justify-between">
                            <Label>Panel Area Change (%)</Label>
                            <span className="text-sm text-muted-foreground">{getSliderNumber(scenarioPanelAreaDelta, 20)}%</span>
                          </div>
                          <div className="w-full px-2">
                            <Slider
                              min={-50}
                              max={200}
                              step={5}
                              value={getSliderValue(scenarioPanelAreaDelta, 20)}
                              onValueChange={handleScenarioPanelAreaDeltaChange}
                            />
                          </div>
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <div className="flex justify-between">
                            <Label>Option Tilt (°)</Label>
                            <span className="text-sm text-muted-foreground">{getSliderNumber(scenarioTilt, 30)}</span>
                          </div>
                          <div className="w-full px-2">
                            <Slider min={0} max={60} step={1} value={getSliderValue(scenarioTilt, 30)} onValueChange={handleScenarioTiltChange} />
                          </div>
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <Label>Option AC Capacity (kW)</Label>
                          <Input
                            type="number"
                            value={scenarioAcCapacity}
                            onChange={(event) => setScenarioAcCapacity(event.target.value)}
                          />
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <Label>Option CAPEX</Label>
                          <Input type="number" value={scenarioCapex} onChange={(event) => setScenarioCapex(event.target.value)} />
                        </div>
                        <Button onClick={handleAddScenario}>Add Option</Button>
                      </div>
                    </CardContent>
                  </Card>

                  {configuredScenarioRows.length > 0 ? (
                    <div className="space-y-4">
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div>
                          <h3 className="text-lg font-semibold">Configured Options</h3>
                          <p className="text-sm text-muted-foreground">
                            Base System is added automatically when you run the comparison. The rows below are your alternative options.
                          </p>
                        </div>
                        <div className="space-x-2">
                          <Button
                            variant="outline"
                            onClick={() => {
                              setScenarioRequests([]);
                              setComparisonResult(null);
                            }}
                          >
                            Clear All
                          </Button>
                          <Button onClick={handleRunComparison} disabled={isLoading}>
                            {isLoading ? 'Running...' : 'Compare System Options'}
                          </Button>
                        </div>
                      </div>

                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Option</TableHead>
                            <TableHead>Panel Area (m²)</TableHead>
                            <TableHead>Tilt (°)</TableHead>
                            <TableHead>AC Capacity (kW)</TableHead>
                            <TableHead>CAPEX</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {configuredScenarioRows.map((scenario, index) => (
                            <TableRow key={scenario.id}>
                              <TableCell className="font-medium">
                                <Input
                                  value={scenario.label}
                                  onChange={(event) => {
                                    const next = [...scenarioRequests];
                                    next[index] = { ...next[index], name: event.target.value };
                                    setScenarioRequests(next);
                                  }}
                                  className="h-8 w-[150px]"
                                />
                              </TableCell>
                              <TableCell>
                                <div>{formatSidebarNumber(scenario.panelArea)} m²</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.panelAreaDelta)}`}>
                                  {formatSignedNumber(scenario.panelAreaDelta)} m² vs base
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>{formatSidebarNumber(scenario.tilt)}°</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.tiltDelta)}`}>
                                  {formatSignedNumber(scenario.tiltDelta)}° vs base
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>{formatSidebarNumber(scenario.acCapacityKw)} kW</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.acCapacityDelta)}`}>
                                  {formatSignedNumber(scenario.acCapacityDelta)} kW vs base
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>{formatCurrencyAmount(scenario.capex, currency, 0)}</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.capexDelta, false)}`}>
                                  {formatSignedCurrency(scenario.capexDelta, currency, 0)} vs base
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <Alert>
                      <AlertTitle>No saved options yet</AlertTitle>
                      <AlertDescription>
                        Add at least one alternative option. Base System is included automatically when you run the comparison.
                      </AlertDescription>
                    </Alert>
                  )}

                  {comparisonResult && (
                    <div className="mt-8 space-y-6">
                      {comparisonResult.fallback_reason && (
                        <Alert>
                          <AlertTitle>Backup forecast method used</AlertTitle>
                          <AlertDescription>{comparisonResult.fallback_reason}</AlertDescription>
                        </Alert>
                      )}

                      <Card className="border-primary/25 bg-primary/5">
                        <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                          <div className="space-y-2">
                            <CardTitle>{comparisonRecommendationTitle}</CardTitle>
                            <CardDescription>Decision-first summary across Base System and every configured option.</CardDescription>
                            <div className="flex flex-wrap gap-2">
                              <Badge variant="secondary">Base System stays visible as the reference</Badge>
                              {recommendedScenario ? <Badge variant="outline">Highlighted option: {recommendedScenario.label}</Badge> : null}
                            </div>
                          </div>
                          {recommendedScenario ? <Badge className="w-fit">Decision-first summary</Badge> : null}
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <p className="text-3xl font-semibold tracking-tight">{recommendedScenario?.label ?? 'No recommendation yet'}</p>
                            <p className="mt-2 text-sm text-muted-foreground">{comparisonRecommendationSummary}</p>
                            <p className="mt-2 text-sm text-muted-foreground">{comparisonRecommendationDetail}</p>
                          </div>
                          {recommendedScenario ? (
                            <div className="grid gap-3 sm:grid-cols-4">
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">Yearly energy</p>
                                <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(recommendedScenario.yearlyKwh)} kWh</p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">Annual savings</p>
                                <p className="mt-1 text-lg font-semibold">
                                  {formatCurrencyAmount(recommendedScenario.annualSavings, recommendedScenario.currency)}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">Simple payback</p>
                                <p className="mt-1 text-lg font-semibold">{formatPaybackYears(recommendedScenario.simplePaybackYears)}</p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">CAPEX</p>
                                <p className="mt-1 text-lg font-semibold">
                                  {formatCurrencyAmount(recommendedScenario.capex, recommendedScenario.currency, 0)}
                                </p>
                              </div>
                            </div>
                          ) : null}
                        </CardContent>
                      </Card>

                      <div className="grid gap-4 md:grid-cols-3">
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Best Payback</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-xl font-semibold">{bestPaybackScenario?.label ?? 'No viable payback'}</div>
                            <p className="text-sm text-muted-foreground">
                              {bestPaybackScenario ? formatPaybackYears(bestPaybackScenario.simplePaybackYears) : 'All options are not viable under the current CAPEX/tariff assumptions.'}
                            </p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Highest Savings</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-xl font-semibold">{highestSavingsScenario?.label ?? 'No data'}</div>
                            <p className="text-sm text-muted-foreground">
                              {highestSavingsScenario
                                ? formatCurrencyAmount(highestSavingsScenario.annualSavings, highestSavingsScenario.currency)
                                : 'No data'}
                            </p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Most Energy</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-xl font-semibold">{mostEnergyScenario?.label ?? 'No data'}</div>
                            <p className="text-sm text-muted-foreground">
                              {mostEnergyScenario ? `${formatSidebarNumber(mostEnergyScenario.yearlyKwh)} kWh/year` : 'No data'}
                            </p>
                          </CardContent>
                        </Card>
                      </div>

                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                        {comparisonOptionRows.map((row) => (
                          <Card
                            key={row.id}
                            className={
                              recommendedScenario?.id === row.id
                                ? 'border-primary/30 bg-primary/5'
                                : row.isBaseline
                                  ? 'border-border/80'
                                  : undefined
                            }
                          >
                            <CardHeader>
                              <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base">
                                <span>{row.label}</span>
                                <div className="flex flex-wrap gap-2">
                                  {row.isBaseline ? <Badge variant="secondary">Base System</Badge> : null}
                                  {recommendedScenario?.id === row.id ? <Badge variant="outline">Recommended</Badge> : null}
                                </div>
                              </CardTitle>
                              <CardDescription>
                                {row.isBaseline
                                  ? 'Reference option for every change shown below.'
                                  : 'Compared against Base System under the same forecast and tariff assumptions.'}
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">Yearly energy</span>
                                  <span className="font-semibold">{formatSidebarNumber(row.yearlyKwh)} kWh</span>
                                </div>
                                <p className={`mt-1 text-xs ${row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.energyDeltaPercent)}`}>
                                  {row.isBaseline
                                    ? 'Reference option'
                                    : `${formatSignedNumber(row.energyDeltaKwh)} kWh · ${formatSignedPercent(row.energyDeltaPercent)} vs base`}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">Annual savings</span>
                                  <span className="font-semibold">{formatCurrencyAmount(row.annualSavings, row.currency)}</span>
                                </div>
                                <p className={`mt-1 text-xs ${row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.savingsDeltaPercent)}`}>
                                  {row.isBaseline
                                    ? 'Reference option'
                                    : `${formatSignedCurrency(row.savingsDeltaValue, row.currency)} · ${formatSignedPercent(row.savingsDeltaPercent)} vs base`}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">Simple payback</span>
                                  <span className="font-semibold">{formatPaybackYears(row.simplePaybackYears)}</span>
                                </div>
                                <p className={`mt-1 text-xs ${row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.paybackDeltaYears, false)}`}>
                                  {row.isBaseline
                                    ? 'Reference option'
                                    : row.paybackDeltaYears == null
                                      ? 'No comparable payback delta'
                                      : `${formatSignedNumber(row.paybackDeltaYears, 1)} years vs base`}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">CAPEX</span>
                                  <span className="font-semibold">{formatCurrencyAmount(row.capex, row.currency, 0)}</span>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle>Monthly Energy By Option</CardTitle>
                          <CardDescription>Base System is the reference line. The recommended option is emphasized when it is not the base system.</CardDescription>
                        </CardHeader>
                        <CardContent className="h-[400px]">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={comparisonChartData}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              {comparisonResult.results.map((result, index) => {
                                const isBaseLine = index === 0;
                                const isRecommendedLine = index === recommendedScenarioIndex;
                                const stroke = isBaseLine ? '#111827' : CHART_COLORS[index % CHART_COLORS.length];

                                return (
                                <Line
                                  key={result.scenario.name}
                                  type="monotone"
                                  dataKey={result.scenario.name}
                                  stroke={stroke}
                                  strokeWidth={isBaseLine || isRecommendedLine ? 3 : 2}
                                  strokeDasharray={isBaseLine || isRecommendedLine ? '' : '6 4'}
                                  opacity={isBaseLine || isRecommendedLine ? 1 : 0.85}
                                />
                                );
                              })}
                            </LineChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader>
                          <CardTitle>All Options At A Glance</CardTitle>
                          <CardDescription>Positive energy and savings changes are better. Lower payback deltas are better.</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Option</TableHead>
                                <TableHead>Yearly Energy</TableHead>
                                <TableHead>Energy vs Base</TableHead>
                                <TableHead>Annual Savings</TableHead>
                                <TableHead>Savings vs Base</TableHead>
                                <TableHead>Payback</TableHead>
                                <TableHead>Payback vs Base</TableHead>
                                <TableHead>CAPEX</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {comparisonOptionRows.map((row) => (
                                <TableRow key={row.id}>
                                  <TableCell>
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="font-medium">{row.label}</span>
                                      {row.isBaseline ? <Badge variant="secondary">Base System</Badge> : null}
                                      {recommendedScenario?.id === row.id ? <Badge variant="outline">Recommended</Badge> : null}
                                    </div>
                                  </TableCell>
                                  <TableCell>{formatSidebarNumber(row.yearlyKwh)} kWh</TableCell>
                                  <TableCell className={row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.energyDeltaPercent)}>
                                    {row.isBaseline
                                      ? 'Reference option'
                                      : `${formatSignedNumber(row.energyDeltaKwh)} kWh · ${formatSignedPercent(row.energyDeltaPercent)}`}
                                  </TableCell>
                                  <TableCell>{formatCurrencyAmount(row.annualSavings, row.currency)}</TableCell>
                                  <TableCell className={row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.savingsDeltaPercent)}>
                                    {row.isBaseline
                                      ? 'Reference option'
                                      : `${formatSignedCurrency(row.savingsDeltaValue, row.currency)} · ${formatSignedPercent(row.savingsDeltaPercent)}`}
                                  </TableCell>
                                  <TableCell>{formatPaybackYears(row.simplePaybackYears)}</TableCell>
                                  <TableCell className={row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.paybackDeltaYears, false)}>
                                    {row.isBaseline
                                      ? 'Reference option'
                                      : row.paybackDeltaYears == null
                                        ? 'Not comparable'
                                        : `${formatSignedNumber(row.paybackDeltaYears, 1)} years`}
                                  </TableCell>
                                  <TableCell>{formatCurrencyAmount(row.capex, row.currency, 0)}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </CardContent>
                      </Card>

                      <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                        <AccordionItem value="scenario-details" className="border-none">
                          <AccordionTrigger className="py-4 text-left hover:no-underline">
                            <div>
                              <p className="font-semibold">Technical Details</p>
                              <p className="text-sm font-normal text-muted-foreground">
                                Open this section for model metadata, weather reference details, and data-source notes.
                              </p>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent className="pb-4">
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Field</TableHead>
                                  <TableHead>Value</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {comparisonTechnicalRows.map((row) => (
                                  <TableRow key={row.field}>
                                    <TableCell className="font-medium">{row.field}</TableCell>
                                    <TableCell>{row.value}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </AccordionContent>
                        </AccordionItem>
                      </Accordion>
                    </div>
                  )}
                </>
              )}
            </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useRef, useState, type CSSProperties, type MouseEvent as ReactMouseEvent, type MutableRefObject, type ReactNode } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { DollarSign, GripVertical, MapPin, Moon, PanelLeftClose, PanelLeftOpen, Settings, Sun } from 'lucide-react';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { APP_DEFAULTS } from '@/lib/defaults';

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
const DEFAULT_SIDEBAR_WIDTH = 368;
const MIN_SIDEBAR_WIDTH = 304;
const MAX_SIDEBAR_WIDTH = 560;
const COLLAPSED_SIDEBAR_WIDTH = 72;
const LEGACY_SYSTEM_CAPEX_DEFAULT = 25000;
type Language = 'en' | 'he';
const FORECAST_APPROACH_COPY: Record<
  Language,
  Record<
  ModelType,
  { label: string; shortLabel: string }
  >
> = {
  en: {
    physical: {
      label: 'Physics-based forecast',
      shortLabel: 'Physics-based',
    },
    ml: {
      label: 'History-based forecast',
      shortLabel: 'History-based',
    },
  },
  he: {
    physical: {
      label: 'תחזית פיזיקלית',
      shortLabel: 'פיזיקלית',
    },
    ml: {
      label: 'תחזית מבוססת היסטוריה',
      shortLabel: 'מבוססת היסטוריה',
    },
  },
};

const UI_COPY: Record<Language, Record<string, string>> = {
  en: {
    languageButton: 'עברית',
    themeToggle: 'Toggle theme',
    appTitle: 'Solar Forecast',
    appSubtitle: 'Estimate production, savings, and payback for one site.',
    controls: 'Controls',
    location: 'Location',
    city: 'City',
    chooseCity: 'Choose city',
    customMapPoint: 'Custom map point',
    address: 'Address',
    addressHelp: 'Search a full street address for a more accurate site location.',
    addressPlaceholder: 'Street, city, country',
    find: 'Find',
    selectedAddress: 'Selected Address',
    noAddress: 'No address selected yet.',
    systemParameters: 'System Parameters',
    forecastYear: 'Forecast Year',
    forecastYearHelp: 'The year to estimate solar production for.',
    panelArea: 'Panel Area (m²)',
    panelAreaHelp: 'Total panel surface. Draw on the map to estimate it automatically.',
    acCapacity: 'AC Capacity (kW)',
    acCapacityHelp: 'Maximum inverter output delivered as AC power.',
    approach: 'Approach',
    approachHelp: 'Physics uses panel and weather assumptions. History learns from past production patterns.',
    learningYears: 'Learning Years',
    learningYearsHelp: 'More years gives a steadier forecast. Fewer years reacts more to recent patterns.',
    advanced: 'Advanced',
    panelEfficiency: 'Panel Efficiency',
    panelEfficiencyHelp: 'Percentage of sunlight converted into electricity.',
    tilt: 'Tilt (°)',
    tiltHelp: 'Panel angle relative to flat ground.',
    cleanliness: 'Cleanliness',
    cleanlinessHelp: 'Adjusts energy loss from dust, dirt, or snow.',
    shading: 'Shading',
    shadingHelp: 'Adjusts energy loss from nearby shadows.',
    temperatureCoefficient: 'Temperature Coefficient',
    temperatureCoefficientHelp: 'How quickly panel efficiency drops as temperature rises.',
    noct: 'NOCT (°C)',
    noctHelp: 'Nominal cell temperature under standard operating conditions.',
    financial: 'Financial',
    tariff: 'Tariff',
    tariffHelp: 'Price per kWh used to estimate value and savings.',
    currency: 'Currency',
    currencyHelp: 'Currency for financial estimates.',
    capex: 'CAPEX',
    capexHelp: 'System cost used for savings and payback.',
    runForecast: 'Run Forecast',
    running: 'Running...',
    expandSidebar: 'Expand sidebar',
    minimizeSidebar: 'Minimize sidebar',
    resizeSidebar: 'Resize sidebar',
    chooseLocation: 'Choose Location',
    tabOverview: 'Overview',
    tabDay: 'Day',
    tabAccuracy: 'Accuracy',
    tabMethods: 'Methods',
    tabOptions: 'Options',
    emptyOverview: 'Choose a location, then run forecast.',
    summary: 'Summary',
    summaryHelp: 'Yearly production, savings, and simple payback from the current inputs.',
    keyResults: 'Key Results',
    yearlyEnergy: 'Yearly Energy',
    annualSavings: 'Annual Savings',
    simplePayback: 'Simple Payback',
    context: 'Context',
    contextHelp: 'Inputs and assumptions used for this forecast.',
    performance: 'Performance',
    performanceHelp: 'Supporting production metrics for benchmarking.',
    specificYield: 'Specific Yield',
    averageDailyEnergy: 'Average Daily Energy',
    monthlyEnergyForecast: 'Monthly Energy Forecast',
    monthlyValue: 'Monthly Value',
    monthlyValueHelp: 'Estimated money by month using the current tariff.',
    seasonalSplit: 'Seasonal Split',
    seasonalSplitHelp: 'Shows where annual output is concentrated across the year.',
    details: 'Details',
    overviewDetailsHelp: 'Method, data source, and financial assumptions.',
    dayEmpty: 'Run forecast to see hourly output.',
    daySummary: 'Day Summary',
    daySummaryHelp: 'Expected production, value, and peak power for the simulated day.',
    dailyEnergy: 'Daily Energy',
    dailyValue: 'Daily Value',
    peakPower: 'Peak Power',
    peakHour: 'Peak Hour',
    systemLosses: 'System Losses',
    hourlyPower: 'Hourly Power',
    hourlyPowerHelp: 'Local-time AC output for the simulated day.',
    dayDetailsHelp: 'Raw loss, source, and forecast context fields.',
    accuracyTitle: 'Accuracy Check',
    accuracyTitleHelp: 'Tests the selected forecast approach on a completed year.',
    runAccuracy: 'Run Accuracy',
    accuracyEmpty: 'Run accuracy to compare forecast vs archive.',
    takeaway: 'Takeaway',
    takeawayHelp: 'Lower error is better. Positive bias means overprediction; negative bias means underprediction.',
    accuracyRating: 'Accuracy rating',
    avgMonthlyMiss: 'Avg monthly miss',
    yearlyMiss: 'Yearly miss',
    bias: 'Bias',
    actualVsForecast: 'Actual vs Forecast',
    actualVsForecastHelp: 'Archive is the reference. Forecast shows what the selected method would have produced.',
    methodApproach: 'Approach',
    weatherReference: 'Weather Reference',
    dataSource: 'Data Source',
    monthlyForecastVsActual: 'Monthly Forecast vs Actual Energy',
    monthlyError: 'Monthly Error',
    monthlyErrorHelp: 'Positive means the forecast was too high. Negative means it was too low.',
    accuracyDetailsHelp: 'Method metadata, fallback notes, and financial assumptions.',
    compareMethods: 'Compare Methods',
    compareMethodsHelpPrefix: 'Tests forecasting methods against completed historical years ending in',
    comparisonWindow: 'Comparison Window (years)',
    compareForecastMethods: 'Compare Methods',
    methodsEmpty: 'Compare methods against past years.',
    historicalReference: 'Historical Reference',
    recommendedMethod: 'Recommended Method',
    recommendedMethodHelp: 'Best fit across yearly error, monthly error, and bias.',
    bestOverall: 'Best overall',
    avgYearlyError: 'Avg yearly error',
    avgMonthlyError: 'Avg monthly error',
    averageBias: 'Average bias',
    methodSummaryHelp: 'Lower error is better. Bias close to 0 is better.',
    referenceVsForecasts: 'Reference vs Forecasts',
    referenceVsForecastsHelp: "Each method's yearly estimate compared with the shared historical reference.",
    errorComparison: 'Error Comparison',
    errorComparisonHelp: 'Errors are shown in kWh for easier comparison.',
    yearDetails: 'Year Details',
    yearDetailsHelp: 'Per-year comparison, detailed bias, and backup notes.',
    optionsEmpty: 'Run forecast first to compare options.',
    compareOptions: 'Compare Options',
    compareOptionsHelp: 'Same location, forecast, and tariff. Only system design changes.',
    baseIncluded: 'Base included',
    sharedContext: 'Shared Context',
    sharedContextHelp: 'These assumptions stay fixed for every option.',
    optionInputs: 'Option Inputs',
    optionInputsHelp: 'Only name, panel area, tilt, AC capacity, and CAPEX change per option.',
    name: 'Name',
    panelAreaChange: 'Panel area change',
    acCapacityShort: 'AC capacity',
    addOption: 'Add Option',
    addOptionHelp: 'Everything not shown here inherits from Base System.',
    optionName: 'Option Name',
    optionTilt: 'Option Tilt (°)',
    optionCapex: 'Option CAPEX',
    configuredOptions: 'Configured Options',
    clearAll: 'Clear All',
    compareSystemOptions: 'Compare Options',
    noSavedOptions: 'No saved options yet',
    noSavedOptionsHelp: 'Add one option. Base is included automatically.',
    recommended: 'Recommended',
    baseReference: 'Base reference',
    highlightedOption: 'Highlighted option',
    bestPayback: 'Best Payback',
    highestSavings: 'Highest Savings',
    mostEnergy: 'Most Energy',
    monthlyEnergy: 'Monthly Energy',
    monthlyEnergyHelp: 'Base System is the reference line. The recommended option is emphasized.',
    allOptions: 'All Options',
    allOptionsHelp: 'Positive energy and savings changes are better. Lower payback deltas are better.',
    optionsDetailsHelp: 'Model metadata, weather reference details, and data-source notes.',
  },
  he: {
    languageButton: 'English',
    themeToggle: 'החלפת מצב תצוגה',
    appTitle: 'תחזית סולארית',
    appSubtitle: 'הערכת ייצור, חיסכון והחזר השקעה לאתר אחד.',
    controls: 'בקרה',
    location: 'מיקום',
    city: 'עיר',
    chooseCity: 'בחר עיר',
    customMapPoint: 'נקודה במפה',
    address: 'כתובת',
    addressHelp: 'חיפוש כתובת מלאה נותן מיקום מדויק יותר.',
    addressPlaceholder: 'רחוב, עיר, מדינה',
    find: 'חפש',
    selectedAddress: 'כתובת נבחרת',
    noAddress: 'עדיין לא נבחרה כתובת.',
    systemParameters: 'פרטי מערכת',
    forecastYear: 'שנת תחזית',
    forecastYearHelp: 'השנה שעבורה מחשבים ייצור סולארי.',
    panelArea: 'שטח פאנלים (מ״ר)',
    panelAreaHelp: 'שטח הפאנלים הכולל. אפשר לסמן על המפה כדי להעריך אוטומטית.',
    acCapacity: 'הספק AC (kW)',
    acCapacityHelp: 'הספק היציאה המרבי של הממיר.',
    approach: 'שיטה',
    approachHelp: 'פיזיקלית משתמשת בנתוני פאנלים ומזג אוויר. היסטורית לומדת מדפוסי עבר.',
    learningYears: 'שנות למידה',
    learningYearsHelp: 'יותר שנים נותנות תחזית יציבה יותר. פחות שנים מגיבות יותר לדפוסים אחרונים.',
    advanced: 'מתקדם',
    panelEfficiency: 'יעילות פאנלים',
    panelEfficiencyHelp: 'אחוז אור השמש שהפאנלים ממירים לחשמל.',
    tilt: 'זווית (°)',
    tiltHelp: 'זווית הפאנלים ביחס לקרקע שטוחה.',
    cleanliness: 'ניקיון',
    cleanlinessHelp: 'התאמת איבוד אנרגיה מאבק, לכלוך או שלג.',
    shading: 'הצללה',
    shadingHelp: 'התאמת איבוד אנרגיה מצללים סמוכים.',
    temperatureCoefficient: 'מקדם טמפרטורה',
    temperatureCoefficientHelp: 'קצב ירידת יעילות הפאנלים כשהטמפרטורה עולה.',
    noct: 'NOCT (°C)',
    noctHelp: 'טמפרטורת תא נומינלית בתנאי עבודה סטנדרטיים.',
    financial: 'כספים',
    tariff: 'תעריף',
    tariffHelp: 'מחיר לקוט״ש לחישוב ערך וחיסכון.',
    currency: 'מטבע',
    currencyHelp: 'המטבע לחישובים כספיים.',
    capex: 'עלות מערכת',
    capexHelp: 'עלות המערכת לחישוב חיסכון והחזר.',
    runForecast: 'הרץ תחזית',
    running: 'רץ...',
    expandSidebar: 'הרחב תפריט',
    minimizeSidebar: 'מזער תפריט',
    resizeSidebar: 'שנה רוחב תפריט',
    chooseLocation: 'בחר מיקום',
    tabOverview: 'סקירה',
    tabDay: 'יום',
    tabAccuracy: 'דיוק',
    tabMethods: 'שיטות',
    tabOptions: 'אפשרויות',
    emptyOverview: 'בחר מיקום ואז הרץ תחזית.',
    summary: 'סיכום',
    summaryHelp: 'ייצור שנתי, חיסכון והחזר השקעה לפי הקלט הנוכחי.',
    keyResults: 'תוצאות מרכזיות',
    yearlyEnergy: 'אנרגיה שנתית',
    annualSavings: 'חיסכון שנתי',
    simplePayback: 'החזר השקעה',
    context: 'הקשר',
    contextHelp: 'קלטים והנחות ששימשו לתחזית.',
    performance: 'ביצועים',
    performanceHelp: 'מדדי ייצור תומכים להשוואה.',
    specificYield: 'תפוקה סגולית',
    averageDailyEnergy: 'אנרגיה יומית ממוצעת',
    monthlyEnergyForecast: 'תחזית אנרגיה חודשית',
    monthlyValue: 'ערך חודשי',
    monthlyValueHelp: 'הערכת כסף לפי חודש על בסיס התעריף הנוכחי.',
    seasonalSplit: 'חלוקה עונתית',
    seasonalSplitHelp: 'מראה איפה הייצור השנתי מרוכז לאורך השנה.',
    details: 'פרטים',
    overviewDetailsHelp: 'שיטה, מקור נתונים והנחות כספיות.',
    dayEmpty: 'הרץ תחזית כדי לראות תפוקה שעתית.',
    daySummary: 'סיכום יום',
    daySummaryHelp: 'ייצור, ערך ושיא הספק ביום המדומה.',
    dailyEnergy: 'אנרגיה יומית',
    dailyValue: 'ערך יומי',
    peakPower: 'שיא הספק',
    peakHour: 'שעת שיא',
    systemLosses: 'איבודי מערכת',
    hourlyPower: 'הספק שעתי',
    hourlyPowerHelp: 'תפוקת AC לפי זמן מקומי ביום המדומה.',
    dayDetailsHelp: 'איבוד גולמי, מקור ושדות הקשר לתחזית.',
    accuracyTitle: 'בדיקת דיוק',
    accuracyTitleHelp: 'בודק את שיטת התחזית על שנה שהסתיימה.',
    runAccuracy: 'בדוק דיוק',
    accuracyEmpty: 'הרץ בדיקת דיוק כדי להשוות תחזית מול ארכיון.',
    takeaway: 'מסקנה',
    takeawayHelp: 'שגיאה נמוכה יותר טובה יותר. הטיה חיובית היא הערכת יתר; שלילית היא הערכת חסר.',
    accuracyRating: 'דירוג דיוק',
    avgMonthlyMiss: 'פספוס חודשי ממוצע',
    yearlyMiss: 'פספוס שנתי',
    bias: 'הטיה',
    actualVsForecast: 'בפועל מול תחזית',
    actualVsForecastHelp: 'הארכיון הוא הייחוס. התחזית מראה מה השיטה הייתה מפיקה.',
    methodApproach: 'שיטה',
    weatherReference: 'ייחוס מזג אוויר',
    dataSource: 'מקור נתונים',
    monthlyForecastVsActual: 'תחזית מול בפועל לפי חודש',
    monthlyError: 'שגיאה חודשית',
    monthlyErrorHelp: 'חיובי אומר שהתחזית הייתה גבוהה מדי. שלילי אומר נמוכה מדי.',
    accuracyDetailsHelp: 'מטא-דאטה של השיטה, הערות גיבוי והנחות כספיות.',
    compareMethods: 'השוואת שיטות',
    compareMethodsHelpPrefix: 'בודק שיטות תחזית מול שנים היסטוריות שהסתיימו עד',
    comparisonWindow: 'חלון השוואה (שנים)',
    compareForecastMethods: 'השווה שיטות',
    methodsEmpty: 'השווה שיטות מול שנים קודמות.',
    historicalReference: 'ייחוס היסטורי',
    recommendedMethod: 'שיטה מומלצת',
    recommendedMethodHelp: 'ההתאמה הטובה ביותר לפי שגיאה שנתית, שגיאה חודשית והטיה.',
    bestOverall: 'הטובה ביותר',
    avgYearlyError: 'שגיאה שנתית ממוצעת',
    avgMonthlyError: 'שגיאה חודשית ממוצעת',
    averageBias: 'הטיה ממוצעת',
    methodSummaryHelp: 'שגיאה נמוכה יותר טובה יותר. הטיה קרובה ל-0 טובה יותר.',
    referenceVsForecasts: 'ייחוס מול תחזיות',
    referenceVsForecastsHelp: 'הערכת כל שיטה מול הייחוס ההיסטורי המשותף.',
    errorComparison: 'השוואת שגיאות',
    errorComparisonHelp: 'השגיאות מוצגות בקוט״ש להשוואה נוחה.',
    yearDetails: 'פירוט שנים',
    yearDetailsHelp: 'השוואה לפי שנה, הטיה מפורטת והערות גיבוי.',
    optionsEmpty: 'הרץ תחזית כדי להשוות אפשרויות.',
    compareOptions: 'השוואת אפשרויות',
    compareOptionsHelp: 'אותו מיקום, תחזית ותעריף. רק עיצוב המערכת משתנה.',
    baseIncluded: 'בסיס כלול',
    sharedContext: 'הקשר משותף',
    sharedContextHelp: 'ההנחות האלה קבועות לכל האפשרויות.',
    optionInputs: 'קלטי אפשרות',
    optionInputsHelp: 'רק שם, שטח פאנלים, זווית, הספק AC ועלות משתנים לכל אפשרות.',
    name: 'שם',
    panelAreaChange: 'שינוי שטח פאנלים',
    acCapacityShort: 'הספק AC',
    addOption: 'הוסף אפשרות',
    addOptionHelp: 'כל מה שלא מוצג כאן יורש ממערכת הבסיס.',
    optionName: 'שם אפשרות',
    optionTilt: 'זווית אפשרות (°)',
    optionCapex: 'עלות אפשרות',
    configuredOptions: 'אפשרויות מוגדרות',
    clearAll: 'נקה הכל',
    compareSystemOptions: 'השווה אפשרויות',
    noSavedOptions: 'אין אפשרויות שמורות',
    noSavedOptionsHelp: 'הוסף אפשרות אחת. הבסיס כלול אוטומטית.',
    recommended: 'מומלץ',
    baseReference: 'בסיס להשוואה',
    highlightedOption: 'אפשרות מודגשת',
    bestPayback: 'החזר הטוב ביותר',
    highestSavings: 'החיסכון הגבוה ביותר',
    mostEnergy: 'הכי הרבה אנרגיה',
    monthlyEnergy: 'אנרגיה חודשית',
    monthlyEnergyHelp: 'מערכת הבסיס היא קו הייחוס. האפשרות המומלצת מודגשת.',
    allOptions: 'כל האפשרויות',
    allOptionsHelp: 'שינוי חיובי באנרגיה ובחיסכון טוב יותר. דלתא החזר נמוכה יותר טובה יותר.',
    optionsDetailsHelp: 'מטא-דאטה של המודל, ייחוס מזג אוויר והערות מקור נתונים.',
  },
};

function HelpTip({ children, label = 'More info' }: { children: ReactNode; label?: string }) {
  return (
    <span className="group relative inline-flex align-middle">
      <span
        tabIndex={0}
        aria-label={label}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-border bg-background text-[10px] font-semibold leading-none text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        ?
      </span>
      <span className="pointer-events-none absolute left-1/2 top-6 z-50 hidden w-64 -translate-x-1/2 rounded-md border bg-popover px-3 py-2 text-xs font-normal leading-5 text-popover-foreground shadow-md group-hover:block group-focus-within:block">
        {children}
      </span>
    </span>
  );
}

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
  { id: 'telaviv', label: 'Tel Aviv, Israel', labelHe: 'תל אביב, ישראל', lat: 32.0853, lng: 34.7818 },
  { id: 'newyork', label: 'New York, USA', labelHe: 'ניו יורק, ארה״ב', lat: 40.7128, lng: -74.006 },
  { id: 'london', label: 'London, UK', labelHe: 'לונדון, בריטניה', lat: 51.5074, lng: -0.1278 },
  { id: 'tokyo', label: 'Tokyo, Japan', labelHe: 'טוקיו, יפן', lat: 35.6762, lng: 139.6503 },
  { id: 'sydney', label: 'Sydney, Australia', labelHe: 'סידני, אוסטרליה', lat: -33.8688, lng: 151.2093 },
  { id: 'berlin', label: 'Berlin, Germany', labelHe: 'ברלין, גרמניה', lat: 52.52, lng: 13.405 },
  { id: 'paris', label: 'Paris, France', labelHe: 'פריז, צרפת', lat: 48.8566, lng: 2.3522 },
  { id: 'sanfrancisco', label: 'San Francisco, USA', labelHe: 'סן פרנסיסקו, ארה״ב', lat: 37.7749, lng: -122.4194 },
];

function formatPaybackYears(paybackYears: number | null | undefined, language: Language = 'en'): string {
  if (paybackYears == null || Number.isNaN(paybackYears)) {
    return language === 'he' ? 'לא כדאי' : 'Not viable';
  }
  return language === 'he' ? `${formatReadableNumber(paybackYears, 1)} שנים` : `${formatReadableNumber(paybackYears, 1)} years`;
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

function getForecastApproachLabel(modelType: ModelType, language: Language = 'en'): string {
  return FORECAST_APPROACH_COPY[language][modelType].label;
}

function getForecastApproachShortLabel(modelType: ModelType, language: Language = 'en'): string {
  return FORECAST_APPROACH_COPY[language][modelType].shortLabel;
}

function getBenchmarkApproachLabel(approachType: BenchmarkApproachType, fallbackLabel: string, language: Language = 'en'): string {
  if (approachType === 'physical' || approachType === 'ml') {
    return getForecastApproachLabel(approachType, language);
  }
  return fallbackLabel;
}

function formatLearningYearsUsed(years: number[] | undefined, language: Language = 'en'): string {
  return years && years.length > 0 ? years.join(', ') : language === 'he' ? 'לא בשימוש' : 'Not used';
}

function describeBiasDirection(biasPercent: number, language: Language = 'en'): string {
  if (!Number.isFinite(biasPercent) || Math.abs(biasPercent) < 1) {
    return language === 'he' ? 'ההטיה כמעט ניטרלית' : 'Bias is close to neutral';
  }
  if (language === 'he') {
    return biasPercent > 0 ? 'נוטה להערכת יתר' : 'נוטה להערכת חסר';
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

function getAccuracyQualityDescription(quality: AccuracyQuality, language: Language = 'en'): string {
  if (quality === 'EXCELLENT') {
    return language === 'he' ? 'השגיאה החודשית נשארה מתחת ל-10%.' : 'Monthly error stayed under 10%.';
  }
  if (quality === 'GOOD') {
    return language === 'he'
      ? 'השגיאה החודשית נשארה מתחת ל-25%, אך עדיין יש שונות בין חודשים.'
      : 'Monthly error stayed under 25%, but there is still noticeable spread month to month.';
  }
  return language === 'he'
    ? 'השגיאה החודשית הגיעה ל-25% או יותר, לכן כדאי להשתמש בתחזית בזהירות.'
    : 'Monthly error reached 25% or more, so the forecast should be used with caution.';
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

function buildAccuracyTakeaway(quality: AccuracyQuality, biasPercent: number, language: Language = 'en'): { headline: string; description: string } {
  const biasDirection = describeBiasDirection(biasPercent, language);
  const biasDirectionLower = biasDirection.toLowerCase();

  if (language === 'he') {
    if (quality === 'EXCELLENT') {
      return {
        headline: 'השיטה התאימה היטב לשנה שנבחרה',
        description: Math.abs(biasPercent) < 5 ? 'הפספוסים החודשיים והשנתיים היו נמוכים.' : biasDirection,
      };
    }
    if (quality === 'GOOD') {
      return {
        headline: 'השיטה שימושית, אך יש תנודות חודשיות',
        description: biasDirection,
      };
    }
    return {
      headline: 'השיטה התקשתה בשנה שנבחרה',
      description: biasDirection,
    };
  }

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

function formatPaybackDelta(actual: number | null | undefined, predicted: number | null | undefined, language: Language = 'en'): string {
  if (actual == null || predicted == null || Number.isNaN(actual) || Number.isNaN(predicted)) {
    return language === 'he' ? 'לא ניתן להשוואה' : 'Not comparable';
  }
  return language === 'he' ? `${formatSignedNumber(predicted - actual, 1)} שנים` : `${formatSignedNumber(predicted - actual, 1)} years`;
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

function formatWeatherReferenceLabel(weatherReferenceYear: number | null | undefined, language: Language = 'en'): string {
  if (weatherReferenceYear == null) {
    return language === 'he' ? 'פרופיל מזג אוויר שנוצר במודל' : 'Model-generated weather profile';
  }
  return language === 'he' ? `מזג אוויר מארכיון ${weatherReferenceYear}` : `Archived weather from ${weatherReferenceYear}`;
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
  markerLabel,
}: {
  position: MapPosition | null;
  setPosition: (value: MapPosition) => void;
  setAddress: (value: string | null) => void;
  clearShapes: () => void;
  isDrawingRef: MutableRefObject<boolean>;
  setSelectedLocationId: (value: string) => void;
  markerLabel: string;
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
      <Popup>{markerLabel}</Popup>
    </Marker>
  );
}

export default function App() {
  const currentYear = new Date().getFullYear();
  const lastCompleteYear = currentYear - 1;

  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [language, setLanguage] = useState<Language>('en');
  const [selectedLocationId, setSelectedLocationId] = useState('');
  const [position, setPosition] = useState<MapPosition | null>(null);
  const [detectedAddress, setDetectedAddress] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const [forecastYear, setForecastYear] = useState<string | number>(currentYear);
  const [panelArea, setPanelArea] = useState<string | number>(APP_DEFAULTS.panelAreaSqm);
  const [acCapacityKw, setAcCapacityKw] = useState<string | number>(APP_DEFAULTS.acCapacityKw);
  const [modelType, setModelType] = useState<ModelType>(APP_DEFAULTS.modelType);
  const [trainingYears, setTrainingYears] = useState(APP_DEFAULTS.trainingYears);
  const [electricityPrice, setElectricityPrice] = useState<string | number>(APP_DEFAULTS.electricityPricePerKwh);
  const [currency, setCurrency] = useState<CurrencyCode>(APP_DEFAULTS.currency);
  const [systemCapex, setSystemCapex] = useState<string | number>(APP_DEFAULTS.systemCapex);

  const [panelEfficiency, setPanelEfficiency] = useState(APP_DEFAULTS.panelEfficiency);
  const [tilt, setTilt] = useState(APP_DEFAULTS.tiltDegrees);
  const [cleanliness, setCleanliness] = useState<CleanlinessLevel>(APP_DEFAULTS.cleanliness);
  const [shading, setShading] = useState<ShadingLevel>(APP_DEFAULTS.shading);
  const [gamma, setGamma] = useState<string | number>(APP_DEFAULTS.gamma);
  const [noct, setNoct] = useState<string | number>(APP_DEFAULTS.noctC);
  const [benchmarkYears, setBenchmarkYears] = useState(APP_DEFAULTS.benchmarkYears);

  const [forecastData, setForecastData] = useState<YearlyForecastResponse | null>(null);
  const [dailySimulation, setDailySimulation] = useState<SimulationResponse | null>(null);
  const [accuracyResult, setAccuracyResult] = useState<AccuracyEvaluationResponse | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkEvaluationResponse | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ScenarioComparisonResponse | null>(null);
  const [scenarioRequests, setScenarioRequests] = useState<ScenarioRequest[]>([]);

  const [scenarioName, setScenarioName] = useState(`${APP_DEFAULTS.scenarioNamePrefix} 1`);
  const [scenarioPanelAreaDelta, setScenarioPanelAreaDelta] = useState(APP_DEFAULTS.scenarioPanelAreaDeltaPercent);
  const [scenarioTilt, setScenarioTilt] = useState(APP_DEFAULTS.tiltDegrees);
  const [scenarioAcCapacity, setScenarioAcCapacity] = useState<string | number>(APP_DEFAULTS.acCapacityKw);
  const [scenarioCapex, setScenarioCapex] = useState<string | number>(APP_DEFAULTS.systemCapex);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isSidebarResizing, setIsSidebarResizing] = useState(false);

  const featureGroupRef = useRef<L.FeatureGroup | null>(null);
  const isDrawingRef = useRef(false);
  const sidebarResizeStateRef = useRef<{ startX: number; startWidth: number } | null>(null);
  const text = UI_COPY[language];
  const isHebrew = language === 'he';

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
  }, [language]);

  useEffect(() => {
    setSystemCapex((currentValue) => (
      Number(currentValue) === LEGACY_SYSTEM_CAPEX_DEFAULT
        ? APP_DEFAULTS.systemCapex
        : currentValue
    ));
    setScenarioCapex((currentValue) => (
      Number(currentValue) === LEGACY_SYSTEM_CAPEX_DEFAULT
        ? APP_DEFAULTS.systemCapex
        : currentValue
    ));
  }, []);

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
    setScenarioName(`${APP_DEFAULTS.scenarioNamePrefix} ${scenarioRequests.length + 2}`);
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
        row[text.historicalReference] = actualReference?.actual_yearly_kwh ?? 0;
        benchmarkResult.approaches.forEach((approach) => {
          const displayLabel = getBenchmarkApproachLabel(approach.approach, approach.label, language);
          row[displayLabel] = approach.yearly_results.find((result) => result.year === year)?.predicted_yearly_kwh ?? 0;
        });
        return row;
      })
    : [];

  const benchmarkMetricChartData = benchmarkResult
    ? benchmarkResult.approaches.map((approach) => ({
        approach: getBenchmarkApproachLabel(approach.approach, approach.label, language),
        [text.avgMonthlyError]: approach.metrics.monthly_mae_kwh,
        [text.avgYearlyError]: approach.metrics.yearly_mae_kwh,
        [text.averageBias]: approach.metrics.bias_kwh,
      }))
    : [];

  const benchmarkSummaryRows: BenchmarkSummaryRow[] = benchmarkResult
    ? benchmarkResult.approaches.map((approach) => ({
        id: approach.approach,
        label: getBenchmarkApproachLabel(approach.approach, approach.label, language),
        monthlyMape: approach.metrics.monthly_mape_percent,
        monthlyMaeKwh: approach.metrics.monthly_mae_kwh,
        yearlyMape: approach.metrics.yearly_mape_percent,
        yearlyMaeKwh: approach.metrics.yearly_mae_kwh,
        biasPercent: approach.metrics.bias_percent,
        biasKwh: approach.metrics.bias_kwh,
        absBiasPercent: Math.abs(approach.metrics.bias_percent),
        fallbackCount: approach.fallback_years.length,
        fallbackSummary: formatFallbackSummary(approach.fallback_years),
        biasDirection: describeBiasDirection(approach.metrics.bias_percent, language),
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
  const benchmarkTrainingWindowLabel = isHebrew
    ? `משתמש ב-${benchmarkResult?.training_window_years ?? trainingYears} שנות למידה`
    : `Using ${benchmarkResult?.training_window_years ?? trainingYears} past years for learning`;
  const accuracyForecastKey = isHebrew ? 'תחזית' : 'Forecast';
  const accuracyActualKey = isHebrew ? 'בפועל' : 'Actual';
  const accuracyErrorKey = isHebrew ? 'שגיאת תחזית (kWh)' : 'Forecast error (kWh)';
  const accuracyMonthlyEnergyChartData = accuracyResult
    ? MONTH_NAMES.map((month, index) => ({
        name: month,
        [accuracyForecastKey]: accuracyResult.predicted_monthly_kwh[index] ?? 0,
        [accuracyActualKey]: accuracyResult.actual_monthly_kwh[index] ?? 0,
      }))
    : [];
  const accuracyMonthlyErrorChartData = accuracyResult
    ? MONTH_NAMES.map((month, index) => ({
        name: month,
        [accuracyErrorKey]: Number(
          ((accuracyResult.predicted_monthly_kwh[index] ?? 0) - (accuracyResult.actual_monthly_kwh[index] ?? 0)).toFixed(1),
        ),
      }))
    : [];
  const accuracyTakeaway = accuracyResult
    ? buildAccuracyTakeaway(accuracyResult.quality, accuracyResult.bias_percent, language)
    : null;
  const accuracyQualityDescription = accuracyResult ? getAccuracyQualityDescription(accuracyResult.quality, language) : '';
  const accuracyQualityClassName = accuracyResult ? getAccuracyQualityClassName(accuracyResult.quality) : 'text-foreground';
  const accuracyBiasDirection = accuracyResult ? describeBiasDirection(accuracyResult.bias_percent, language) : describeBiasDirection(0, language);
  const selectedForecastApproachLabel = getForecastApproachLabel(modelType, language);
  const accuracyMethodLabel = accuracyResult
    ? getForecastApproachLabel(accuracyResult.model_type_used, language)
    : selectedForecastApproachLabel;
  const accuracyWeatherBasisLabel = accuracyResult
    ? formatWeatherReferenceLabel(accuracyResult.weather_reference_year, language)
    : isHebrew ? 'לא זמין' : 'Not available';
  const accuracyTrainingYearsLabel = accuracyResult
    ? formatLearningYearsUsed(accuracyResult.training_years_used, language)
    : isHebrew ? 'לא זמין' : 'Not available';
  const accuracyComparisonRows = accuracyResult
    ? [
        {
          metric: text.yearlyEnergy,
          actual: `${formatSidebarNumber(accuracyResult.actual_yearly_kwh)} kWh`,
          forecast: `${formatSidebarNumber(accuracyResult.predicted_yearly_kwh)} kWh`,
          difference: `${formatSignedNumber(accuracyResult.bias_kwh)} kWh (${formatSignedNumber(accuracyResult.bias_percent, 2)}%)`,
        },
        {
          metric: text.annualSavings,
          actual: `${formatSidebarNumber(accuracyResult.actual_annual_savings)} ${accuracyResult.financial_assumptions.currency}`,
          forecast: `${formatSidebarNumber(accuracyResult.predicted_annual_savings)} ${accuracyResult.financial_assumptions.currency}`,
          difference: `${formatSignedNumber(
            accuracyResult.predicted_annual_savings - accuracyResult.actual_annual_savings,
          )} ${accuracyResult.financial_assumptions.currency}`,
        },
        {
          metric: text.simplePayback,
          actual: formatPaybackYears(accuracyResult.actual_simple_payback_years, language),
          forecast: formatPaybackYears(accuracyResult.predicted_simple_payback_years, language),
          difference: formatPaybackDelta(
            accuracyResult.actual_simple_payback_years,
            accuracyResult.predicted_simple_payback_years,
            language,
          ),
        },
      ]
    : [];
  const currentBasePayload = buildPayload();
  const comparisonRequestedModelLabel = selectedForecastApproachLabel;
  const comparisonModelLabel = comparisonResult
    ? getForecastApproachLabel(comparisonResult.model_type_used, language)
    : comparisonRequestedModelLabel;
  const comparisonWeatherBasisLabel = comparisonResult
    ? formatWeatherReferenceLabel(comparisonResult.weather_reference_year, language)
    : forecastData
      ? formatWeatherReferenceLabel(forecastData.weather_reference_year, language)
      : isHebrew ? 'יוגדר בהרצת ההשוואה' : 'Resolved when you run comparison';
  const comparisonSharedContextRows = [
    { label: text.forecastYear, value: String(currentBasePayload.year) },
    { label: text.approach, value: comparisonModelLabel },
    { label: text.weatherReference, value: comparisonWeatherBasisLabel },
    { label: text.tariff, value: `${formatSidebarNumber(currentBasePayload.electricity_price_per_kwh, 2)} ${currency}/kWh` },
    {
      label: isHebrew ? 'מערכת בסיס' : 'Base system reference',
      value:
        `${formatSidebarNumber(currentBasePayload.panel_area)} m² · ` +
        `${formatSidebarNumber(currentBasePayload.tilt)}° · ` +
        `${formatSidebarNumber(currentBasePayload.ac_capacity_kw)} kW · ` +
        `${formatCurrencyAmount(currentBasePayload.system_capex, currency, 0)}`,
    },
    {
      label: isHebrew ? 'הגדרות בירושה' : 'Inherited settings',
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
    recommendedScenarioSelection.mode === 'payback'
      ? isHebrew ? 'אפשרות מומלצת' : 'Recommended Option'
      : isHebrew ? 'אפשרות החיסכון הטובה ביותר' : 'Best Savings Option';
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
        ? isHebrew
          ? 'מערכת הבסיס עדיין נותנת את החזר ההשקעה הקצר ביותר.'
          : 'Base System still offers the shortest simple payback under the shared forecast assumptions.'
        : isHebrew
          ? `${recommendedScenario.label} נותנת את החזר ההשקעה הקצר ביותר.`
          : `${recommendedScenario.label} offers the shortest simple payback under the shared forecast assumptions.`
      : recommendedScenario.isBaseline
        ? isHebrew
          ? 'לאף אפשרות אין החזר כדאי, ומערכת הבסיס עדיין נותנת את החיסכון השנתי הגבוה ביותר.'
          : 'No option has a viable simple payback, and Base System still produces the highest annual savings.'
        : isHebrew
          ? 'לאף אפשרות אין החזר כדאי, לכן ההמלצה עוברת לחיסכון השנתי הגבוה ביותר.'
          : `No option has a viable simple payback, so the recommendation falls back to the highest annual savings.`
    : isHebrew ? 'הרץ השוואת אפשרויות כדי לקבל המלצה.' : 'Run the option comparison to generate a recommendation.';
  const comparisonRecommendationDetail = recommendedScenario
    ? recommendedScenario.isBaseline
      ? `${isHebrew ? 'מערכת הבסיס נשארת אפשרות הייחוס עם' : 'Base System remains the reference option with'} ${formatSidebarNumber(recommendedScenario.yearlyKwh)} kWh/${isHebrew ? 'שנה' : 'year'}, ${formatCurrencyAmount(
          recommendedScenario.annualSavings,
          recommendedScenario.currency,
        )} ${isHebrew ? 'חיסכון שנתי, והחזר' : 'in annual savings, and'} ${formatPaybackYears(recommendedScenario.simplePaybackYears, language)}${isHebrew ? '.' : ' simple payback.'}`
      : isHebrew
        ? `${recommendedScenario.label} משנה את האנרגיה השנתית ב-${formatSignedNumber(
            recommendedScenario.energyDeltaKwh,
          )} kWh, את החיסכון השנתי ב-${formatSignedCurrency(
            recommendedScenario.savingsDeltaValue,
            recommendedScenario.currency,
          )}, ו${
            recommendedScenario.paybackDeltaYears == null
              ? 'לא נותנת דלתא החזר ניתנת להשוואה'
              : `משנה את ההחזר ב-${formatSignedNumber(recommendedScenario.paybackDeltaYears, 1)} שנים`
          } מול מערכת הבסיס.`
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
    : isHebrew ? 'הוסף לפחות אפשרות אחת להשוואה מול מערכת הבסיס.' : 'Add at least one alternative option to compare against Base System.';
  const comparisonTechnicalRows = comparisonResult
    ? [
        {
          field: isHebrew ? 'שיטה מבוקשת' : 'Requested forecast approach',
          value: getForecastApproachLabel(comparisonResult.model_type_requested, language),
        },
        {
          field: isHebrew ? 'שיטה בפועל' : 'Forecast approach used',
          value: getForecastApproachLabel(comparisonResult.model_type_used, language),
        },
        {
          field: isHebrew ? 'ייחוס מזג אוויר' : 'Weather reference used',
          value: formatWeatherReferenceLabel(comparisonResult.weather_reference_year, language),
        },
        {
          field: text.learningYears,
          value: formatLearningYearsUsed(comparisonResult.training_years_used, language),
        },
        {
          field: isHebrew ? 'הערת גיבוי' : 'Backup forecast note',
          value: comparisonResult.fallback_reason || (isHebrew ? 'לא הופעלה שיטת גיבוי' : 'No backup forecast method used'),
        },
        { field: text.dataSource, value: comparisonResult.data_source },
      ]
    : [];
  const locationSummary = position
    ? detectedAddress || `${position.lat.toFixed(4)}, ${position.lng.toFixed(4)}`
    : isHebrew ? 'בחר עיר, חפש כתובת או לחץ על המפה.' : 'Choose a city, search an address, or click the map.';
  const systemSummary =
    `${formatSidebarNumber(panelArea)} m² · ` +
    `${formatSidebarNumber(acCapacityKw)} kW · ` +
    `${getForecastApproachShortLabel(modelType, language)}`;
  const financialSummary = `${formatSidebarNumber(electricityPrice, 2)} ${currency}/kWh · CAPEX ${formatSidebarNumber(systemCapex)} ${currency}`;
  const overviewSummaryText = forecastData
    ? `${formatReadableKwh(
        forecastData.yearly_kwh,
      )}/year · ${formatReadableCurrency(
        forecastData.annual_savings,
        forecastData.financial_assumptions.currency,
      )}/year · ${
        forecastData.simple_payback_years == null
          ? isHebrew ? 'אין החזר כדאי' : 'No viable payback'
          : isHebrew
            ? `החזר תוך ${formatReadableNumber(forecastData.simple_payback_years, 1)} שנים`
            : `${formatReadableNumber(forecastData.simple_payback_years, 1)} year payback`
      }`
    : '';
  const overviewContextRows = forecastData
    ? [
        { label: text.forecastYear, value: String(forecastData.forecast_year) },
        { label: text.methodApproach, value: getForecastApproachLabel(forecastData.model_type_used, language) },
        { label: text.weatherReference, value: formatWeatherReferenceLabel(forecastData.weather_reference_year, language) },
        {
          label: text.tariff,
          value: `${formatReadableNumber(forecastData.financial_assumptions.electricity_price_per_kwh, 2)} ${forecastData.financial_assumptions.currency}/kWh`,
        },
        {
          label: text.capex,
          value: formatReadableCurrency(forecastData.financial_assumptions.system_capex, forecastData.financial_assumptions.currency),
        },
        ...(forecastData.training_years_used.length > 0
          ? [
              {
                label: text.learningYears,
                value: formatLearningYearsUsed(forecastData.training_years_used, language),
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
        { field: isHebrew ? 'שיטה מבוקשת' : 'Requested forecast approach', value: getForecastApproachLabel(forecastData.model_type_requested, language) },
        { field: isHebrew ? 'שיטה בפועל' : 'Forecast approach used', value: getForecastApproachLabel(forecastData.model_type_used, language) },
        { field: text.weatherReference, value: formatWeatherReferenceLabel(forecastData.weather_reference_year, language) },
        { field: text.dataSource, value: forecastData.data_source },
        { field: isHebrew ? 'בסיס הערכה' : 'Valuation basis', value: forecastData.financial_assumptions.valuation_basis },
        { field: isHebrew ? 'בסיס חיסכון שנתי' : 'Annual savings basis', value: forecastData.financial_assumptions.annual_savings_basis },
        { field: isHebrew ? 'בסיס החזר' : 'Payback basis', value: forecastData.financial_assumptions.payback_basis },
        ...(forecastData.training_years_used.length > 0
          ? [
              {
                field: text.learningYears,
                value: formatLearningYearsUsed(forecastData.training_years_used, language),
              },
            ]
          : []),
      ]
    : [];
  const dailySimulationDateLabel = dailySimulation
    ? formatSimulationDateLabel(dailySimulation.hourly_time[0] ?? '')
    : isHebrew ? 'לא זמין' : 'Not available';
  const dailyPeakPower = dailySimulation && dailySimulation.hourly_ac_kw.length > 0 ? Math.max(...dailySimulation.hourly_ac_kw) : null;
  const dailyPeakIndex =
    dailySimulation && dailyPeakPower != null
      ? dailySimulation.hourly_ac_kw.findIndex((power) => power === dailyPeakPower)
      : -1;
  const dailyPeakHourLabel =
    dailySimulation && dailyPeakIndex >= 0
      ? formatHourlyLabel(dailySimulation.hourly_time[dailyPeakIndex], dailyPeakIndex)
      : isHebrew ? 'לא זמין' : 'Not available';
  const dailyLossPercent = dailySimulation ? Math.max(0, (1 - dailySimulation.system_loss_factor) * 100) : null;
  const dailySummaryText = dailySimulation
    ? `${dailySimulationDateLabel} · ${formatReadableKwh(
        dailySimulation.daily_kwh,
        1,
      )} · ${formatReadableCurrency(
        dailySimulation.estimated_daily_value,
        dailySimulation.financial_assumptions.currency,
        2,
      )} · peak ${dailyPeakHourLabel} at ${formatReadableNumber(dailyPeakPower, 2)} kW`
    : '';
  const dailyHourlyChartData = dailySimulation
    ? dailySimulation.hourly_ac_kw.map((power, index) => ({
        time: formatHourlyLabel(dailySimulation.hourly_time[index], index),
        power,
      }))
    : [];
  const dailyTechnicalRows = dailySimulation
    ? [
        { field: isHebrew ? 'יום מדומה' : 'Simulated day', value: dailySimulationDateLabel },
        { field: isHebrew ? 'מקדם איבוד גולמי' : 'Raw system loss factor', value: formatReadableNumber(dailySimulation.system_loss_factor, 3) },
        {
          field: isHebrew ? 'קואורדינטות מיקום' : 'Location coordinates',
          value: `${formatReadableNumber(dailySimulation.location[0], 4)}, ${formatReadableNumber(dailySimulation.location[1], 4)}`,
        },
        { field: isHebrew ? 'אזור זמן' : 'Timezone', value: dailySimulation.timezone },
        { field: text.dataSource, value: dailySimulation.data_source },
        { field: isHebrew ? 'בסיס הערכה' : 'Valuation basis', value: dailySimulation.financial_assumptions.valuation_basis },
      ]
    : [];
  const sidebarStyle = {
    '--sidebar-width': `${sidebarCollapsed ? COLLAPSED_SIDEBAR_WIDTH : sidebarWidth}px`,
  } as CSSProperties;

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground" dir={isHebrew ? 'rtl' : 'ltr'}>
      <header className="border-b bg-card">
        <div className="flex w-full items-start justify-between gap-6 px-6 py-6 md:px-8 md:py-8">
          <div className="min-w-0 flex-1">
            <h1 className="flex items-center gap-3 text-3xl font-black tracking-tight sm:text-4xl lg:text-5xl">
              <Sun className="h-8 w-8 shrink-0 text-yellow-500 sm:h-10 sm:w-10 lg:h-12 lg:w-12" />
              <span>{text.appTitle}</span>
            </h1>
            <p className="mt-3 max-w-4xl text-sm text-muted-foreground sm:text-base">
              {text.appSubtitle}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button variant="outline" onClick={() => setLanguage(isHebrew ? 'en' : 'he')}>
              {text.languageButton}
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              aria-label={text.themeToggle}
              title={text.themeToggle}
            >
              {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </Button>
          </div>
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
                aria-label={text.expandSidebar}
                title={text.expandSidebar}
              >
                <PanelLeftOpen className="h-4 w-4" />
              </Button>
              <div className="min-w-0 md:pt-2 md:[writing-mode:vertical-rl]">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{text.controls}</p>
              </div>
            </div>
          ) : (
            <div className="flex h-full min-h-0 w-full flex-col gap-4 overflow-y-auto p-4">
              <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-background/70 px-3 py-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold">{text.controls}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarCollapsed(true)}
                  aria-label={text.minimizeSidebar}
                  title={text.minimizeSidebar}
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
                        <p className="text-sm font-semibold">{text.location}</p>
                        <p className="mt-1 max-w-full break-words text-xs text-muted-foreground [overflow-wrap:anywhere]">
                          {locationSummary}
                        </p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pb-3">
                    <div className="space-y-2">
                      <Label>{text.city}</Label>
                      <Select
                        value={selectedLocationId}
                        onValueChange={(value) => {
                          setSelectedLocationId(value);
                          if (value !== 'custom') {
                            const selected = PREDEFINED_LOCATIONS.find((location) => location.id === value);
                            if (selected) {
                              setPosition({ lat: selected.lat, lng: selected.lng });
                              setDetectedAddress(isHebrew ? selected.labelHe : selected.label);
                              clearShapes();
                            }
                          }
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={text.chooseCity} />
                        </SelectTrigger>
                        <SelectContent>
                          {PREDEFINED_LOCATIONS.map((location) => (
                            <SelectItem key={location.id} value={location.id}>
                              {isHebrew ? location.labelHe : location.label}
                            </SelectItem>
                          ))}
                          <SelectItem value="custom">{text.customMapPoint}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="rounded-xl border border-dashed border-border/70 bg-muted/25 p-3">
                      <div className="flex items-center gap-2">
                        <Label>{text.address}</Label>
                        <HelpTip>{text.addressHelp}</HelpTip>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <Input
                          placeholder={text.addressPlaceholder}
                          value={searchQuery}
                          onChange={(event) => setSearchQuery(event.target.value)}
                          onKeyDown={(event) => event.key === 'Enter' && handleSearchLocation()}
                        />
                        <Button variant="secondary" onClick={handleSearchLocation} disabled={isSearching}>
                          {isSearching ? '...' : text.find}
                        </Button>
                      </div>
                    </div>

                    <div>
                      <Label className="text-muted-foreground">{text.selectedAddress}</Label>
                      {detectedAddress ? (
                        <Alert className="mt-2 border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/20">
                          <AlertDescription className="max-h-24 overflow-y-auto break-words text-sm [overflow-wrap:anywhere]">
                            {detectedAddress}
                          </AlertDescription>
                        </Alert>
                      ) : (
                        <p className="mt-2 text-sm text-muted-foreground">{text.noAddress}</p>
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
                        <p className="text-sm font-semibold">{text.systemParameters}</p>
                        <p className="mt-1 truncate text-xs text-muted-foreground">{systemSummary}</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pb-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>{text.forecastYear}</Label>
                        <HelpTip>{text.forecastYearHelp}</HelpTip>
                      </div>
                      <Input type="number" value={forecastYear} onChange={(event) => setForecastYear(event.target.value)} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>{text.panelArea}</Label>
                        <HelpTip>{text.panelAreaHelp}</HelpTip>
                      </div>
                      <Input type="number" value={panelArea} onChange={(event) => setPanelArea(event.target.value)} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>{text.acCapacity}</Label>
                        <HelpTip>{text.acCapacityHelp}</HelpTip>
                      </div>
                      <Input type="number" value={acCapacityKw} onChange={(event) => setAcCapacityKw(event.target.value)} />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>{text.approach}</Label>
                        <HelpTip>{text.approachHelp}</HelpTip>
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
                                  <span className="font-medium">{getForecastApproachShortLabel(approach, language)}</span>
                                </div>
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
                            <div className="flex items-center gap-2">
                              <Label>{text.learningYears}</Label>
                              <HelpTip>{text.learningYearsHelp}</HelpTip>
                            </div>
                          </div>
                          <span className="text-sm text-muted-foreground">{trainingYears}</span>
                        </div>
                        <Slider
                          min={1}
                          max={10}
                          step={1}
                          value={getSliderValue(trainingYears, APP_DEFAULTS.trainingYears)}
                          onValueChange={handleTrainingYearsChange}
                        />
                      </div>
                    ) : null}

                    <Accordion type="single" collapsible className="rounded-xl border border-border/70 bg-muted/15 px-3">
                      <AccordionItem value="advanced-system" className="border-none">
                        <AccordionTrigger className="py-3 hover:no-underline">
                          <div className="min-w-0">
                            <p className="text-sm font-medium">{text.advanced}</p>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="space-y-4 pb-3">
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <div className="flex items-center gap-2">
                                <Label>{text.panelEfficiency}</Label>
                                <HelpTip>{text.panelEfficiencyHelp}</HelpTip>
                              </div>
                              <span className="text-sm text-muted-foreground">{panelEfficiency.toFixed(2)}</span>
                            </div>
                            <Slider min={0.1} max={0.3} step={0.01} value={getSliderValue(panelEfficiency, APP_DEFAULTS.panelEfficiency)} onValueChange={handlePanelEfficiencyChange} />
                          </div>

                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <div className="flex items-center gap-2">
                                <Label>{text.tilt}</Label>
                                <HelpTip>{text.tiltHelp}</HelpTip>
                              </div>
                              <span className="text-sm text-muted-foreground">{tilt}</span>
                            </div>
                            <Slider min={0} max={60} step={1} value={getSliderValue(tilt, APP_DEFAULTS.tiltDegrees)} onValueChange={handleTiltChange} />
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Label>{text.cleanliness}</Label>
                              <HelpTip>{text.cleanlinessHelp}</HelpTip>
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
                              <Label>{text.shading}</Label>
                              <HelpTip>{text.shadingHelp}</HelpTip>
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
                              <Label>{text.temperatureCoefficient}</Label>
                              <HelpTip>{text.temperatureCoefficientHelp}</HelpTip>
                            </div>
                            <Input type="number" step="0.0001" value={gamma} onChange={(event) => setGamma(event.target.value)} />
                          </div>

                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Label>{text.noct}</Label>
                              <HelpTip>{text.noctHelp}</HelpTip>
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
                        <p className="text-sm font-semibold">{text.financial}</p>
                        <p className="mt-1 truncate text-xs text-muted-foreground">{financialSummary}</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="space-y-4 pb-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Label>{text.tariff}</Label>
                        <HelpTip>{text.tariffHelp}</HelpTip>
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
                        <Label>{text.currency}</Label>
                        <HelpTip>{text.currencyHelp}</HelpTip>
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
                        <Label>{text.capex}</Label>
                        <HelpTip>{text.capexHelp}</HelpTip>
                      </div>
                      <Input type="number" step="100" value={systemCapex} onChange={(event) => setSystemCapex(event.target.value)} />
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              <Button className="w-full" size="lg" onClick={handleRunForecast} disabled={!position || isLoading}>
                {isLoading ? text.running : text.runForecast}
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
              aria-label={text.resizeSidebar}
              title={text.resizeSidebar}
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
              <AlertTitle>{isHebrew ? 'בעיה בבקשת שרת' : 'Backend request issue'}</AlertTitle>
              <AlertDescription>{apiError}</AlertDescription>
            </Alert>
          )}

          {!position ? (
            <Alert className="mb-6">
              <AlertTitle>{text.chooseLocation}</AlertTitle>
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
                  markerLabel={isHebrew ? 'מיקום נבחר' : 'Selected Location'}
                />
              </MapContainer>
            </div>
          )}

          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="mb-4 flex h-auto flex-wrap">
              <TabsTrigger value="overview">{text.tabOverview}</TabsTrigger>
              <TabsTrigger value="daily">{text.tabDay}</TabsTrigger>
              <TabsTrigger value="accuracy">{text.tabAccuracy}</TabsTrigger>
              <TabsTrigger value="benchmark">{text.tabMethods}</TabsTrigger>
              <TabsTrigger value="scenarios">{text.tabOptions}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {!forecastData ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  {text.emptyOverview}
                </div>
              ) : (
                <>
                  {forecastData.fallback_reason && (
                    <Alert>
                      <AlertTitle>{isHebrew ? 'הופעלה שיטת גיבוי' : 'Backup forecast approach used'}</AlertTitle>
                      <AlertDescription>{forecastData.fallback_reason}</AlertDescription>
                    </Alert>
                  )}

                  <Card className="border-primary/25 bg-primary/5">
                    <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <CardTitle className="flex items-center gap-2">
                          {text.summary}
                          <HelpTip>{text.summaryHelp}</HelpTip>
                        </CardTitle>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="secondary">{isHebrew ? 'שנה' : 'Year'} {forecastData.forecast_year}</Badge>
                          <Badge variant="outline">{getForecastApproachLabel(forecastData.model_type_used, language)}</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-lg leading-7 text-foreground">{overviewSummaryText}</p>
                    </CardContent>
                  </Card>

                  <div className="space-y-3">
                    <h3 className="text-lg font-semibold">{text.keyResults}</h3>
                    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-muted-foreground">{text.yearlyEnergy}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatReadableKwh(forecastData.yearly_kwh)}</div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-muted-foreground">{text.annualSavings}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">
                            {formatReadableCurrency(forecastData.annual_savings, forecastData.financial_assumptions.currency)}
                          </div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium text-muted-foreground">{text.simplePayback}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatPaybackYears(forecastData.simple_payback_years, language)}</div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          {text.context}
                          <HelpTip>{text.contextHelp}</HelpTip>
                        </CardTitle>
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
                        <CardTitle className="flex items-center gap-2">
                          {text.performance}
                          <HelpTip>{text.performanceHelp}</HelpTip>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-3">
                        <div className="rounded-lg border bg-background/70 p-3">
                          <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.specificYield}</p>
                          <p className="mt-1 text-lg font-semibold">{formatReadableNumber(forecastData.specific_yield_kwh_per_kwp, 1)} kWh/kWp</p>
                        </div>
                        <div className="rounded-lg border bg-background/70 p-3">
                          <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.averageDailyEnergy}</p>
                          <p className="mt-1 text-lg font-semibold">{formatReadableKwh(forecastData.avg_daily_kwh, 1)}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle>{text.monthlyEnergyForecast}</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={overviewMonthlyEnergyChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip formatter={(value) => [formatReadableKwh(Number(value)), isHebrew ? 'אנרגיה' : 'Energy']} />
                            <Bar dataKey="value" fill="#eab308" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          {text.monthlyValue}
                          <HelpTip>{text.monthlyValueHelp}</HelpTip>
                        </CardTitle>
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
                                isHebrew ? 'ערך משוער' : 'Estimated value',
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
                      <CardTitle className="flex items-center gap-2">
                        {text.seasonalSplit}
                        <HelpTip>{text.seasonalSplitHelp}</HelpTip>
                      </CardTitle>
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
                                  <p className="text-muted-foreground">
                                    {formatReadableNumber(row.sharePercent, 1)}% {isHebrew ? 'מהייצור השנתי' : 'of yearly production'}
                                  </p>
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
                          <p className="flex items-center gap-2 font-semibold">
                            {text.details}
                            <HelpTip>{text.overviewDetailsHelp}</HelpTip>
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{isHebrew ? 'שדה' : 'Field'}</TableHead>
                              <TableHead>{isHebrew ? 'ערך' : 'Value'}</TableHead>
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
                  {text.dayEmpty}
                </div>
              ) : (
                <>
                  <Card className="border-primary/25 bg-primary/5">
                    <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <CardTitle className="flex items-center gap-2">
                          {text.daySummary}
                          <HelpTip>{text.daySummaryHelp}</HelpTip>
                        </CardTitle>
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
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.dailyEnergy}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatReadableKwh(dailySimulation.daily_kwh, 1)}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.dailyValue}</CardTitle>
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
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.peakPower}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatReadableNumber(dailyPeakPower, 2)} kW</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.peakHour}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{dailyPeakHourLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.systemLosses}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatReadableNumber(dailyLossPercent, 1)}%</div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        {text.hourlyPower}
                        <HelpTip>{text.hourlyPowerHelp}</HelpTip>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[400px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={dailyHourlyChartData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="time" />
                          <YAxis />
                          <Tooltip formatter={(value) => [`${formatReadableNumber(Number(value), 2)} kW`, isHebrew ? 'הספק AC' : 'AC Power']} />
                          {dailyPeakIndex >= 0 ? (
                            <ReferenceLine
                              x={dailyPeakHourLabel}
                              stroke="#f59e0b"
                              strokeDasharray="4 4"
                              label={{ value: text.peakHour, position: 'top', fill: '#a16207', fontSize: 12 }}
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
                          <p className="flex items-center gap-2 font-semibold">
                            {text.details}
                            <HelpTip>{text.dayDetailsHelp}</HelpTip>
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{isHebrew ? 'שדה' : 'Field'}</TableHead>
                              <TableHead>{isHebrew ? 'ערך' : 'Value'}</TableHead>
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
                    <h3 className="flex items-center gap-2 font-medium">
                      {text.accuracyTitle}
                      <HelpTip>{text.accuracyTitleHelp}</HelpTip>
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">{isHebrew ? 'שנה' : 'Year'} {evaluationYear}</Badge>
                    <Badge variant="outline">{selectedForecastApproachLabel}</Badge>
                  </div>
                </div>
                <Button onClick={handleRunAccuracy} disabled={!position || isLoading}>
                  {isLoading ? text.running : text.runAccuracy}
                </Button>
              </div>

              {selectedForecastYear > lastCompleteYear && (
                <Alert>
                  <AlertTitle>{isHebrew ? 'משתמשים בשנת הארכיון המלאה האחרונה' : 'Using last complete archive year'}</AlertTitle>
                  <AlertDescription>
                    {isHebrew
                      ? `בחרת ${selectedForecastYear}, אבל הארכיון מלא רק עד ${lastCompleteYear}, לכן הבדיקה תרוץ מול ${evaluationYear}.`
                      : `You selected ${selectedForecastYear}, but archived actual weather is currently complete only through ${lastCompleteYear}, so this check runs against ${evaluationYear}.`}
                  </AlertDescription>
                </Alert>
              )}

              {!accuracyResult ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  {text.accuracyEmpty}
                </div>
              ) : (
                <>
                  {accuracyResult.fallback_reason && (
                    <Alert>
                      <AlertTitle>{isHebrew ? 'הופעלה שיטת גיבוי' : 'Backup method used'}</AlertTitle>
                      <AlertDescription>{accuracyResult.fallback_reason}</AlertDescription>
                    </Alert>
                  )}

                  <div className="grid gap-4">
                    <Card className="border-primary/25 bg-primary/5">
                      <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-2">
                          <CardTitle className="flex items-center gap-2">
                            {text.takeaway}
                            <HelpTip>{text.takeawayHelp}</HelpTip>
                          </CardTitle>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary">{isHebrew ? 'שנת בדיקה' : 'Checked year'} {accuracyResult.year}</Badge>
                            <Badge variant="outline">{accuracyMethodLabel}</Badge>
                          </div>
                        </div>
                        <div className="space-y-1 md:text-right">
                          <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.accuracyRating}</p>
                          <p className={`text-2xl font-semibold ${accuracyQualityClassName}`}>{accuracyResult.quality}</p>
                          <HelpTip>{accuracyQualityDescription}</HelpTip>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <p className="text-3xl font-semibold tracking-tight">{accuracyTakeaway?.headline}</p>
                          <p className="mt-2 text-sm text-muted-foreground">{accuracyBiasDirection}</p>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-3">
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.avgMonthlyMiss}</p>
                            <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(accuracyResult.monthly_mae_kwh)} kWh</p>
                            <p className="text-xs text-muted-foreground">{formatSidebarNumber(accuracyResult.mape_percent, 2)}% monthly error</p>
                          </div>
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.yearlyMiss}</p>
                            <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(accuracyResult.yearly_mae_kwh)} kWh</p>
                            <p className="text-xs text-muted-foreground">{formatSidebarNumber(accuracyResult.yearly_mape_percent, 2)}% yearly error</p>
                          </div>
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.bias}</p>
                            <p className="mt-1 text-lg font-semibold">{formatSignedNumber(accuracyResult.bias_kwh)} kWh</p>
                            <p className="text-xs text-muted-foreground">
                              {formatSignedNumber(accuracyResult.bias_percent, 2)}% · {accuracyBiasDirection}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          {text.actualVsForecast}
                          <HelpTip>{text.actualVsForecastHelp}</HelpTip>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{isHebrew ? 'מדד' : 'Metric'}</TableHead>
                              <TableHead>{isHebrew ? 'בפועל' : 'Archived Actual'}</TableHead>
                              <TableHead>{isHebrew ? 'תחזית' : 'Forecast'}</TableHead>
                              <TableHead>{isHebrew ? 'הפרש' : 'Difference'}</TableHead>
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
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.methodApproach}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyMethodLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.weatherReference}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyWeatherBasisLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.learningYears}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyTrainingYearsLabel}</div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">{text.dataSource}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-semibold">{accuracyResult.data_source}</div>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle>{text.monthlyForecastVsActual}</CardTitle>
                      </CardHeader>
                      <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={accuracyMonthlyEnergyChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey={accuracyForecastKey} fill="#3b82f6" radius={[2, 2, 0, 0]} />
                            <Bar dataKey={accuracyActualKey} fill="#10b981" radius={[2, 2, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          {text.monthlyError}
                          <HelpTip>{text.monthlyErrorHelp}</HelpTip>
                        </CardTitle>
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
                            <Bar dataKey={accuracyErrorKey} fill="#f59e0b" radius={[2, 2, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                    <AccordionItem value="accuracy-details" className="border-none">
                      <AccordionTrigger className="py-4 text-left hover:no-underline">
                        <div>
                          <p className="flex items-center gap-2 font-semibold">
                            {text.details}
                            <HelpTip>{text.accuracyDetailsHelp}</HelpTip>
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{isHebrew ? 'שדה' : 'Field'}</TableHead>
                              <TableHead>{isHebrew ? 'ערך' : 'Value'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            <TableRow>
                              <TableCell>{isHebrew ? 'שיטה מבוקשת' : 'Requested forecast approach'}</TableCell>
                              <TableCell>{getForecastApproachLabel(accuracyResult.model_type_requested, language)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{isHebrew ? 'שיטה בפועל' : 'Forecast approach used'}</TableCell>
                              <TableCell>{accuracyMethodLabel}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{isHebrew ? 'כלל דירוג דיוק' : 'Accuracy rating rule'}</TableCell>
                              <TableCell>{accuracyQualityDescription}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{text.weatherReference}</TableCell>
                              <TableCell>{accuracyWeatherBasisLabel}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{text.learningYears}</TableCell>
                              <TableCell>{accuracyTrainingYearsLabel}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{isHebrew ? 'הערת גיבוי' : 'Backup method note'}</TableCell>
                              <TableCell>{accuracyResult.fallback_reason || (isHebrew ? 'לא הופעלה שיטת גיבוי' : 'No backup method used')}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{text.dataSource}</TableCell>
                              <TableCell>{accuracyResult.data_source}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{isHebrew ? 'בסיס הערכה' : 'Valuation basis'}</TableCell>
                              <TableCell>{accuracyResult.financial_assumptions.valuation_basis}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{isHebrew ? 'בסיס חיסכון שנתי' : 'Annual savings basis'}</TableCell>
                              <TableCell>{accuracyResult.financial_assumptions.annual_savings_basis}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>{isHebrew ? 'בסיס החזר' : 'Payback basis'}</TableCell>
                              <TableCell>{accuracyResult.financial_assumptions.payback_basis}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>

                        {accuracyResult.ml_metadata && (
                          <div>
                            <p className="mb-2 text-sm font-medium">{isHebrew ? 'אבחון תחזית מבוססת היסטוריה' : 'History-based forecast diagnostics'}</p>
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
                    <h3 className="flex items-center gap-2 font-medium">
                      {text.compareMethods}
                      <HelpTip>
                        {text.compareMethodsHelpPrefix} {evaluationYear}.
                      </HelpTip>
                    </h3>
                  </div>
                  <div className="w-full max-w-sm space-y-2">
                    <div className="flex justify-between">
                      <Label>{text.comparisonWindow}</Label>
                      <span className="text-sm text-muted-foreground">{benchmarkYears}</span>
                    </div>
                    <Slider min={1} max={5} step={1} value={getSliderValue(benchmarkYears, APP_DEFAULTS.benchmarkYears)} onValueChange={handleBenchmarkYearsChange} />
                  </div>
                </div>
                <Button onClick={handleRunBenchmark} disabled={!position || isLoading}>
                  {isLoading ? text.running : text.compareForecastMethods}
                </Button>
              </div>

              {!benchmarkResult ? (
                <div className="rounded-xl border bg-muted/20 p-12 text-center text-muted-foreground">
                  {text.methodsEmpty}
                </div>
              ) : (
                <>
                  <Alert>
                    <AlertTitle className="flex items-center gap-2">
                      {text.historicalReference}
                      <HelpTip>{benchmarkResult.reference_note}</HelpTip>
                    </AlertTitle>
                  </Alert>

                  <div className="grid gap-4">
                    <Card className="border-primary/25 bg-primary/5">
                      <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-2">
                          <CardTitle className="flex items-center gap-2">
                            {text.recommendedMethod}
                            <HelpTip>
                              {text.recommendedMethodHelp} {benchmarkWindowLabel}.
                            </HelpTip>
                          </CardTitle>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary">{isHebrew ? 'חלון' : 'Window'} {benchmarkWindowLabel}</Badge>
                            <Badge variant="outline">{benchmarkTrainingWindowLabel}</Badge>
                          </div>
                        </div>
                        {recommendedBenchmark ? <Badge className="w-fit">{text.bestOverall}</Badge> : null}
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <p className="text-3xl font-semibold tracking-tight">
                            {recommendedBenchmark?.label ?? (isHebrew ? 'אין המלצה עדיין' : 'No recommendation yet')}
                          </p>
                        </div>
                        {recommendedBenchmark ? (
                          <div className="grid gap-3 sm:grid-cols-3">
                            <div className="rounded-lg border bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.avgYearlyError}</p>
                              <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(recommendedBenchmark.yearlyMaeKwh)} kWh</p>
                              <p className="text-xs text-muted-foreground">{formatSidebarNumber(recommendedBenchmark.yearlyMape, 2)}% yearly error</p>
                            </div>
                            <div className="rounded-lg border bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.avgMonthlyError}</p>
                              <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(recommendedBenchmark.monthlyMaeKwh)} kWh</p>
                              <p className="text-xs text-muted-foreground">{formatSidebarNumber(recommendedBenchmark.monthlyMape, 2)}% monthly error</p>
                            </div>
                            <div className="rounded-lg border bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.averageBias}</p>
                              <p className="mt-1 text-lg font-semibold">{formatSignedNumber(recommendedBenchmark.biasKwh)} kWh</p>
                              <p className="text-xs text-muted-foreground">{recommendedBenchmark.biasDirection}</p>
                            </div>
                          </div>
                        ) : null}
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
                              <CardTitle className="flex items-center gap-2">
                                {getBenchmarkApproachLabel(approach.approach, approach.label, language)}
                                <HelpTip>{approach.description}</HelpTip>
                              </CardTitle>
                            </div>
                            {recommendedBenchmark?.id === approach.approach ? <Badge variant="secondary">{text.bestOverall}</Badge> : null}
                          </div>
                        </CardHeader>
                        <CardContent className="grid gap-3 sm:grid-cols-2">
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.avgYearlyError}</p>
                            <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(approach.metrics.yearly_mae_kwh)} kWh</p>
                          </div>
                          <div className="rounded-lg border bg-background/70 p-3">
                            <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.averageBias}</p>
                            <p className="mt-1 text-lg font-semibold">{formatSignedNumber(approach.metrics.bias_kwh)} kWh</p>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        {text.summary}
                        <HelpTip>{text.methodSummaryHelp}</HelpTip>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>{text.methodApproach}</TableHead>
                            <TableHead>{text.avgYearlyError}</TableHead>
                            <TableHead>{text.avgMonthlyError}</TableHead>
                            <TableHead>{isHebrew ? 'שגיאה שנתית (%)' : 'Yearly Error (%)'}</TableHead>
                            <TableHead>{text.bias}</TableHead>
                            <TableHead>{isHebrew ? 'שימוש בגיבוי' : 'Backup Logic Used'}</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {rankedBenchmarkSummaryRows.map((row) => (
                            <TableRow key={row.id}>
                              <TableCell>
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="font-medium">{row.label}</span>
                                  {recommendedBenchmark?.id === row.id ? <Badge variant="secondary">{text.bestOverall}</Badge> : null}
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
                        <CardTitle className="flex items-center gap-2">
                          {text.referenceVsForecasts}
                          <HelpTip>{text.referenceVsForecastsHelp}</HelpTip>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="h-[360px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={benchmarkEnergyChartData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="year" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line type="monotone" dataKey={text.historicalReference} stroke="#111827" strokeWidth={3} />
                            {benchmarkResult.approaches.map((approach, index) => (
                              <Line
                                key={approach.approach}
                                type="monotone"
                                dataKey={getBenchmarkApproachLabel(approach.approach, approach.label, language)}
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
                        <CardTitle className="flex items-center gap-2">
                          {text.errorComparison}
                          <HelpTip>{text.errorComparisonHelp}</HelpTip>
                        </CardTitle>
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
                            <Bar dataKey={text.avgMonthlyError} fill="#2563eb" />
                            <Bar dataKey={text.avgYearlyError} fill="#10b981" />
                            <Bar dataKey={text.averageBias} fill="#f59e0b" />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  </div>

                  <Accordion type="single" collapsible className="rounded-xl border bg-card px-4">
                    <AccordionItem value="year-details" className="border-none">
                      <AccordionTrigger className="py-4 text-left hover:no-underline">
                        <div>
                          <p className="flex items-center gap-2 font-semibold">
                            {text.yearDetails}
                            <HelpTip>{text.yearDetailsHelp}</HelpTip>
                          </p>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="pb-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{text.methodApproach}</TableHead>
                              <TableHead>{isHebrew ? 'שנה' : 'Year'}</TableHead>
                              <TableHead>{text.historicalReference}</TableHead>
                              <TableHead>{isHebrew ? 'הערכת תחזית' : 'Forecast Estimate'}</TableHead>
                              <TableHead>{isHebrew ? 'שגיאה מוחלטת' : 'Absolute Error'}</TableHead>
                              <TableHead>{isHebrew ? 'שגיאה שנתית (%)' : 'Yearly Error (%)'}</TableHead>
                              <TableHead>{text.bias} (kWh)</TableHead>
                              <TableHead>{isHebrew ? 'הערת גיבוי' : 'Backup Logic Note'}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {benchmarkResult.approaches.flatMap((approach) =>
                              approach.yearly_results.map((result) => (
                                <TableRow key={`${approach.approach}-${result.year}`}>
                                  <TableCell className="font-medium">{getBenchmarkApproachLabel(approach.approach, approach.label, language)}</TableCell>
                                  <TableCell>{result.year}</TableCell>
                                  <TableCell>{formatSidebarNumber(result.actual_yearly_kwh)} kWh</TableCell>
                                  <TableCell>{formatSidebarNumber(result.predicted_yearly_kwh)} kWh</TableCell>
                                  <TableCell>{formatSidebarNumber(result.yearly_mae_kwh)} kWh</TableCell>
                                  <TableCell>{formatSidebarNumber(result.yearly_mape_percent, 2)}%</TableCell>
                                  <TableCell>{formatSignedNumber(result.yearly_bias_kwh)} kWh</TableCell>
                                  <TableCell>{result.fallback_reason || (isHebrew ? 'לא הופעל גיבוי' : 'No backup logic used')}</TableCell>
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
                  {text.optionsEmpty}
                </div>
              ) : (
                <>
                  <div className="flex flex-col gap-4 rounded-lg border bg-muted/30 p-4 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div>
                        <h3 className="flex items-center gap-2 font-medium">
                          {text.compareOptions}
                          <HelpTip>{text.compareOptionsHelp}</HelpTip>
                        </h3>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="secondary">{text.baseIncluded}</Badge>
                        <Badge variant="outline">{comparisonRequestedModelLabel}</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          {text.sharedContext}
                          <HelpTip>{text.sharedContextHelp}</HelpTip>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>{isHebrew ? 'הגדרה משותפת' : 'Shared setting'}</TableHead>
                              <TableHead>{isHebrew ? 'ערך' : 'Value'}</TableHead>
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
                        <CardTitle className="flex items-center gap-2">
                          {text.optionInputs}
                          <HelpTip>{text.optionInputsHelp}</HelpTip>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <ul className="space-y-2 text-sm text-muted-foreground">
                          <li>{text.name}</li>
                          <li>{text.panelAreaChange}</li>
                          <li>{text.tilt}</li>
                          <li>{text.acCapacityShort}</li>
                          <li>{text.capex}</li>
                        </ul>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        {text.addOption}
                        <HelpTip>{text.addOptionHelp}</HelpTip>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-col items-end gap-4 md:flex-row">
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <Label>{text.optionName}</Label>
                          <Input value={scenarioName} onChange={(event) => setScenarioName(event.target.value)} />
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <div className="flex justify-between">
                            <Label>{text.panelAreaChange} (%)</Label>
                            <span className="text-sm text-muted-foreground">{getSliderNumber(scenarioPanelAreaDelta, APP_DEFAULTS.scenarioPanelAreaDeltaPercent)}%</span>
                          </div>
                          <div className="w-full px-2">
                            <Slider
                              min={-50}
                              max={200}
                              step={5}
                              value={getSliderValue(scenarioPanelAreaDelta, APP_DEFAULTS.scenarioPanelAreaDeltaPercent)}
                              onValueChange={handleScenarioPanelAreaDeltaChange}
                            />
                          </div>
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <div className="flex justify-between">
                            <Label>{text.optionTilt}</Label>
                            <span className="text-sm text-muted-foreground">{getSliderNumber(scenarioTilt, APP_DEFAULTS.tiltDegrees)}</span>
                          </div>
                          <div className="w-full px-2">
                            <Slider min={0} max={60} step={1} value={getSliderValue(scenarioTilt, APP_DEFAULTS.tiltDegrees)} onValueChange={handleScenarioTiltChange} />
                          </div>
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <Label>{text.acCapacity} </Label>
                          <Input
                            type="number"
                            value={scenarioAcCapacity}
                            onChange={(event) => setScenarioAcCapacity(event.target.value)}
                          />
                        </div>
                        <div className="min-w-[150px] flex-1 space-y-2">
                          <Label>{text.optionCapex}</Label>
                          <Input type="number" value={scenarioCapex} onChange={(event) => setScenarioCapex(event.target.value)} />
                        </div>
                        <Button onClick={handleAddScenario}>{text.addOption}</Button>
                      </div>
                    </CardContent>
                  </Card>

                  {configuredScenarioRows.length > 0 ? (
                    <div className="space-y-4">
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div>
                          <h3 className="text-lg font-semibold">{text.configuredOptions}</h3>
                        </div>
                        <div className="space-x-2">
                          <Button
                            variant="outline"
                            onClick={() => {
                              setScenarioRequests([]);
                              setComparisonResult(null);
                            }}
                          >
                            {text.clearAll}
                          </Button>
                          <Button onClick={handleRunComparison} disabled={isLoading}>
                            {isLoading ? text.running : text.compareSystemOptions}
                          </Button>
                        </div>
                      </div>

                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>{isHebrew ? 'אפשרות' : 'Option'}</TableHead>
                            <TableHead>{text.panelArea}</TableHead>
                            <TableHead>{text.tilt}</TableHead>
                            <TableHead>{text.acCapacity}</TableHead>
                            <TableHead>{text.capex}</TableHead>
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
                                  {formatSignedNumber(scenario.panelAreaDelta)} m² {isHebrew ? 'מול בסיס' : 'vs base'}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>{formatSidebarNumber(scenario.tilt)}°</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.tiltDelta)}`}>
                                  {formatSignedNumber(scenario.tiltDelta)}° {isHebrew ? 'מול בסיס' : 'vs base'}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>{formatSidebarNumber(scenario.acCapacityKw)} kW</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.acCapacityDelta)}`}>
                                  {formatSignedNumber(scenario.acCapacityDelta)} kW {isHebrew ? 'מול בסיס' : 'vs base'}
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>{formatCurrencyAmount(scenario.capex, currency, 0)}</div>
                                <div className={`text-xs ${getDeltaToneClass(scenario.capexDelta, false)}`}>
                                  {formatSignedCurrency(scenario.capexDelta, currency, 0)} {isHebrew ? 'מול בסיס' : 'vs base'}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <Alert>
                      <AlertTitle>{text.noSavedOptions}</AlertTitle>
                      <AlertDescription>
                        {text.noSavedOptionsHelp}
                      </AlertDescription>
                    </Alert>
                  )}

                  {comparisonResult && (
                    <div className="mt-8 space-y-6">
                      {comparisonResult.fallback_reason && (
                        <Alert>
                          <AlertTitle>{isHebrew ? 'הופעלה שיטת גיבוי' : 'Backup forecast method used'}</AlertTitle>
                          <AlertDescription>{comparisonResult.fallback_reason}</AlertDescription>
                        </Alert>
                      )}

                      <Card className="border-primary/25 bg-primary/5">
                        <CardHeader className="gap-4 md:flex-row md:items-start md:justify-between">
                          <div className="space-y-2">
                            <CardTitle className="flex items-center gap-2">
                              {comparisonRecommendationTitle}
                              <HelpTip>{isHebrew ? 'המלצה בין מערכת הבסיס וכל האפשרויות.' : 'Recommendation across Base System and configured options.'}</HelpTip>
                            </CardTitle>
                            <div className="flex flex-wrap gap-2">
                              <Badge variant="secondary">{text.baseReference}</Badge>
                              {recommendedScenario ? <Badge variant="outline">{text.highlightedOption}: {recommendedScenario.label}</Badge> : null}
                            </div>
                          </div>
                          {recommendedScenario ? <Badge className="w-fit">{text.recommended}</Badge> : null}
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div>
                            <p className="text-3xl font-semibold tracking-tight">
                              {recommendedScenario?.label ?? (isHebrew ? 'אין המלצה עדיין' : 'No recommendation yet')}
                            </p>
                            <div className="mt-2">
                              <HelpTip>
                                {comparisonRecommendationSummary} {comparisonRecommendationDetail}
                              </HelpTip>
                            </div>
                          </div>
                          {recommendedScenario ? (
                            <div className="grid gap-3 sm:grid-cols-4">
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.yearlyEnergy}</p>
                                <p className="mt-1 text-lg font-semibold">{formatSidebarNumber(recommendedScenario.yearlyKwh)} kWh</p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.annualSavings}</p>
                                <p className="mt-1 text-lg font-semibold">
                                  {formatCurrencyAmount(recommendedScenario.annualSavings, recommendedScenario.currency)}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.simplePayback}</p>
                                <p className="mt-1 text-lg font-semibold">{formatPaybackYears(recommendedScenario.simplePaybackYears, language)}</p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <p className="text-xs uppercase tracking-wide text-muted-foreground">{text.capex}</p>
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
                            <CardTitle className="text-sm font-medium text-muted-foreground">{text.bestPayback}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-xl font-semibold">{bestPaybackScenario?.label ?? (isHebrew ? 'אין החזר כדאי' : 'No viable payback')}</div>
                            <p className="text-sm text-muted-foreground">
                              {bestPaybackScenario
                                ? formatPaybackYears(bestPaybackScenario.simplePaybackYears, language)
                                : isHebrew
                                  ? 'אין אפשרות כדאית לפי העלות והתעריף הנוכחיים.'
                                  : 'All options are not viable under the current CAPEX/tariff assumptions.'}
                            </p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">{text.highestSavings}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-xl font-semibold">{highestSavingsScenario?.label ?? (isHebrew ? 'אין נתונים' : 'No data')}</div>
                            <p className="text-sm text-muted-foreground">
                              {highestSavingsScenario
                                ? formatCurrencyAmount(highestSavingsScenario.annualSavings, highestSavingsScenario.currency)
                                : isHebrew ? 'אין נתונים' : 'No data'}
                            </p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">{text.mostEnergy}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="text-xl font-semibold">{mostEnergyScenario?.label ?? (isHebrew ? 'אין נתונים' : 'No data')}</div>
                            <p className="text-sm text-muted-foreground">
                              {mostEnergyScenario ? `${formatSidebarNumber(mostEnergyScenario.yearlyKwh)} kWh/${isHebrew ? 'שנה' : 'year'}` : isHebrew ? 'אין נתונים' : 'No data'}
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
                                  {row.isBaseline ? <Badge variant="secondary">{isHebrew ? 'מערכת בסיס' : 'Base System'}</Badge> : null}
                                  {recommendedScenario?.id === row.id ? <Badge variant="outline">{text.recommended}</Badge> : null}
                                </div>
                              </CardTitle>
                              <HelpTip>
                                {row.isBaseline
                                  ? isHebrew ? 'אפשרות ייחוס לכל שינוי שמוצג למטה.' : 'Reference option for every change shown below.'
                                  : isHebrew ? 'מושווה למערכת הבסיס עם אותן הנחות תחזית ותעריף.' : 'Compared against Base System under the same forecast and tariff assumptions.'}
                              </HelpTip>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">{text.yearlyEnergy}</span>
                                  <span className="font-semibold">{formatSidebarNumber(row.yearlyKwh)} kWh</span>
                                </div>
                                <p className={`mt-1 text-xs ${row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.energyDeltaPercent)}`}>
                                  {row.isBaseline
                                    ? isHebrew ? 'אפשרות ייחוס' : 'Reference option'
                                    : `${formatSignedNumber(row.energyDeltaKwh)} kWh · ${formatSignedPercent(row.energyDeltaPercent)} ${isHebrew ? 'מול בסיס' : 'vs base'}`}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">{text.annualSavings}</span>
                                  <span className="font-semibold">{formatCurrencyAmount(row.annualSavings, row.currency)}</span>
                                </div>
                                <p className={`mt-1 text-xs ${row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.savingsDeltaPercent)}`}>
                                  {row.isBaseline
                                    ? isHebrew ? 'אפשרות ייחוס' : 'Reference option'
                                    : `${formatSignedCurrency(row.savingsDeltaValue, row.currency)} · ${formatSignedPercent(row.savingsDeltaPercent)} ${isHebrew ? 'מול בסיס' : 'vs base'}`}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">{text.simplePayback}</span>
                                  <span className="font-semibold">{formatPaybackYears(row.simplePaybackYears, language)}</span>
                                </div>
                                <p className={`mt-1 text-xs ${row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.paybackDeltaYears, false)}`}>
                                  {row.isBaseline
                                    ? isHebrew ? 'אפשרות ייחוס' : 'Reference option'
                                    : row.paybackDeltaYears == null
                                      ? isHebrew ? 'אין דלתא החזר להשוואה' : 'No comparable payback delta'
                                      : `${formatSignedNumber(row.paybackDeltaYears, 1)} ${isHebrew ? 'שנים מול בסיס' : 'years vs base'}`}
                                </p>
                              </div>
                              <div className="rounded-lg border bg-background/70 p-3">
                                <div className="flex items-end justify-between">
                                  <span className="text-sm text-muted-foreground">{text.capex}</span>
                                  <span className="font-semibold">{formatCurrencyAmount(row.capex, row.currency, 0)}</span>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2">
                            {text.monthlyEnergy}
                            <HelpTip>{text.monthlyEnergyHelp}</HelpTip>
                          </CardTitle>
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
                          <CardTitle className="flex items-center gap-2">
                            {text.allOptions}
                            <HelpTip>{text.allOptionsHelp}</HelpTip>
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>{isHebrew ? 'אפשרות' : 'Option'}</TableHead>
                                <TableHead>{text.yearlyEnergy}</TableHead>
                                <TableHead>{isHebrew ? 'אנרגיה מול בסיס' : 'Energy vs Base'}</TableHead>
                                <TableHead>{text.annualSavings}</TableHead>
                                <TableHead>{isHebrew ? 'חיסכון מול בסיס' : 'Savings vs Base'}</TableHead>
                                <TableHead>{text.simplePayback}</TableHead>
                                <TableHead>{isHebrew ? 'החזר מול בסיס' : 'Payback vs Base'}</TableHead>
                                <TableHead>{text.capex}</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {comparisonOptionRows.map((row) => (
                                <TableRow key={row.id}>
                                  <TableCell>
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="font-medium">{row.label}</span>
                                      {row.isBaseline ? <Badge variant="secondary">{isHebrew ? 'מערכת בסיס' : 'Base System'}</Badge> : null}
                                      {recommendedScenario?.id === row.id ? <Badge variant="outline">{text.recommended}</Badge> : null}
                                    </div>
                                  </TableCell>
                                  <TableCell>{formatSidebarNumber(row.yearlyKwh)} kWh</TableCell>
                                  <TableCell className={row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.energyDeltaPercent)}>
                                    {row.isBaseline
                                      ? isHebrew ? 'אפשרות ייחוס' : 'Reference option'
                                      : `${formatSignedNumber(row.energyDeltaKwh)} kWh · ${formatSignedPercent(row.energyDeltaPercent)}`}
                                  </TableCell>
                                  <TableCell>{formatCurrencyAmount(row.annualSavings, row.currency)}</TableCell>
                                  <TableCell className={row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.savingsDeltaPercent)}>
                                    {row.isBaseline
                                      ? isHebrew ? 'אפשרות ייחוס' : 'Reference option'
                                      : `${formatSignedCurrency(row.savingsDeltaValue, row.currency)} · ${formatSignedPercent(row.savingsDeltaPercent)}`}
                                  </TableCell>
                                  <TableCell>{formatPaybackYears(row.simplePaybackYears, language)}</TableCell>
                                  <TableCell className={row.isBaseline ? 'text-muted-foreground' : getDeltaToneClass(row.paybackDeltaYears, false)}>
                                    {row.isBaseline
                                      ? isHebrew ? 'אפשרות ייחוס' : 'Reference option'
                                      : row.paybackDeltaYears == null
                                        ? isHebrew ? 'לא ניתן להשוואה' : 'Not comparable'
                                        : `${formatSignedNumber(row.paybackDeltaYears, 1)} ${isHebrew ? 'שנים' : 'years'}`}
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
                              <p className="flex items-center gap-2 font-semibold">
                                {text.details}
                                <HelpTip>{text.optionsDetailsHelp}</HelpTip>
                              </p>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent className="pb-4">
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>{isHebrew ? 'שדה' : 'Field'}</TableHead>
                                  <TableHead>{isHebrew ? 'ערך' : 'Value'}</TableHead>
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

export type CleanlinessLevel = 'clean' | 'normal' | 'dusty';
export type ShadingLevel = 'none' | 'low' | 'medium' | 'high';
export type CurrencyCode = 'USD' | 'EUR' | 'ILS';

export interface FinancialAssumptions {
  electricity_price_per_kwh: number;
  currency: CurrencyCode;
  system_capex: number;
  valuation_basis: string;
  annual_savings_basis: string;
  payback_basis: string;
}

export interface PVRequestPayload {
  latitude: number; longitude: number; year: number; tilt: number;
  panel_area: number; panel_efficiency: number; cleanliness: CleanlinessLevel;
  shading: ShadingLevel; ac_capacity_kw: number; gamma: number; noct: number;
  electricity_price_per_kwh: number; currency: CurrencyCode; system_capex: number;
}

export interface ScenarioComparisonScenarioPayload {
  name: string; tilt: number; panel_area: number; panel_efficiency: number;
  cleanliness: CleanlinessLevel; shading: ShadingLevel; ac_capacity_kw: number;
  gamma: number; noct: number; system_capex: number;
}

export interface ScenarioComparisonRequestPayload {
  context: Pick<PVRequestPayload, 'latitude' | 'longitude' | 'year' | 'electricity_price_per_kwh' | 'currency'>;
  scenarios: ScenarioComparisonScenarioPayload[];
}

export interface SimulationResponse {
  location: [number, number]; production_model: string; weather_source: string;
  system_loss_factor: number; hourly_ac_kw: number[]; avg_kw: number; daily_kwh: number;
  estimated_daily_value: number; financial_assumptions: FinancialAssumptions;
  timezone: string; hourly_time: string[];
}

export interface YearlyForecastResponse {
  location: [number, number]; requested_forecast_year: number; production_model: string;
  weather_source: string; weather_reference_year: number; monthly_kwh: number[];
  yearly_kwh: number; specific_yield_kwh_per_kwp: number; avg_daily_kwh: number;
  monthly_estimated_value: number[]; yearly_estimated_value: number; annual_savings: number;
  simple_payback_years?: number | null; avg_monthly_estimated_value: number;
  financial_assumptions: FinancialAssumptions; fallback_reason?: string | null;
}

export interface ScenarioComparisonResult {
  scenario: ScenarioComparisonScenarioPayload; yearly_kwh: number; monthly_kwh: number[];
  yearly_estimated_value: number; annual_savings: number; simple_payback_years?: number | null;
  payback_delta_years?: number | null; monthly_estimated_value: number[];
  financial_assumptions: FinancialAssumptions; deviation_percent: number; value_deviation_percent: number;
}

export interface ScenarioComparisonResponse {
  requested_forecast_year: number; production_model: string; weather_source: string;
  weather_reference_year: number; fallback_reason?: string | null; baseline_yearly_kwh: number;
  baseline_yearly_estimated_value: number; baseline_annual_savings: number;
  baseline_simple_payback_years?: number | null; results: ScenarioComparisonResult[];
}

export function resolveApiBaseUrl(): string {
  const value = import.meta.env.VITE_API_BASE_URL?.trim();
  return value && value !== '/' ? value.replace(/\/+$/, '') : '';
}

function errorMessage(payload: unknown, status: number): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as {detail?: unknown}).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item) => typeof item === 'object' && item && 'msg' in item ? String(item.msg) : String(item)).join(', ');
  }
  return `Request failed with status ${status}.`;
}

export async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${resolveApiBaseUrl()}${path}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
  });
  const text = await response.text();
  let body: unknown = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }
  if (!response.ok) throw new Error(errorMessage(body, response.status));
  return body as T;
}

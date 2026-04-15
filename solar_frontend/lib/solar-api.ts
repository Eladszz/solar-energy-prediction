export type ModelType = 'physical' | 'ml';
export type CleanlinessLevel = 'clean' | 'normal' | 'dusty';
export type ShadingLevel = 'none' | 'low' | 'medium' | 'high';
export type CurrencyCode = 'USD' | 'EUR' | 'ILS';
export type BenchmarkApproachType = 'physical' | 'ml' | 'naive';

export interface FinancialAssumptions {
  electricity_price_per_kwh: number;
  currency: CurrencyCode;
  system_capex: number;
  valuation_basis: string;
  annual_savings_basis: string;
  payback_basis: string;
}

export interface PVRequestPayload {
  latitude: number;
  longitude: number;
  year: number;
  tilt: number;
  panel_area: number;
  panel_efficiency: number;
  cleanliness: CleanlinessLevel;
  shading: ShadingLevel;
  ac_capacity_kw: number;
  gamma: number;
  noct: number;
  model_type: ModelType;
  electricity_price_per_kwh: number;
  currency: CurrencyCode;
  system_capex: number;
  training_years: number;
}

export interface BenchmarkEvaluationPayload {
  latitude: number;
  longitude: number;
  year: number;
  benchmark_years: number;
  tilt: number;
  panel_area: number;
  panel_efficiency: number;
  cleanliness: CleanlinessLevel;
  shading: ShadingLevel;
  ac_capacity_kw: number;
  gamma: number;
  noct: number;
  system_capex: number;
  training_years: number;
}

export interface ScenarioComparisonContextPayload {
  latitude: number;
  longitude: number;
  year: number;
  model_type: ModelType;
  training_years: number;
  electricity_price_per_kwh: number;
  currency: CurrencyCode;
}

export interface ScenarioComparisonScenarioPayload {
  name: string;
  tilt: number;
  panel_area: number;
  panel_efficiency: number;
  cleanliness: CleanlinessLevel;
  shading: ShadingLevel;
  ac_capacity_kw: number;
  gamma: number;
  noct: number;
  system_capex: number;
}

export interface ScenarioComparisonRequestPayload {
  context: ScenarioComparisonContextPayload;
  scenarios: ScenarioComparisonScenarioPayload[];
}

export interface SimulationResponse {
  location: [number, number];
  system_loss_factor: number;
  hourly_ac_kw: number[];
  avg_kw: number;
  daily_kwh: number;
  estimated_daily_value: number;
  financial_assumptions: FinancialAssumptions;
  timezone: string;
  hourly_time: string[];
  data_source: 'live' | 'demo';
  demo_scenario_id?: string | null;
  demo_scenario_name?: string | null;
}

export interface YearlyForecastResponse {
  location: [number, number];
  forecast_year: number;
  model_type_requested: ModelType;
  model_type_used: ModelType;
  weather_reference_year?: number | null;
  training_years_used: number[];
  monthly_kwh: number[];
  yearly_kwh: number;
  specific_yield_kwh_per_kwp: number;
  avg_daily_kwh: number;
  monthly_estimated_value: number[];
  yearly_estimated_value: number;
  annual_savings: number;
  simple_payback_years?: number | null;
  avg_monthly_estimated_value: number;
  financial_assumptions: FinancialAssumptions;
  fallback_reason?: string | null;
  ml_metadata?: Record<string, unknown> | null;
  data_source: 'live' | 'demo';
  demo_scenario_id?: string | null;
  demo_scenario_name?: string | null;
}

export interface AccuracyEvaluationResponse {
  year: number;
  model_type_requested: ModelType;
  model_type_used: ModelType;
  weather_reference_year?: number | null;
  training_years_used: number[];
  fallback_reason?: string | null;
  actual_yearly_kwh: number;
  predicted_yearly_kwh: number;
  actual_yearly_estimated_value: number;
  predicted_yearly_estimated_value: number;
  actual_annual_savings: number;
  predicted_annual_savings: number;
  actual_simple_payback_years?: number | null;
  predicted_simple_payback_years?: number | null;
  actual_monthly_kwh: number[];
  predicted_monthly_kwh: number[];
  actual_monthly_estimated_value: number[];
  predicted_monthly_estimated_value: number[];
  monthly_mae_kwh: number;
  mape_percent: number;
  yearly_mae_kwh: number;
  yearly_mape_percent: number;
  bias_percent: number;
  bias_kwh: number;
  quality: 'EXCELLENT' | 'GOOD' | 'POOR';
  financial_assumptions: FinancialAssumptions;
  ml_metadata?: Record<string, unknown> | null;
  data_source: 'live' | 'demo';
  demo_scenario_id?: string | null;
  demo_scenario_name?: string | null;
}

export interface BenchmarkMetrics {
  monthly_mape_percent: number;
  monthly_mae_kwh: number;
  yearly_mape_percent: number;
  yearly_mae_kwh: number;
  bias_percent: number;
  bias_kwh: number;
}

export interface BenchmarkYearResult {
  year: number;
  actual_yearly_kwh: number;
  predicted_yearly_kwh: number;
  actual_monthly_kwh: number[];
  predicted_monthly_kwh: number[];
  yearly_mape_percent: number;
  yearly_mae_kwh: number;
  yearly_bias_kwh: number;
  model_type_used: BenchmarkApproachType;
  weather_reference_year?: number | null;
  training_years_used: number[];
  fallback_reason?: string | null;
}

export interface BenchmarkApproachResult {
  approach: BenchmarkApproachType;
  label: string;
  description: string;
  metrics: BenchmarkMetrics;
  yearly_results: BenchmarkYearResult[];
  fallback_years: number[];
}

export interface BenchmarkEvaluationResponse {
  evaluation_years: number[];
  benchmark_years_requested: number;
  training_window_years: number;
  reference_note: string;
  approaches: BenchmarkApproachResult[];
  data_source: 'live' | 'demo';
  demo_scenario_id?: string | null;
  demo_scenario_name?: string | null;
}

export interface ScenarioComparisonResult {
  scenario: ScenarioComparisonScenarioPayload;
  yearly_kwh: number;
  monthly_kwh: number[];
  yearly_estimated_value: number;
  annual_savings: number;
  simple_payback_years?: number | null;
  payback_delta_years?: number | null;
  monthly_estimated_value: number[];
  financial_assumptions: FinancialAssumptions;
  deviation_percent: number;
  value_deviation_percent: number;
}

export interface ScenarioComparisonResponse {
  year: number;
  model_type_requested: ModelType;
  model_type_used: ModelType;
  weather_reference_year?: number | null;
  training_years_used: number[];
  fallback_reason?: string | null;
  baseline_yearly_kwh: number;
  baseline_yearly_estimated_value: number;
  baseline_annual_savings: number;
  baseline_simple_payback_years?: number | null;
  results: ScenarioComparisonResult[];
  data_source: 'live' | 'demo';
  demo_scenario_id?: string | null;
  demo_scenario_name?: string | null;
}

function normalizeBaseUrl(value: string): string {
  const trimmedValue = value.trim();
  if (!trimmedValue || trimmedValue === '/') {
    return '';
  }

  return trimmedValue.replace(/\/+$/, '');
}

export function resolveApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    return normalizeBaseUrl(configured);
  }

  return '';
}

function buildErrorMessage(payload: unknown, status: number): string {
  if (typeof payload === 'string' && payload.trim()) {
    return payload;
  }

  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail)) {
      const message = detail
        .map((entry) => {
          if (typeof entry === 'string') {
            return entry;
          }
          if (entry && typeof entry === 'object' && 'msg' in entry) {
            return String((entry as { msg: unknown }).msg);
          }
          return null;
        })
        .filter(Boolean)
        .join(', ');
      if (message) {
        return message;
      }
    }
  }

  return `Request failed with status ${status}.`;
}

export async function apiPost<TResponse>(
  path: string,
  payload: unknown,
): Promise<TResponse> {
  const response = await fetch(`${resolveApiBaseUrl()}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const rawBody = await response.text();
  let parsedBody: unknown = null;
  if (rawBody) {
    try {
      parsedBody = JSON.parse(rawBody);
    } catch {
      parsedBody = rawBody;
    }
  }

  if (!response.ok) {
    throw new Error(buildErrorMessage(parsedBody, response.status));
  }

  return parsedBody as TResponse;
}

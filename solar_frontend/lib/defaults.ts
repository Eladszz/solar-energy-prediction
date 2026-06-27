import type { CleanlinessLevel, CurrencyCode, ModelType, ShadingLevel } from '@/lib/solar-api';
import defaults from '../../shared/defaults.json';

export const APP_DEFAULTS = {
  tiltDegrees: defaults.tilt_degrees,
  panelAreaSqm: defaults.panel_area_sqm,
  panelEfficiency: defaults.panel_efficiency,
  cleanliness: defaults.cleanliness as CleanlinessLevel,
  shading: defaults.shading as ShadingLevel,
  acCapacityKw: defaults.ac_capacity_kw,
  gamma: defaults.temperature_coefficient,
  noctC: defaults.noct_c,
  modelType: defaults.model_type as ModelType,
  electricityPricePerKwh: defaults.electricity_price_per_kwh,
  currency: defaults.currency as CurrencyCode,
  systemCapex: defaults.system_capex,
  trainingYears: defaults.training_years,
  benchmarkYears: defaults.benchmark_years,
  scenarioPanelAreaDeltaPercent: defaults.scenario_panel_area_delta_percent,
  scenarioNamePrefix: defaults.scenario_name_prefix,
} as const;

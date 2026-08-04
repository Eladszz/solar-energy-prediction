import type { CleanlinessLevel, CurrencyCode, ShadingLevel } from '@/lib/solar-api';
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
  electricityPricePerKwh: defaults.electricity_price_per_kwh,
  currency: defaults.currency as CurrencyCode,
  systemCapex: defaults.system_capex,
  scenarioPanelAreaDeltaPercent: defaults.scenario_panel_area_delta_percent,
  scenarioNamePrefix: defaults.scenario_name_prefix,
} as const;

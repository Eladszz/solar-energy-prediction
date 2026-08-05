import type {CurrencyCode} from '@/lib/solar-api';
import type {Copy, Language} from '@/src/i18n';

const localeFor = (language: Language) => language === 'he' ? 'he-IL' : 'en-US';

export function formatNumber(value: number | null | undefined, language: Language, maximumFractionDigits = 1): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return new Intl.NumberFormat(localeFor(language), {maximumFractionDigits}).format(value);
}

export function formatEnergy(value: number | null | undefined, language: Language, maximumFractionDigits = 0): string {
  return `${formatNumber(value, language, maximumFractionDigits)} kWh`;
}

export function formatPower(value: number | null | undefined, language: Language, maximumFractionDigits = 2): string {
  return `${formatNumber(value, language, maximumFractionDigits)} kW`;
}

export function formatMoney(value: number | null | undefined, currency: CurrencyCode, language: Language, maximumFractionDigits = 0): string {
  if (value == null || !Number.isFinite(value)) return '—';
  return new Intl.NumberFormat(localeFor(language), {
    style: 'currency',
    currency,
    maximumFractionDigits,
  }).format(value);
}

export function formatPercent(value: number | null | undefined, language: Language, maximumFractionDigits = 1, withSign = false): string {
  if (value == null || !Number.isFinite(value)) return '—';
  const formatted = formatNumber(Math.abs(value), language, maximumFractionDigits);
  const sign = withSign ? value > 0 ? '+' : value < 0 ? '−' : '' : value < 0 ? '−' : '';
  return `${sign}${formatted}%`;
}

export function formatPayback(value: number | null | undefined, language: Language, copy: Copy): string {
  if (value == null || !Number.isFinite(value)) return copy.notViable;
  return `${formatNumber(value, language, 1)} ${copy.years}`;
}

export function formatHour(value: string | undefined, fallbackIndex: number): string {
  if (!value) return `${String(fallbackIndex).padStart(2, '0')}:00`;
  const time = value.includes('T') ? value.split('T')[1] : value;
  return time?.slice(0, 5) || `${String(fallbackIndex).padStart(2, '0')}:00`;
}

export function formatDate(value: string | undefined, language: Language): string {
  if (!value) return '—';
  const datePart = value.includes('T') ? value.split('T')[0] : value.slice(0, 10);
  const parsed = new Date(`${datePart}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return datePart;
  return new Intl.DateTimeFormat(localeFor(language), {dateStyle: 'medium'}).format(parsed);
}

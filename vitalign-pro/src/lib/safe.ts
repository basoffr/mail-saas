/**
 * Safe Runtime Utilities
 * Provides defensive helpers for array/bool/string normalization
 * to prevent TypeErrors when API contracts vary
 */

/**
 * Ensure value is an array, return fallback if not
 */
export const asArray = <T = any>(v: any, fallback: T[] = []): T[] =>
  Array.isArray(v) ? (v as T[]) : fallback;

/**
 * Ensure value is a boolean, return fallback if not
 */
export const asBool = (v: any, fallback = false): boolean =>
  typeof v === 'boolean' ? v : fallback;

/**
 * Ensure value is a string, return fallback if not
 */
export const asString = (v: any, fallback = ''): string =>
  typeof v === 'string' ? v : fallback;

/**
 * Pick first valid value from object by trying multiple keys
 * Handles camelCase/snake_case variations
 */
export const pick = <T = any>(obj: any, keys: string[], fallback: T): T => {
  if (!obj) return fallback;
  for (const k of keys) {
    const val = obj[k];
    if (val !== undefined && val !== null) return val;
  }
  return fallback;
};

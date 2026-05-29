// NEC Lookup Tables
// Per-year data lives in src/data/years/nec<YYYY>.js
// This file re-exports everything so existing imports don't need to change.

import * as nec2014 from './years/nec2014.js';
import * as nec2017 from './years/nec2017.js';
import * as nec2020 from './years/nec2020.js';
import * as nec2023 from './years/nec2023.js';

// Registry keyed by year — use this when you need to look up tables for a specific edition
export const NEC_TABLE_REGISTRY = {
  2014: nec2014,
  2017: nec2017,
  2020: nec2020,
  2023: nec2023,
};

// NEC year options
export const NEC_YEARS = [2014, 2017, 2020, 2023];

// Year-specific notes assembled from each edition's YEAR_NOTES
export const NEC_YEAR_NOTES = {
  2014: nec2014.YEAR_NOTES,
  2017: nec2017.YEAR_NOTES,
  2020: nec2020.YEAR_NOTES,
  2023: nec2023.YEAR_NOTES,
};

// Shared UI constants (not year-specific)
export const UNIT_COUNT_OPTIONS = [
  '1 unit', '2 units', '3 units', '4 units', '5 units',
  '6 units', '7 units', '8 units', '9 units', '10 units',
  '15 units', '20 units', '25 units', '30 units', '40 units', '50 units',
];

// Phase / service configurations (NEC 220.83)
export const PHASE_CONFIGS = [
  '1-Phase, 3-Wire 120/240 V',
  '1-Phase, 2-Wire 120 V with neutral',
  '1-Phase, 2-Wire 240 V (No neutral)',
  '3-Phase, 4-Wire 208Y/120 V',
  '3-Phase, 4-Wire 480Y/277 V',
];

// Re-exports of 2017 tables for backwards compatibility with existing imports
export { BUILDING_TYPES, RANGE_DEMAND_TABLE, OPTIONAL_MULTI_UNIT_DF, DEFAULT_APPLIANCES, HVAC_COMPONENTS } from './years/nec2017.js';

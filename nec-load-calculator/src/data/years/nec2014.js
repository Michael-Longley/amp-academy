// NEC 2014 Lookup Tables
// TODO: verify all values against NEC 2014 edition — currently copied from 2017 as a placeholder

// Table 220.12 — General Lighting Loads by Occupancy
// Values in VA per square foot.
export const BUILDING_TYPES = [
  { key: 'armories',        label: 'Armories & auditoriums',                      vaPerSqft: 1.0,  vaPerM2: 11.0 },
  { key: 'banks',           label: 'Banks',                                        vaPerSqft: 3.5,  vaPerM2: 39.0 },
  { key: 'barberBeauty',    label: 'Barber & beauty shops',                        vaPerSqft: 3.0,  vaPerM2: 33.0 },
  { key: 'churches',        label: 'Churches',                                     vaPerSqft: 1.0,  vaPerM2: 11.0 },
  { key: 'clubs',           label: 'Clubs',                                        vaPerSqft: 2.0,  vaPerM2: 22.0 },
  { key: 'courtrooms',      label: 'Courtrooms',                                   vaPerSqft: 2.0,  vaPerM2: 22.0 },
  { key: 'dwelling',        label: 'Dwelling Units',                               vaPerSqft: 3.0,  vaPerM2: 33.0 },
  { key: 'garages',         label: 'Garages — commercial (storage)',               vaPerSqft: 0.5,  vaPerM2: 6.0  },
  { key: 'hospitals',       label: 'Hospitals',                                    vaPerSqft: 2.0,  vaPerM2: 22.0 },
  { key: 'hotelsMotels',    label: 'Hotels & Motels',                              vaPerSqft: 2.0,  vaPerM2: 22.0 },
  { key: 'industrialLoft',  label: 'Industrial commercial (loft) buildings',       vaPerSqft: 2.0,  vaPerM2: 22.0 },
  { key: 'lodgeRooms',      label: 'Lodge rooms',                                  vaPerSqft: 1.5,  vaPerM2: 17.0 },
  { key: 'offices',         label: 'Office buildings',                             vaPerSqft: 3.5,  vaPerM2: 39.0 },
  { key: 'restaurants',     label: 'Restaurants',                                  vaPerSqft: 2.0,  vaPerM2: 22.0 },
  { key: 'schools',         label: 'Schools',                                      vaPerSqft: 3.0,  vaPerM2: 33.0 },
  { key: 'stores',          label: 'Stores',                                       vaPerSqft: 3.0,  vaPerM2: 33.0 },
  { key: 'warehouses',      label: 'Warehouses (storage)',                         vaPerSqft: 0.25, vaPerM2: 3.0  },
  { key: 'assemblyHalls',   label: 'Assembly halls & auditoriums',                 vaPerSqft: 1.0,  vaPerM2: 11.0 },
  { key: 'hallsCorridors',  label: 'Halls, corridors, closets, stairways',        vaPerSqft: 0.5,  vaPerM2: 6.0  },
  { key: 'storageSpaces',   label: 'Storage spaces',                               vaPerSqft: 0.25, vaPerM2: 3.0  },
];

// Table 220.55 — Range/Cooking Equipment Demand Factors
// TODO: verify against NEC 2014 Table 220.55
export const RANGE_DEMAND_TABLE = [
  { qty: 1,  dfOver12kW: 0.80, kWUnder12kW: 8  },
  { qty: 2,  dfOver12kW: 0.75, kWUnder12kW: 11 },
  { qty: 3,  dfOver12kW: 0.70, kWUnder12kW: 14 },
  { qty: 4,  dfOver12kW: 0.66, kWUnder12kW: 17 },
  { qty: 5,  dfOver12kW: 0.62, kWUnder12kW: 20 },
  { qty: 6,  dfOver12kW: 0.59, kWUnder12kW: 21 },
  { qty: 7,  dfOver12kW: 0.56, kWUnder12kW: 22 },
  { qty: 8,  dfOver12kW: 0.53, kWUnder12kW: 23 },
  { qty: 9,  dfOver12kW: 0.51, kWUnder12kW: 24 },
  { qty: 10, dfOver12kW: 0.49, kWUnder12kW: 25 },
  { qty: 11, dfOver12kW: 0.47, kWUnder12kW: 26 },
  { qty: 12, dfOver12kW: 0.45, kWUnder12kW: 27 },
  { qty: 13, dfOver12kW: 0.43, kWUnder12kW: 28 },
  { qty: 14, dfOver12kW: 0.41, kWUnder12kW: 29 },
  { qty: 15, dfOver12kW: 0.40, kWUnder12kW: 30 },
  { qty: 16, dfOver12kW: 0.39, kWUnder12kW: 31 },
  { qty: 17, dfOver12kW: 0.38, kWUnder12kW: 32 },
  { qty: 18, dfOver12kW: 0.37, kWUnder12kW: 33 },
  { qty: 19, dfOver12kW: 0.36, kWUnder12kW: 34 },
  { qty: 20, dfOver12kW: 0.35, kWUnder12kW: 35 },
  { qty: 21, dfOver12kW: 0.34, kWUnder12kW: 36 },
  { qty: 22, dfOver12kW: 0.33, kWUnder12kW: 37 },
  { qty: 23, dfOver12kW: 0.32, kWUnder12kW: 38 },
  { qty: 24, dfOver12kW: 0.31, kWUnder12kW: 39 },
  { qty: 25, dfOver12kW: 0.30, kWUnder12kW: 40 },
];

// Table 220.82(B) — Optional Method Demand Factors for 3+ Dwelling Units
// TODO: verify against NEC 2014 Table 220.82(B)
export const OPTIONAL_MULTI_UNIT_DF = [
  { units: 3,  df: 0.45 },
  { units: 4,  df: 0.45 },
  { units: 5,  df: 0.45 },
  { units: 6,  df: 0.44 },
  { units: 7,  df: 0.44 },
  { units: 8,  df: 0.43 },
  { units: 9,  df: 0.43 },
  { units: 10, df: 0.43 },
  { units: 11, df: 0.42 },
  { units: 12, df: 0.41 },
  { units: 13, df: 0.41 },
  { units: 14, df: 0.40 },
  { units: 15, df: 0.40 },
  { units: 16, df: 0.39 },
  { units: 17, df: 0.39 },
  { units: 18, df: 0.38 },
  { units: 19, df: 0.38 },
  { units: 20, df: 0.38 },
  { units: 21, df: 0.37 },
  { units: 22, df: 0.36 },
  { units: 23, df: 0.36 },
  { units: 24, df: 0.35 },
  { units: 25, df: 0.35 },
  { units: 26, df: 0.34 },
  { units: 27, df: 0.34 },
  { units: 28, df: 0.33 },
  { units: 29, df: 0.33 },
  { units: 30, df: 0.33 },
  { units: 31, df: 0.32 },
  { units: 32, df: 0.31 },
  { units: 33, df: 0.31 },
  { units: 34, df: 0.30 },
  { units: 35, df: 0.30 },
  { units: 36, df: 0.30 },
  { units: 37, df: 0.29 },
  { units: 38, df: 0.29 },
  { units: 39, df: 0.28 },
  { units: 40, df: 0.28 },
  { units: 41, df: 0.28 },
  { units: 42, df: 0.28 },
  { units: 43, df: 0.27 },
  { units: 44, df: 0.27 },
  { units: 45, df: 0.27 },
  { units: 46, df: 0.26 },
  { units: 47, df: 0.26 },
  { units: 48, df: 0.26 },
  { units: 49, df: 0.26 },
  { units: 50, df: 0.26 },
  { units: 51, df: 0.25 },
  { units: 55, df: 0.25 },
  { units: 56, df: 0.24 },
  { units: 60, df: 0.24 },
  { units: 61, df: 0.24 },
  { units: 62, df: 0.23 },
];

// Default appliance nameplate VA ratings
// TODO: verify against NEC 2014
export const DEFAULT_APPLIANCES = {
  disposal:       { label: 'Disposal',                nameplate: 100,   necRef: '220.53' },
  waterHeater:    { label: 'Water Heater',             nameplate: 4500,  necRef: '220.53' },
  compactor:      { label: 'Trash Compactor',          nameplate: 1200,  necRef: '220.53' },
  centralVacuum:  { label: 'Central Vacuum',           nameplate: 840,   necRef: '220.53' },
  dishwasher:     { label: 'Dishwasher',               nameplate: 1200,  necRef: '220.53' },
};

// HVAC components
export const HVAC_COMPONENTS = {
  heating:            { label: 'Heating',               necRef: '220.60' },
  cooling:            { label: 'Cooling / AC',          necRef: '220.60' },
  blower:             { label: 'Blower Motor',          necRef: '220.60' },
  acCompressor:       { label: 'AC Compressor',         necRef: '220.60' },
  heatPump:           { label: 'Heat Pump',             necRef: '220.60' },
  heatPumpCompressor: { label: 'Heat Pump Compressor',  necRef: '220.60' },
  supplemental:       { label: 'Supplemental Heat/Air', necRef: '220.60' },
  spaceHeaters:       { label: 'Space Heaters',         necRef: '220.60' },
};

// Year-specific notes / rule differences
export const YEAR_NOTES = {
  optionalMethodNote: 'NEC 2014 § 220.82 — Optional calculation for dwelling units.',
  dryerNote: 'NEC 2014 § 220.54 — Minimum 5,000W per dryer.',
  rangeNote: 'NEC 2014 § 220.55 — Table 220.55 demand factors apply.',
  evNote: null,
};

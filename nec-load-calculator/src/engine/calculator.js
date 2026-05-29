/**
 * NEC Load Calculator Engine
 *
 * Mirrors the formulas in the Load sheet of the Excel workbook.
 * All inputs and outputs are in Volt-Amperes (VA) unless noted.
 *
 * Article references:
 *   220.12  — General Lighting Loads
 *   220.52  — Small Appliance & Laundry Branch Circuits
 *   220.53  — Appliance Load (fastened in place)
 *   220.54  — Electric Clothes Dryers
 *   220.55  — Electric Ranges, etc. (Table 220.55)
 *   220.60  — Noncoincident Loads (HVAC max)
 *   220.82  — Optional Calculation for Dwelling Units
 */

import { BUILDING_TYPES, RANGE_DEMAND_TABLE, OPTIONAL_MULTI_UNIT_DF } from '../data/necTables.js';

// ─────────────────────────────────────────────────────────────────────────────
// Utility helpers
// ─────────────────────────────────────────────────────────────────────────────

/** Parse a unit-count string like "3 units" → 3 */
export function parseUnits(unitStr) {
  const n = parseInt(unitStr, 10);
  return isNaN(n) ? 1 : n;
}

/** Look up VA per square foot for a building type key */
export function getLightingVA(buildingTypeKey, areaUnit) {
  const found = BUILDING_TYPES.find(b => b.key === buildingTypeKey);
  if (!found) return 0;
  return areaUnit === 'sqm' ? found.vaPerM2 : found.vaPerSqft;
}

/** Range demand factor from Table 220.55 for a given qty */
function getRangeDemand(qty, nameplateVA) {
  if (qty <= 0 || nameplateVA <= 0) return 0;
  // Table 220.55: find the matching qty (cap at 25 for table lookup, use 0.30 DF beyond)
  const capped = Math.min(qty, 25);
  const row = RANGE_DEMAND_TABLE.find(r => r.qty === capped)
    || RANGE_DEMAND_TABLE[RANGE_DEMAND_TABLE.length - 1];

  if (nameplateVA <= 12000) {
    // Nameplate ≤ 12 kW: use the kW demand value from the table (AJ column), multiply by units
    // For qty > 1, add demand proportionally (NEC Table 220.55 Note 1)
    return row.kWUnder12kW * 1000;
  } else {
    // Nameplate > 12 kW: use demand factor (AH column) × total nameplate
    return row.dfOver12kW * nameplateVA * qty;
  }
}

/** Optional method demand factor for 3+ units from Table 220.82(B) */
function getOptionalMultiUnitDF(units) {
  // Find the closest row at or below the unit count
  const sorted = [...OPTIONAL_MULTI_UNIT_DF].sort((a, b) => b.units - a.units);
  const row = sorted.find(r => r.units <= units);
  return row ? row.df : 0.23; // 62+ units → 0.23
}

// ─────────────────────────────────────────────────────────────────────────────
// Step-by-step load calculations
// ─────────────────────────────────────────────────────────────────────────────

/**
 * General Lighting Load — NEC 220.12
 * @param {number} area  numeric area value
 * @param {'sqft'|'sqm'} areaUnit
 * @param {string} buildingTypeKey
 * @returns {number} VA
 */
export function calcLighting(area, areaUnit, buildingTypeKey) {
  if (!area || area <= 0) return 0;
  const vaPerUnit = getLightingVA(buildingTypeKey, areaUnit);
  return area * vaPerUnit;
}

/**
 * Small Appliance Branch Circuits — NEC 220.52(A)
 * Minimum 2 circuits required.
 * @param {number} numCircuits
 * @returns {number} VA
 */
export function calcSmallAppliance(numCircuits = 2) {
  return Math.max(2, numCircuits) * 1500;
}

/**
 * Laundry Branch Circuit — NEC 220.52(B)
 * @param {boolean} hasLaundry
 * @returns {number} VA
 */
export function calcLaundry(hasLaundry = true) {
  return hasLaundry ? 1500 : 0;
}

/**
 * Fastened-in-Place Appliances — NEC 220.53
 * @param {Array<{qty:number, nameplate:number}>} appliances  per-unit quantities & VA
 * @param {number} units   number of building units
 * @param {'standard'|'optional'} method
 * @returns {{ total: number, demandFactor: number, subtotal: number }}
 */
export function calcFastenedAppliances(appliances, units, method) {
  const effectiveQty = appliances.reduce((sum, a) => sum + a.qty * units, 0);
  const subtotal = appliances.reduce((sum, a) => sum + a.qty * units * a.nameplate, 0);

  if (method === 'optional') {
    // Optional Method: no demand factor — full nameplate
    return { total: subtotal, demandFactor: 1.0, subtotal };
  }

  // Standard Method: 75% demand factor if 4 or more units of appliances
  const df = effectiveQty >= 4 ? 0.75 : 1.0;
  return { total: subtotal * df, demandFactor: df, subtotal };
}

/**
 * Electric Range/Cooking Equipment — NEC 220.55 (Table 220.55)
 * @param {number} qty    number of ranges per unit
 * @param {number} nameplateVA  nameplate rating in VA (convert kW × 1000)
 * @param {number} units  number of building units
 * @param {'standard'|'optional'} method
 * @returns {number} VA
 */
export function calcRange(qty, nameplateVA, units, method) {
  if (qty <= 0 || nameplateVA <= 0) return 0;
  const totalQty = qty * units;

  if (method === 'optional') {
    return nameplateVA * totalQty;
  }

  // Standard Method: Table 220.55 demand
  return getRangeDemand(totalQty, nameplateVA);
}

/**
 * Electric Clothes Dryer — NEC 220.54
 * Minimum 5,000 VA per dryer.
 * @param {number} qty    number of dryers per unit
 * @param {number} nameplateVA
 * @param {number} units
 * @param {'standard'|'optional'} method
 * @returns {number} VA
 */
export function calcDryer(qty, nameplateVA, units, method) {
  if (qty <= 0) return 0;
  const totalQty = qty * units;

  if (method === 'optional') {
    return nameplateVA * totalQty;
  }

  // Standard Method: use 5,000 VA minimum per dryer
  const effectiveVA = Math.max(5000, nameplateVA);
  return effectiveVA * totalQty;
}

/**
 * HVAC — Noncoincident Loads — NEC 220.60
 * Uses the larger of heating or cooling (never both).
 *
 * @param {{heating:number, cooling:number, blower:number, acCompressor:number,
 *           heatPump:number, heatPumpCompressor:number, supplemental:number, spaceHeaters:number}} hvac
 *   All values already converted to VA (qty × nameplate × units)
 * @returns {{ hvacTotal: number, heatingTotal: number, coolingTotal: number, usedFor: string }}
 */
export function calcHVAC(hvac) {
  const {
    heating = 0, cooling = 0, blower = 0, acCompressor = 0,
    heatPump = 0, heatPumpCompressor = 0, supplemental = 0, spaceHeaters = 0,
  } = hvac;

  // Heating side: heating + blower + heat pump + heat pump compressor + supplemental + space heaters
  const heatingTotal = heating + blower + heatPump + heatPumpCompressor + supplemental + spaceHeaters;

  // Cooling side: cooling + blower + AC compressor
  const coolingTotal = cooling + blower + acCompressor;

  const hvacTotal = Math.max(heatingTotal, coolingTotal);
  const usedFor = heatingTotal >= coolingTotal ? 'heating' : 'cooling';

  return { hvacTotal, heatingTotal, coolingTotal, usedFor };
}

/**
 * Continuous Loads — NEC 220.14(F) / 215.2 / 230.42
 * In load calculation summaries, continuous loads are counted at nameplate.
 * (The 125% factor is for branch-circuit / feeder conductor sizing, not load totals.)
 * @param {Array<{qty:number, nameplate:number}>} loads  per-unit
 * @param {number} units
 * @returns {number} VA
 */
export function calcContinuous(loads, units) {
  return loads.reduce((sum, l) => sum + l.qty * units * l.nameplate, 0);
}

// ─────────────────────────────────────────────────────────────────────────────
// Final load assembly
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Calculate the complete NEC load breakdown.
 *
 * @param {object} inputs
 * @param {string}  inputs.buildingType       key from BUILDING_TYPES
 * @param {number}  inputs.area               numeric area
 * @param {'sqft'|'sqm'} inputs.areaUnit
 * @param {number}  inputs.units              number of building units
 * @param {'standard'|'optional'} inputs.method
 * @param {number}  inputs.year               NEC year (2014/2017/2020/2023)
 * @param {number}  inputs.smallApplianceCircuits
 * @param {boolean} inputs.hasLaundry
 * @param {Array<{qty,nameplate}>} inputs.fastenedAppliances
 * @param {{qty:number, nameplateVA:number}} inputs.range
 * @param {{qty:number, nameplateVA:number}} inputs.dryer
 * @param {object}  inputs.hvacInputs         raw {qty, nameplate} per component
 * @param {Array<{qty,nameplate}>} inputs.otherLoads
 *
 * @returns {object} detailed breakdown with all intermediate values
 */
export function calculateLoad(inputs) {
  const {
    buildingType,
    area,
    areaUnit,
    units,
    method,
    smallApplianceCircuits = 2,
    hasLaundry = true,
    fastenedAppliances = [],
    range = { qty: 0, nameplateVA: 0 },
    dryer = { qty: 0, nameplateVA: 0 },
    hvacInputs = {},
    otherLoads = [],
  } = inputs;

  // ── Step 1: Lighting & Circuits ────────────────────────────────────────────
  const lightingVA       = calcLighting(area, areaUnit, buildingType);
  const smallApplianceVA = calcSmallAppliance(smallApplianceCircuits);
  const laundryVA        = calcLaundry(hasLaundry);
  const lightingTotal    = lightingVA + smallApplianceVA + laundryVA;

  // ── Step 2: Fastened Appliances ────────────────────────────────────────────
  const fastenedResult = calcFastenedAppliances(fastenedAppliances, units, method);

  // ── Step 3: Cord & Plug (Range + Dryer) ───────────────────────────────────
  const rangeVA = calcRange(range.qty, range.nameplateVA, units, method);
  const dryerVA = calcDryer(dryer.qty, dryer.nameplateVA, units, method);
  const cordPlugTotal = rangeVA + dryerVA;

  // ── Step 4: HVAC ──────────────────────────────────────────────────────────
  // Convert per-unit hvacInputs into VA totals
  const hvacVA = {};
  const hvacComponents = ['heating','cooling','blower','acCompressor','heatPump','heatPumpCompressor','supplemental','spaceHeaters'];
  for (const comp of hvacComponents) {
    const c = hvacInputs[comp] || { qty: 0, nameplate: 0 };
    hvacVA[comp] = c.qty * c.nameplate * units;
  }
  const hvacResult = calcHVAC(hvacVA);

  // ── Step 5: Other Loads ───────────────────────────────────────────────────
  const continuousVA = calcContinuous(otherLoads, units);

  // ── Final Assembly ─────────────────────────────────────────────────────────
  let finalLoadVA = 0;
  let optionalBreakdown = null;

  if (method === 'standard') {
    finalLoadVA =
      lightingTotal +
      fastenedResult.total +
      cordPlugTotal +
      hvacResult.hvacTotal +
      continuousVA;

  } else {
    // Optional Method — NEC 220.82
    const isDwelling = buildingType === 'dwelling';

    if (isDwelling && units <= 2) {
      // 1–2 dwelling units: first 10,000 VA @ 100% + remainder @ 40% + HVAC @ 100%
      const baseLoad =
        lightingTotal +
        fastenedResult.total +    // no demand factor for optional
        cordPlugTotal +
        continuousVA;

      const first10k    = Math.min(baseLoad, 10000);
      const remainder40 = Math.max(0, baseLoad - 10000) * 0.40;
      const demandLoad  = first10k + remainder40;

      finalLoadVA = demandLoad + hvacResult.hvacTotal;

      optionalBreakdown = {
        baseLoad,
        first10k,
        remainder40,
        demandLoad,
        hvac: hvacResult.hvacTotal,
        demandFactor40pct: 0.40,
      };

    } else if (isDwelling && units >= 3) {
      // 3+ dwelling units: use demand factor table
      const df = getOptionalMultiUnitDF(units);
      const allLoads =
        lightingTotal +
        fastenedResult.total +
        cordPlugTotal +
        hvacResult.hvacTotal +
        continuousVA;

      finalLoadVA = allLoads * df;

      optionalBreakdown = {
        allLoads,
        demandFactor: df,
      };

    } else {
      // Non-dwelling optional: fall back to standard method sum
      finalLoadVA =
        lightingTotal +
        fastenedResult.total +
        cordPlugTotal +
        hvacResult.hvacTotal +
        continuousVA;
    }
  }

  return {
    // Inputs (for display)
    method,
    units,
    buildingType,
    area,
    areaUnit,

    // Line items
    lightingVA,
    smallApplianceVA,
    laundryVA,
    lightingTotal,

    fastenedSubtotal: fastenedResult.subtotal,
    fastenedDemandFactor: fastenedResult.demandFactor,
    fastenedTotal: fastenedResult.total,

    rangeVA,
    dryerVA,
    cordPlugTotal,

    hvacHeatingTotal: hvacResult.heatingTotal,
    hvacCoolingTotal: hvacResult.coolingTotal,
    hvacTotal: hvacResult.hvacTotal,
    hvacUsedFor: hvacResult.usedFor,

    continuousVA,

    // Optional method details (only for optional)
    optionalBreakdown,

    // Final
    finalLoadVA: Math.round(finalLoadVA),
    finalAmps: finalLoadVA > 0 ? (finalLoadVA / 240).toFixed(1) : '—',
  };
}

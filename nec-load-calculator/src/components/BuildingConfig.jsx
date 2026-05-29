import { BUILDING_TYPES, UNIT_COUNT_OPTIONS, PHASE_CONFIGS } from '../data/necTables.js';

export default function BuildingConfig({ building, onChange }) {
  const { units, buildingType, area, areaUnit, phaseConfig, smallApplianceCircuits, hasLaundry } = building;

  return (
    <section className="card">
      <h2 className="step-header">
        <span className="step-badge">Step 1</span>
        Building Configuration
      </h2>

      <div className="form-grid">
        {/* Unit count */}
        <div className="field">
          <label>Number of Units
            <span className="nec-ref">NEC 220.82</span>
          </label>
          <select
            value={units}
            onChange={e => onChange('units', e.target.value)}
          >
            {UNIT_COUNT_OPTIONS.map(u => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
        </div>

        {/* Building type */}
        <div className="field field-wide">
          <label>Occupancy / Building Type
            <span className="nec-ref">Table 220.12</span>
          </label>
          <select
            value={buildingType}
            onChange={e => onChange('buildingType', e.target.value)}
          >
            {BUILDING_TYPES.map(b => (
              <option key={b.key} value={b.key}>{b.label}</option>
            ))}
          </select>
        </div>

        {/* Area */}
        <div className="field">
          <label>Area
            <span className="nec-ref">220.12</span>
          </label>
          <div className="input-group">
            <input
              type="number"
              min="0"
              step="1"
              placeholder="0"
              value={area}
              onChange={e => onChange('area', e.target.value)}
            />
            <select
              value={areaUnit}
              onChange={e => onChange('areaUnit', e.target.value)}
            >
              <option value="sqft">ft²</option>
              <option value="sqm">m²</option>
            </select>
          </div>
        </div>

        {/* Phase configuration */}
        <div className="field field-wide">
          <label>Service / Phase Configuration
            <span className="nec-ref">220.83</span>
          </label>
          <select
            value={phaseConfig}
            onChange={e => onChange('phaseConfig', e.target.value)}
          >
            {PHASE_CONFIGS.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        {/* Small appliance circuits */}
        <div className="field">
          <label>Small Appliance Circuits
            <span className="nec-ref">220.52(A)</span>
          </label>
          <select
            value={smallApplianceCircuits}
            onChange={e => onChange('smallApplianceCircuits', Number(e.target.value))}
          >
            {[2, 3, 4, 5].map(n => (
              <option key={n} value={n}>{n} circuits × 1,500 VA</option>
            ))}
          </select>
        </div>

        {/* Laundry */}
        <div className="field">
          <label>Laundry Circuit
            <span className="nec-ref">220.52(B)</span>
          </label>
          <select
            value={hasLaundry ? 'yes' : 'no'}
            onChange={e => onChange('hasLaundry', e.target.value === 'yes')}
          >
            <option value="yes">Yes — 1,500 VA</option>
            <option value="no">No laundry circuit</option>
          </select>
        </div>
      </div>
    </section>
  );
}

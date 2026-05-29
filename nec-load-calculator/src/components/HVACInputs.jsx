import { HVAC_COMPONENTS } from '../data/necTables.js';

const QTY_OPTIONS = [0, 1, 2, 3, 4, 5];

// Which HVAC components are "heating" vs "cooling"
const HEATING_KEYS = ['heating', 'heatPump', 'heatPumpCompressor', 'supplemental', 'spaceHeaters'];
const COOLING_KEYS = ['cooling', 'acCompressor'];
const SHARED_KEYS  = ['blower'];

export default function HVACInputs({ hvac, onChange }) {
  const renderRow = (key) => {
    const def = HVAC_COMPONENTS[key];
    const val = hvac[key] || { qty: 0, nameplate: 0 };
    return (
      <tr key={key}>
        <td>{def.label}</td>
        <td>
          <select
            value={val.qty}
            onChange={e => onChange(key, 'qty', Number(e.target.value))}
          >
            {QTY_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </td>
        <td>
          <input
            type="number"
            min="0"
            step="100"
            value={val.nameplate}
            onChange={e => onChange(key, 'nameplate', Number(e.target.value))}
          />
        </td>
        <td className="ref-cell">{def.necRef}</td>
      </tr>
    );
  };

  return (
    <section className="card">
      <h2 className="step-header">
        <span className="step-badge">Step 3</span>
        Heating &amp; Cooling (HVAC)
        <span className="nec-ref-inline">NEC 220.60</span>
      </h2>
      <p className="note">
        Per NEC 220.60, only the <strong>larger</strong> of the heating or cooling load is used.
        The blower motor is included in both and counted with whichever is larger.
      </p>

      <div className="hvac-grid">
        {/* Heating column */}
        <div className="hvac-col">
          <h3 className="hvac-col-heading heating-heading">Heating Loads</h3>
          <table className="appliance-table">
            <thead>
              <tr><th>Type</th><th>Qty</th><th>VA</th><th>Ref</th></tr>
            </thead>
            <tbody>
              {HEATING_KEYS.map(renderRow)}
            </tbody>
          </table>
        </div>

        {/* Cooling column */}
        <div className="hvac-col">
          <h3 className="hvac-col-heading cooling-heading">Cooling Loads</h3>
          <table className="appliance-table">
            <thead>
              <tr><th>Type</th><th>Qty</th><th>VA</th><th>Ref</th></tr>
            </thead>
            <tbody>
              {COOLING_KEYS.map(renderRow)}
            </tbody>
          </table>
        </div>
      </div>

      {/* Shared blower */}
      <div className="subsection">
        <h3>Shared Equipment</h3>
        <table className="appliance-table">
          <thead>
            <tr><th>Type</th><th>Qty</th><th>VA</th><th>Ref</th></tr>
          </thead>
          <tbody>
            {SHARED_KEYS.map(renderRow)}
          </tbody>
        </table>
      </div>
    </section>
  );
}

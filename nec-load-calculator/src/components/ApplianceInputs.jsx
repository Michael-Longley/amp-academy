import { DEFAULT_APPLIANCES } from '../data/necTables.js';

const QTY_OPTIONS = [0, 1, 2, 3, 4, 5];

export default function ApplianceInputs({ appliances, cordPlug, onChange, onCordPlugChange }) {
  return (
    <section className="card">
      <h2 className="step-header">
        <span className="step-badge">Step 2</span>
        Appliance Loads
      </h2>

      {/* Fastened in-place appliances */}
      <div className="subsection">
        <h3>Fastened-in-Place Appliances
          <span className="nec-ref">NEC 220.53</span>
        </h3>
        <p className="note">If 4 or more appliance units, a 75% demand factor applies (Standard Method).</p>

        <table className="appliance-table">
          <thead>
            <tr>
              <th>Appliance</th>
              <th>Qty / Unit</th>
              <th>Nameplate VA</th>
              <th>NEC Ref</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(DEFAULT_APPLIANCES).map(([key, def]) => {
              const appl = appliances[key] || { qty: 0, nameplate: def.nameplate };
              return (
                <tr key={key}>
                  <td>{def.label}</td>
                  <td>
                    <select
                      value={appl.qty}
                      onChange={e => onChange(key, 'qty', Number(e.target.value))}
                    >
                      {QTY_OPTIONS.map(n => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      step="50"
                      value={appl.nameplate}
                      onChange={e => onChange(key, 'nameplate', Number(e.target.value))}
                    />
                  </td>
                  <td className="ref-cell">{def.necRef}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Cord & plug connected */}
      <div className="subsection">
        <h3>Cord-and-Plug Connected Equipment</h3>

        {/* Range */}
        <table className="appliance-table">
          <thead>
            <tr>
              <th>Equipment</th>
              <th>Qty / Unit</th>
              <th>Nameplate VA</th>
              <th>NEC Ref</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Electric Range / Cooktop</td>
              <td>
                <select
                  value={cordPlug.range.qty}
                  onChange={e => onCordPlugChange('range', 'qty', Number(e.target.value))}
                >
                  {QTY_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={cordPlug.range.nameplateVA}
                  onChange={e => onCordPlugChange('range', 'nameplateVA', Number(e.target.value))}
                />
              </td>
              <td className="ref-cell">220.55</td>
            </tr>
            <tr>
              <td>Electric Dryer</td>
              <td>
                <select
                  value={cordPlug.dryer.qty}
                  onChange={e => onCordPlugChange('dryer', 'qty', Number(e.target.value))}
                >
                  {QTY_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  step="500"
                  value={cordPlug.dryer.nameplateVA}
                  onChange={e => onCordPlugChange('dryer', 'nameplateVA', Number(e.target.value))}
                />
              </td>
              <td className="ref-cell">220.54</td>
            </tr>
          </tbody>
        </table>
        <p className="note">
          Range: demand per Table 220.55 (Standard) or full nameplate (Optional).
          Dryer: minimum 5,000 VA per dryer (Standard) or full nameplate (Optional).
        </p>
      </div>
    </section>
  );
}

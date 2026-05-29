const QTY_OPTIONS = [0, 1, 2, 3, 4, 5];

const LOAD_DEFS = [
  { key: 'continuous',  label: 'Continuous Loads',       necRef: '210.19(A)(1)' },
  { key: 'combination', label: 'Combination Load',        necRef: '220.14'       },
  { key: 'specific',    label: 'Specific Appliance Load', necRef: '220.14'       },
  { key: 'other',       label: 'Other Load',              necRef: '220.14'       },
];

export default function OtherLoads({ otherLoads, onChange }) {
  return (
    <section className="card">
      <h2 className="step-header">
        <span className="step-badge">Step 4</span>
        Continuous &amp; Other Loads
      </h2>
      <p className="note">
        Continuous loads run for 3+ hours. Note: the 125% sizing factor applies to conductor
        and overcurrent device sizing, not to the load calculation total.
      </p>

      <table className="appliance-table">
        <thead>
          <tr>
            <th>Load Type</th>
            <th>Qty / Unit</th>
            <th>Nameplate VA</th>
            <th>NEC Ref</th>
          </tr>
        </thead>
        <tbody>
          {LOAD_DEFS.map(({ key, label, necRef }) => {
            const load = otherLoads[key] || { qty: 0, nameplate: 0 };
            return (
              <tr key={key}>
                <td>{label}</td>
                <td>
                  <select
                    value={load.qty}
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
                    value={load.nameplate}
                    onChange={e => onChange(key, 'nameplate', Number(e.target.value))}
                  />
                </td>
                <td className="ref-cell">{necRef}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

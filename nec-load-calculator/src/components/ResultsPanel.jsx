import { NEC_YEAR_NOTES } from '../data/necTables.js';

function va(n) {
  if (!n && n !== 0) return '—';
  return n.toLocaleString() + ' VA';
}
function pct(n) {
  return (n * 100).toFixed(0) + '%';
}

function Row({ label, value, sub, highlight, indent }) {
  return (
    <tr className={[highlight ? 'row-highlight' : '', indent ? 'row-indent' : ''].join(' ')}>
      <td className="result-label">{label}</td>
      <td className="result-value">{value}</td>
      {sub !== undefined && <td className="result-sub">{sub}</td>}
    </tr>
  );
}

function Divider({ label }) {
  return (
    <tr className="row-divider">
      <td colSpan="3">{label}</td>
    </tr>
  );
}

export default function ResultsPanel({ result, necYear, method }) {
  if (!result) return null;

  const note = NEC_YEAR_NOTES[necYear];
  const isOptional = method === 'optional';
  const ob = result.optionalBreakdown;
  const isDwelling = result.buildingType === 'dwelling';

  return (
    <section className="card results-card">
      <h2 className="step-header results-header">
        Live Results
        <span className="results-badge">
          {necYear} NEC — {isOptional ? 'Optional' : 'Standard'} Method
        </span>
      </h2>

      <table className="results-table">
        <tbody>
          {/* ── Lighting & Circuits ─────────────────────────────────── */}
          <Divider label="General Lighting & Branch Circuits" />
          <Row label="General Lighting (Table 220.12)" value={va(result.lightingVA)} />
          <Row label="Small Appliance Circuits (220.52A)" value={va(result.smallApplianceVA)} />
          <Row label="Laundry Circuit (220.52B)"          value={va(result.laundryVA)} />
          <Row label="Subtotal" value={va(result.lightingTotal)} highlight />

          {/* ── Fastened Appliances ─────────────────────────────────── */}
          <Divider label="Fastened-in-Place Appliances (220.53)" />
          <Row label="Gross nameplate total" value={va(result.fastenedSubtotal)} />
          {!isOptional && (
            <Row
              label={`Demand factor applied (${pct(result.fastenedDemandFactor)})`}
              value={result.fastenedDemandFactor < 1 ? '× 75%' : '× 100%'}
            />
          )}
          <Row label="Fastened appliances total" value={va(result.fastenedTotal)} highlight />

          {/* ── Cord & Plug ─────────────────────────────────────────── */}
          <Divider label="Cord-and-Plug Connected Equipment" />
          <Row label="Electric Range (Table 220.55)" value={va(result.rangeVA)} />
          <Row label="Electric Dryer (220.54)"        value={va(result.dryerVA)} />
          <Row label="Cord-and-plug total"             value={va(result.cordPlugTotal)} highlight />

          {/* ── HVAC ────────────────────────────────────────────────── */}
          <Divider label="Heating or Cooling — Larger Value Only (220.60)" />
          <Row label="Heating side total" value={va(result.hvacHeatingTotal)} />
          <Row label="Cooling side total" value={va(result.hvacCoolingTotal)} />
          <Row
            label={`HVAC load used (${result.hvacUsedFor})`}
            value={va(result.hvacTotal)}
            highlight
          />

          {/* ── Other Loads ─────────────────────────────────────────── */}
          <Divider label="Other Loads (220.14)" />
          <Row label="Continuous &amp; other loads" value={va(result.continuousVA)} highlight />

          {/* ── Optional Method Breakdown ───────────────────────────── */}
          {isOptional && ob && isDwelling && result.units <= 2 && (
            <>
              <Divider label="Optional Method Demand (220.82B) — 1–2 Units" />
              <Row label="Base load (all loads before demand)" value={va(ob.baseLoad)} />
              <Row indent label={`First 10,000 VA @ 100%`}    value={va(ob.first10k)} />
              <Row indent label={`Remainder @ 40%`}            value={va(ob.remainder40)} />
              <Row label="Demand-adjusted load"               value={va(ob.demandLoad)} highlight />
              <Row label="+ HVAC at 100%"                     value={va(ob.hvac)} />
            </>
          )}

          {isOptional && ob && isDwelling && result.units >= 3 && (
            <>
              <Divider label={`Optional Method Demand (220.82B) — ${result.units} Units`} />
              <Row label="All loads before demand factor"        value={va(ob.allLoads)} />
              <Row label={`Demand factor (${pct(ob.demandFactor)})`} value={`× ${pct(ob.demandFactor)}`} />
            </>
          )}

          {/* ── Final ───────────────────────────────────────────────── */}
          <tr className="row-final">
            <td className="result-label">FINAL CALCULATED LOAD</td>
            <td className="result-value final-va">{va(result.finalLoadVA)}</td>
            <td className="result-sub final-amps">{result.finalAmps} A @ 240V</td>
          </tr>
        </tbody>
      </table>

      {/* NEC Year Notes */}
      {note && (
        <div className="year-notes">
          <p>{note.optionalMethodNote}</p>
          {note.evNote && <p className="ev-note">{note.evNote}</p>}
        </div>
      )}
    </section>
  );
}

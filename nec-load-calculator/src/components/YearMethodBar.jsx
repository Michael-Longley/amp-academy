import { NEC_YEARS } from '../data/necTables.js';

export default function YearMethodBar({ necYear, method, onChange }) {
  return (
    <header className="year-method-bar">
      <div className="bar-brand">
        <span className="bar-title">Amp Academy - Load Calculator</span>
        <span className="bar-subtitle">Article 220 — Dwelling Unit Service & Feeder Loads</span>
      </div>
      <div className="bar-controls">
        <label className="bar-label">
          NEC Year
          <select
            value={necYear}
            onChange={e => onChange('necYear', Number(e.target.value))}
          >
            {NEC_YEARS.map(yr => (
              <option key={yr} value={yr}>{yr} NEC</option>
            ))}
          </select>
        </label>
        <label className="bar-label">
          Method
          <select
            value={method}
            onChange={e => onChange('method', e.target.value)}
          >
            <option value="standard">Standard Method</option>
            <option value="optional">Optional Method</option>
          </select>
        </label>
      </div>
    </header>
  );
}

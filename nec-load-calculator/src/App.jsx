import { useState, useMemo } from 'react';
import YearMethodBar   from './components/YearMethodBar.jsx';
import BuildingConfig  from './components/BuildingConfig.jsx';
import ApplianceInputs from './components/ApplianceInputs.jsx';
import HVACInputs      from './components/HVACInputs.jsx';
import OtherLoads      from './components/OtherLoads.jsx';
import ResultsPanel    from './components/ResultsPanel.jsx';
import { calculateLoad, parseUnits } from './engine/calculator.js';
import './App.css';

const DEFAULT_STATE = {
  necYear: 2023,
  method: 'standard',

  building: {
    units: '1 unit',
    buildingType: 'dwelling',
    area: '',
    areaUnit: 'sqft',
    phaseConfig: '1-Phase, 3-Wire 120/240 V',
    smallApplianceCircuits: 2,
    hasLaundry: true,
  },

  appliances: {
    disposal:      { qty: 0, nameplate: 100  },
    waterHeater:   { qty: 0, nameplate: 4500 },
    compactor:     { qty: 0, nameplate: 1200 },
    centralVacuum: { qty: 0, nameplate: 840  },
    dishwasher:    { qty: 0, nameplate: 1200 },
  },

  cordPlug: {
    range: { qty: 0, nameplateVA: 12000 },
    dryer: { qty: 0, nameplateVA: 6000  },
  },

  hvac: {
    heating:            { qty: 0, nameplate: 0 },
    cooling:            { qty: 0, nameplate: 0 },
    blower:             { qty: 0, nameplate: 0 },
    acCompressor:       { qty: 0, nameplate: 0 },
    heatPump:           { qty: 0, nameplate: 0 },
    heatPumpCompressor: { qty: 0, nameplate: 0 },
    supplemental:       { qty: 0, nameplate: 0 },
    spaceHeaters:       { qty: 0, nameplate: 0 },
  },

  otherLoads: {
    continuous:  { qty: 0, nameplate: 0 },
    combination: { qty: 0, nameplate: 0 },
    specific:    { qty: 0, nameplate: 0 },
    other:       { qty: 0, nameplate: 0 },
  },
};

export default function App() {
  const [state, setState] = useState(DEFAULT_STATE);

  // Update helpers
  const setTop = (key, value) =>
    setState(s => ({ ...s, [key]: value }));

  const setBuilding = (key, value) =>
    setState(s => ({ ...s, building: { ...s.building, [key]: value } }));

  const setAppliance = (applKey, field, value) =>
    setState(s => ({
      ...s,
      appliances: {
        ...s.appliances,
        [applKey]: { ...s.appliances[applKey], [field]: value },
      },
    }));

  const setCordPlug = (type, field, value) =>
    setState(s => ({
      ...s,
      cordPlug: {
        ...s.cordPlug,
        [type]: { ...s.cordPlug[type], [field]: value },
      },
    }));

  const setHVAC = (comp, field, value) =>
    setState(s => ({
      ...s,
      hvac: {
        ...s.hvac,
        [comp]: { ...s.hvac[comp], [field]: value },
      },
    }));

  const setOtherLoad = (key, field, value) =>
    setState(s => ({
      ...s,
      otherLoads: {
        ...s.otherLoads,
        [key]: { ...s.otherLoads[key], [field]: value },
      },
    }));

  // Live calculation
  const result = useMemo(() => {
    const { building, appliances, cordPlug, hvac, otherLoads, method } = state;
    const units = parseUnits(building.units);

    return calculateLoad({
      buildingType:           building.buildingType,
      area:                   Number(building.area) || 0,
      areaUnit:               building.areaUnit,
      units,
      method,
      smallApplianceCircuits: building.smallApplianceCircuits,
      hasLaundry:             building.hasLaundry,

      fastenedAppliances: Object.values(appliances).map(a => ({
        qty:       a.qty,
        nameplate: a.nameplate,
      })),

      range: cordPlug.range,
      dryer: cordPlug.dryer,

      hvacInputs: hvac,

      otherLoads: Object.values(otherLoads).map(l => ({
        qty:       l.qty,
        nameplate: l.nameplate,
      })),
    });
  }, [state]);

  return (
    <div className="app-layout">
      <YearMethodBar
        necYear={state.necYear}
        method={state.method}
        onChange={(key, val) => setTop(key, val)}
      />

      <div className="content-area">
        <div className="inputs-col">
          <BuildingConfig
            building={state.building}
            onChange={setBuilding}
          />
          <ApplianceInputs
            appliances={state.appliances}
            cordPlug={state.cordPlug}
            onChange={setAppliance}
            onCordPlugChange={setCordPlug}
          />
          <HVACInputs
            hvac={state.hvac}
            onChange={setHVAC}
          />
          <OtherLoads
            otherLoads={state.otherLoads}
            onChange={setOtherLoad}
          />
        </div>

        <div className="results-col">
          <ResultsPanel
            result={result}
            necYear={state.necYear}
            method={state.method}
          />
        </div>
      </div>
    </div>
  );
}

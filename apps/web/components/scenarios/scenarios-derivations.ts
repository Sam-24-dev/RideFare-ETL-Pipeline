import type { ModelLabPayload } from "../../lib/data/loaders";
import { formatCurrency } from "../../lib/formatters";

type ScenarioControls = ModelLabPayload["simulator"]["controls"];
type ScenarioGridRow = ModelLabPayload["simulator"]["grid"][number];

export type ScenarioSelection = {
  source: string;
  destination: string;
  cabType: string;
  timeBlock: string;
  weatherProfile: string;
  surgeMultiplier: number;
};

export type ScenarioDraftState = {
  referenceDistanceFactor: number;
  selection: ScenarioSelection;
  options: {
    sources: string[];
    destinations: string[];
    cabTypes: string[];
    timeBlocks: ScenarioControls["time_blocks"];
    weatherProfiles: ScenarioControls["weather_profiles"];
    surgeLevels: number[];
  };
};

export type ScenarioInfluenceFactor = {
  title: "Distancia" | "Demanda" | "Clima" | "Hora y ritmo urbano";
  body: string;
};

export type ScenarioEditorial = {
  heading: "Cómo leer este escenario";
  columns: [string, string];
};

export type ScenarioExperience = ScenarioDraftState & {
  selectedScenario: ScenarioGridRow | null;
  baseScenario: ScenarioGridRow | null;
  routeLabel: string;
  timeLabel: string;
  weatherLabel: string;
  demandLabel: string;
  deltaAbs: number;
  deltaPct: number;
  comparisonMax: number;
  factors: ScenarioInfluenceFactor[];
  editorial: ScenarioEditorial;
};

export function hasPendingScenarioChanges(
  appliedSelection: ScenarioSelection,
  draftSelection: ScenarioSelection,
): boolean {
  return (
    appliedSelection.source !== draftSelection.source ||
    appliedSelection.destination !== draftSelection.destination ||
    appliedSelection.cabType !== draftSelection.cabType ||
    appliedSelection.timeBlock !== draftSelection.timeBlock ||
    appliedSelection.weatherProfile !== draftSelection.weatherProfile ||
    appliedSelection.surgeMultiplier !== draftSelection.surgeMultiplier
  );
}

const DEFAULT_SIGNAL_ORDER = [
  "Distancia",
  "Demanda",
  "Clima",
  "Hora y ritmo urbano",
] as const;

export function pickDefaultScenarioSelection(payload: ModelLabPayload): ScenarioSelection {
  const referenceDistanceFactor = getReferenceDistanceFactor(payload.simulator.controls);
  const referenceRows = getReferenceRows(payload.simulator.grid, referenceDistanceFactor);

  const candidates = referenceRows.filter(
    (row) => row.surge_multiplier > 1 && row.weather_profile !== "despejado",
  );
  const rankedRows = (candidates.length > 0 ? candidates : referenceRows).sort(compareScenarioRows);
  const defaultRow = rankedRows[0] ?? referenceRows[0];

  if (defaultRow) {
    return {
      source: defaultRow.source,
      destination: defaultRow.destination,
      cabType: defaultRow.cab_type,
      timeBlock: defaultRow.time_block,
      weatherProfile: defaultRow.weather_profile,
      surgeMultiplier: defaultRow.surge_multiplier,
    };
  }

  const controls = payload.simulator.controls;
  return {
    source: controls.sources[0] ?? "",
    destination: controls.destinations_by_source[controls.sources[0] ?? ""]?.[0] ?? "",
    cabType: controls.cab_types[0] ?? "",
    timeBlock: controls.time_blocks[0]?.id ?? "",
    weatherProfile: controls.weather_profiles[0]?.id ?? "",
    surgeMultiplier: controls.surge_levels[0] ?? 1,
  };
}

export function resolveScenarioDraft(
  payload: ModelLabPayload,
  partialSelection: Partial<ScenarioSelection> = {},
): ScenarioDraftState {
  const controls = payload.simulator.controls;
  const referenceDistanceFactor = getReferenceDistanceFactor(controls);
  const referenceRows = getReferenceRows(payload.simulator.grid, referenceDistanceFactor);

  const sources = controls.sources.filter((source) =>
    referenceRows.some((row) => row.source === source),
  );
  const source = pickStringOption(partialSelection.source, sources);

  const sourceRows = referenceRows.filter((row) => row.source === source);
  const destinations = (controls.destinations_by_source[source] ?? []).filter((destination) =>
    sourceRows.some((row) => row.destination === destination),
  );
  const destination = pickStringOption(partialSelection.destination, destinations);

  const routeRows = sourceRows.filter((row) => row.destination === destination);
  const cabTypes = controls.cab_types.filter((cabType) =>
    routeRows.some((row) => row.cab_type === cabType),
  );
  const cabType = pickStringOption(partialSelection.cabType, cabTypes);

  const serviceRows = routeRows.filter((row) => row.cab_type === cabType);
  const timeBlocks = controls.time_blocks.filter((timeBlock) =>
    serviceRows.some((row) => row.time_block === timeBlock.id),
  );
  const timeBlock = pickStringOption(
    partialSelection.timeBlock,
    timeBlocks.map((item) => item.id),
  );

  const timeRows = serviceRows.filter((row) => row.time_block === timeBlock);
  const weatherProfiles = controls.weather_profiles.filter((profile) =>
    timeRows.some((row) => row.weather_profile === profile.id),
  );
  const weatherProfile = pickStringOption(
    partialSelection.weatherProfile,
    weatherProfiles.map((item) => item.id),
  );

  const weatherRows = timeRows.filter((row) => row.weather_profile === weatherProfile);
  const surgeLevels = controls.surge_levels.filter((level) =>
    weatherRows.some((row) => row.surge_multiplier === level),
  );
  const surgeMultiplier = pickNumberOption(partialSelection.surgeMultiplier, surgeLevels);

  return {
    referenceDistanceFactor,
    selection: {
      source,
      destination,
      cabType,
      timeBlock,
      weatherProfile,
      surgeMultiplier,
    },
    options: {
      sources,
      destinations,
      cabTypes,
      timeBlocks,
      weatherProfiles,
      surgeLevels,
    },
  };
}

export function findScenarioBySelection(
  payload: ModelLabPayload,
  selection: ScenarioSelection,
): ScenarioGridRow | null {
  const referenceDistanceFactor = getReferenceDistanceFactor(payload.simulator.controls);

  return (
    payload.simulator.grid.find(
      (row) =>
        nearlyEqual(row.distance_factor, referenceDistanceFactor) &&
        row.source === selection.source &&
        row.destination === selection.destination &&
        row.cab_type === selection.cabType &&
        row.time_block === selection.timeBlock &&
        row.weather_profile === selection.weatherProfile &&
        row.surge_multiplier === selection.surgeMultiplier,
    ) ?? null
  );
}

export function findBaseScenario(
  payload: ModelLabPayload,
  selection: ScenarioSelection,
): ScenarioGridRow | null {
  const selectedScenario = findScenarioBySelection(payload, selection);
  if (!selectedScenario) {
    return null;
  }

  const referenceDistanceFactor = getReferenceDistanceFactor(payload.simulator.controls);
  const comparableRows = getReferenceRows(payload.simulator.grid, referenceDistanceFactor).filter(
    (row) =>
      row.source === selection.source &&
      row.destination === selection.destination &&
      row.cab_type === selection.cabType,
  );
  const referenceTimeBlock = pickReferenceTimeBlock(comparableRows, selection.timeBlock);
  const referenceTimeRows = comparableRows.filter((row) => row.time_block === referenceTimeBlock);

  return (
    referenceTimeRows.find(
      (row) => row.weather_profile === "despejado" && row.surge_multiplier === 1,
    ) ??
    referenceTimeRows.find(
      (row) =>
        row.weather_profile === selection.weatherProfile && row.surge_multiplier === 1,
    ) ??
    referenceTimeRows.find(
      (row) =>
        row.weather_profile === "despejado" &&
        row.surge_multiplier === selection.surgeMultiplier,
    ) ??
    comparableRows.find(
      (row) => row.weather_profile === "despejado" && row.surge_multiplier === 1,
    ) ??
    comparableRows.find(
      (row) =>
        row.weather_profile === selection.weatherProfile && row.surge_multiplier === 1,
    ) ??
    comparableRows.find(
      (row) =>
        row.weather_profile === "despejado" &&
        row.surge_multiplier === selection.surgeMultiplier,
    ) ??
    selectedScenario
  );
}

export function buildScenarioExperience(
  payload: ModelLabPayload,
  selection: ScenarioSelection,
): ScenarioExperience {
  const draft = resolveScenarioDraft(payload, selection);
  const selectedScenario = findScenarioBySelection(payload, draft.selection);
  const baseScenario = selectedScenario ? findBaseScenario(payload, draft.selection) : null;
  const deltaAbs =
    selectedScenario && baseScenario
      ? selectedScenario.predicted_price - baseScenario.predicted_price
      : 0;
  const deltaPct =
    selectedScenario && baseScenario && baseScenario.predicted_price > 0
      ? deltaAbs / baseScenario.predicted_price
      : 0;
  const comparisonMax = Math.max(
    selectedScenario?.predicted_price ?? 0,
    baseScenario?.predicted_price ?? 0,
    1,
  );

  const routeLabel = selectedScenario
    ? `${selectedScenario.source} → ${selectedScenario.destination}`
    : "Sin escenario visible";
  const timeLabel = getTimeLabel(payload.simulator.controls, draft.selection.timeBlock);
  const weatherProfile = payload.simulator.controls.weather_profiles.find(
    (profile) => profile.id === draft.selection.weatherProfile,
  );
  const weatherLabel = weatherProfile?.label ?? "Sin clima visible";
  const demandLabel = getDemandLabel(draft.selection.surgeMultiplier).toLowerCase();
  const factors = buildScenarioFactors(payload, draft.selection, selectedScenario, baseScenario);
  const editorial = buildScenarioEditorial(
    routeLabel,
    timeLabel,
    weatherLabel,
    demandLabel,
    deltaAbs,
    deltaPct,
    selectedScenario,
    baseScenario,
    factors[0]?.title ?? "Demanda",
  );

  return {
    ...draft,
    selectedScenario,
    baseScenario,
    routeLabel,
    timeLabel,
    weatherLabel,
    demandLabel,
    deltaAbs,
    deltaPct,
    comparisonMax,
    factors,
    editorial,
  };
}

function buildScenarioFactors(
  payload: ModelLabPayload,
  selection: ScenarioSelection,
  selectedScenario: ScenarioGridRow | null,
  baseScenario: ScenarioGridRow | null,
): ScenarioInfluenceFactor[] {
  const weatherProfile = payload.simulator.controls.weather_profiles.find(
    (profile) => profile.id === selection.weatherProfile,
  );
  const orderedSignals = getOrderedSignals(payload, selection, selectedScenario, baseScenario);

  const factorMap: Record<ScenarioInfluenceFactor["title"], ScenarioInfluenceFactor> = {
    Distancia: {
      title: "Distancia",
      body: selectedScenario
        ? `Influencia estable. Trayecto de ${selectedScenario.route_distance_median.toFixed(1)} mi.`
        : "Influencia estable. El trayecto visible marca la referencia del precio.",
    },
    Demanda: {
      title: "Demanda",
      body: `El precio responde a una presión de demanda ${getDemandLabel(selection.surgeMultiplier).toLowerCase()}.`,
    },
    Clima: {
      title: "Clima",
      body: weatherProfile
        ? `${weatherProfile.label}. ${weatherProfile.description}`
        : "Sin perfil climático visible para esta lectura.",
    },
    "Hora y ritmo urbano": {
      title: "Hora y ritmo urbano",
      body: getTimeBlockNarrative(selection.timeBlock),
    },
  };

  return orderedSignals.map((signal) => factorMap[signal]);
}

function buildScenarioEditorial(
  routeLabel: string,
  timeLabel: string,
  weatherLabel: string,
  demandLabel: string,
  deltaAbs: number,
  deltaPct: number,
  selectedScenario: ScenarioGridRow | null,
  baseScenario: ScenarioGridRow | null,
  dominantFactor: string,
): ScenarioEditorial {
  if (!selectedScenario || !baseScenario) {
    return {
      heading: "Cómo leer este escenario",
      columns: [
        "No hay una lectura exportada para esta combinación. Vuelve a la referencia o prueba otra ruta, clima o franja horaria.",
        "Cuando exista un escenario comparable, aquí verás qué cambia frente a la referencia y qué margen esperado acompaña esa lectura.",
      ],
    };
  }

  const rangeLabel = `${formatCurrency(selectedScenario.price_band_low)} — ${formatCurrency(selectedScenario.price_band_high)}`;
  const deltaAdverb =
    deltaPct >= 0.15
      ? "abre una diferencia clara"
      : deltaPct >= 0.05
        ? "sube de forma moderada"
        : "casi no cambia";
  const paragraphOne =
    deltaPct >= 0.15
      ? `Frente a la referencia de ${formatCurrency(baseScenario.predicted_price)}, este escenario ${deltaAdverb} en ${routeLabel}. La combinación de ${timeLabel.toLowerCase()}, clima ${weatherLabel.toLowerCase()} y demanda ${demandLabel} lleva la lectura hasta ${formatCurrency(selectedScenario.predicted_price)}.`
      : deltaPct >= 0.05
        ? `Frente a la referencia de ${formatCurrency(baseScenario.predicted_price)}, este escenario ${deltaAdverb} en ${routeLabel}. La franja ${timeLabel} y el perfil ${weatherLabel.toLowerCase()} empujan la tarifa hacia ${formatCurrency(selectedScenario.predicted_price)} con una demanda ${demandLabel}.`
        : `En ${routeLabel}, este escenario ${deltaAdverb} frente a la referencia de ${formatCurrency(baseScenario.predicted_price)}. En ${timeLabel.toLowerCase()}, con clima ${weatherLabel.toLowerCase()} y demanda ${demandLabel}, la lectura sigue cerca de ${formatCurrency(selectedScenario.predicted_price)}.`;
  const paragraphTwo = `La señal que más ordena esta lectura es ${getDominantFactorNarrative(
    dominantFactor,
  )}. El margen esperado de ${rangeLabel} acompaña esta combinación mientras comparas otra lectura del mismo trayecto.`;

  return {
    heading: "Cómo leer este escenario",
    columns: [paragraphOne, paragraphTwo],
  };
}

function getOrderedSignals(
  payload: ModelLabPayload,
  selection: ScenarioSelection,
  selectedScenario: ScenarioGridRow | null,
  baseScenario: ScenarioGridRow | null,
): ScenarioInfluenceFactor["title"][] {
  const contextualScores = buildContextualSignalScores(
    payload,
    selection,
    selectedScenario,
    baseScenario,
  );
  const globalScores = buildGlobalSignalScores(payload);

  return [...DEFAULT_SIGNAL_ORDER].sort(
    (left, right) =>
      (contextualScores[right] + (globalScores[right] ?? 0) * 0.28) -
        (contextualScores[left] + (globalScores[left] ?? 0) * 0.28) ||
      DEFAULT_SIGNAL_ORDER.indexOf(left) - DEFAULT_SIGNAL_ORDER.indexOf(right),
  );
}

function buildContextualSignalScores(
  payload: ModelLabPayload,
  selection: ScenarioSelection,
  selectedScenario: ScenarioGridRow | null,
  baseScenario: ScenarioGridRow | null,
): Record<ScenarioInfluenceFactor["title"], number> {
  const maxDistance = Math.max(
    ...payload.simulator.controls.route_catalog.map((route) => route.median_distance),
    1,
  );
  const deltaBoost =
    selectedScenario && baseScenario && baseScenario.predicted_price > 0
      ? Math.min(
          Math.abs(selectedScenario.predicted_price - baseScenario.predicted_price) /
            baseScenario.predicted_price,
          0.35,
        )
      : 0;
  const distanceScore = selectedScenario
    ? clampScore((selectedScenario.route_distance_median / maxDistance) * 0.72 + 0.12)
    : 0.2;
  const demandScore = clampScore(
    getDemandIntensity(selection.surgeMultiplier) * (0.68 + deltaBoost),
  );
  const climateScore = clampScore(
    getWeatherSeverity(payload.simulator.controls, selection.weatherProfile) *
      (0.58 + deltaBoost * 0.9),
  );
  const timeScore = clampScore(
    getTimeBlockIntensity(selection.timeBlock) * (0.42 + deltaBoost * 0.55) +
      (baseScenario && baseScenario.time_block !== selection.timeBlock ? 0.08 : 0),
  );

  return {
    Distancia: distanceScore,
    Demanda: demandScore,
    Clima: climateScore,
    "Hora y ritmo urbano": timeScore,
  };
}

function buildGlobalSignalScores(
  payload: ModelLabPayload,
): Partial<Record<ScenarioInfluenceFactor["title"], number>> {
  const groupedScores = new Map<ScenarioInfluenceFactor["title"], number>();

  for (const item of payload.featureImportance) {
    if (item.importance > 0) {
      const label = normalizeSignalTitle(mapScenarioSignal(item.feature));
      groupedScores.set(label, (groupedScores.get(label) ?? 0) + item.importance);
    }
  }

  if (groupedScores.size === 0) {
    for (const item of payload.shapSummary.global_importance) {
      if (item.mean_abs_shap > 0) {
        const label = normalizeSignalTitle(mapScenarioSignal(item.feature));
        groupedScores.set(label, (groupedScores.get(label) ?? 0) + item.mean_abs_shap);
      }
    }
  }

  if (groupedScores.size === 0) {
    return {};
  }

  const maxScore = Math.max(...groupedScores.values(), 1);
  const normalized: Partial<Record<ScenarioInfluenceFactor["title"], number>> = {};
  for (const [label, score] of groupedScores.entries()) {
    normalized[label] = score / maxScore;
  }
  return normalized;
}

function mapScenarioSignal(feature: string): string {
  const normalizedFeature = feature.toLowerCase();

  if (normalizedFeature.includes("distance") || normalizedFeature.includes("base_fare")) {
    return "Distancia";
  }

  if (normalizedFeature.includes("surge") || normalizedFeature.includes("demand")) {
    return "Demanda";
  }

  if (
    normalizedFeature.includes("temp") ||
    normalizedFeature.includes("cloud") ||
    normalizedFeature.includes("pressure") ||
    normalizedFeature.includes("rain") ||
    normalizedFeature.includes("humidity") ||
    normalizedFeature.includes("wind") ||
    normalizedFeature.includes("weather")
  ) {
    return "Clima";
  }

  if (
    normalizedFeature.includes("hour") ||
    normalizedFeature.includes("traffic") ||
    normalizedFeature.includes("day_of_week") ||
    normalizedFeature.includes("congestion")
  ) {
    return "Hora y ritmo urbano";
  }

  return "Hora y ritmo urbano";
}

function normalizeSignalTitle(label: string): ScenarioInfluenceFactor["title"] {
  switch (label) {
    case "Distancia":
      return "Distancia";
    case "Demanda":
      return "Demanda";
    case "Clima":
      return "Clima";
    default:
      return "Hora y ritmo urbano";
  }
}

function pickReferenceTimeBlock(
  comparableRows: ScenarioGridRow[],
  currentTimeBlock: string,
): string {
  const preferredOrder = ["tarde", "manana", "noche", "madrugada"];
  for (const preferredTimeBlock of preferredOrder) {
    if (comparableRows.some((row) => row.time_block === preferredTimeBlock)) {
      return preferredTimeBlock;
    }
  }

  return comparableRows.some((row) => row.time_block === currentTimeBlock)
    ? currentTimeBlock
    : (comparableRows[0]?.time_block ?? currentTimeBlock);
}

function getReferenceDistanceFactor(controls: ScenarioControls): number {
  return [...controls.distance_factors]
    .sort(
      (left, right) =>
        Math.abs(left.factor - 1) - Math.abs(right.factor - 1) || left.factor - right.factor,
    )[0]?.factor ?? 1;
}

function getReferenceRows(rows: ScenarioGridRow[], referenceDistanceFactor: number): ScenarioGridRow[] {
  return rows.filter((row) => nearlyEqual(row.distance_factor, referenceDistanceFactor));
}

function compareScenarioRows(left: ScenarioGridRow, right: ScenarioGridRow): number {
  return (
    right.predicted_price - left.predicted_price ||
    right.route_distance_median - left.route_distance_median ||
    right.surge_multiplier - left.surge_multiplier
  );
}

function pickStringOption(value: string | undefined, options: string[]): string {
  return value && options.includes(value) ? value : (options[0] ?? "");
}

function pickNumberOption(value: number | undefined, options: number[]): number {
  return typeof value === "number" && options.includes(value) ? value : (options[0] ?? 1);
}

function nearlyEqual(left: number, right: number): boolean {
  return Math.abs(left - right) < 0.0001;
}

function getTimeLabel(controls: ScenarioControls, timeBlockId: string): string {
  return controls.time_blocks.find((timeBlock) => timeBlock.id === timeBlockId)?.label ?? "Sin franja";
}

function getDemandLabel(surgeMultiplier: number): "Base" | "Alta" | "Pico" {
  if (surgeMultiplier >= 1.5) {
    return "Pico";
  }

  if (surgeMultiplier >= 1.25) {
    return "Alta";
  }

  return "Base";
}

function getDemandIntensity(surgeMultiplier: number): number {
  if (surgeMultiplier >= 1.5) {
    return 0.88;
  }

  if (surgeMultiplier >= 1.25) {
    return 0.54;
  }

  return 0.12;
}

function getWeatherSeverity(controls: ScenarioControls, weatherProfileId: string): number {
  const currentProfile = controls.weather_profiles.find((profile) => profile.id === weatherProfileId);
  if (!currentProfile) {
    return 0.2;
  }

  const maxClouds = Math.max(...controls.weather_profiles.map((profile) => profile.values.clouds), 1);
  const maxRain = Math.max(...controls.weather_profiles.map((profile) => profile.values.rain), 0.1);
  const maxHumidity = Math.max(
    ...controls.weather_profiles.map((profile) => profile.values.humidity),
    1,
  );
  const maxWind = Math.max(...controls.weather_profiles.map((profile) => profile.values.wind), 1);

  return clampScore(
    0.22 * (currentProfile.values.clouds / maxClouds) +
      0.36 * (currentProfile.values.rain / maxRain) +
      0.22 * (currentProfile.values.humidity / maxHumidity) +
      0.2 * (currentProfile.values.wind / maxWind),
  );
}

function getTimeBlockNarrative(timeBlockId: string): string {
  switch (timeBlockId) {
    case "madrugada":
      return "Ritmo urbano bajo y menor fricción.";
    case "manana":
      return "Actividad en ascenso y accesos más tensos.";
    case "tarde":
      return "Ventana más sensible a cambios de demanda.";
    case "noche":
      return "Cae la oferta y se amplía la incertidumbre del trayecto.";
    default:
      return "El ritmo urbano cambia la lectura del trayecto.";
  }
}

function getTimeBlockIntensity(timeBlockId: string): number {
  switch (timeBlockId) {
    case "madrugada":
      return 0.18;
    case "manana":
      return 0.34;
    case "tarde":
      return 0.46;
    case "noche":
      return 0.62;
    default:
      return 0.28;
  }
}

function getDominantFactorNarrative(factor: string): string {
  switch (factor) {
    case "Distancia":
      return "la distancia del trayecto";
    case "Demanda":
      return "la presión de demanda";
    case "Clima":
      return "el perfil climático";
    default:
      return "la franja y el ritmo urbano";
  }
}

function clampScore(value: number): number {
  return Math.max(0.06, Math.min(value, 1.2));
}

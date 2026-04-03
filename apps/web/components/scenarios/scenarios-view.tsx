"use client";

import { useState } from "react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ModelLabPayload } from "@/lib/data/loaders";
import { formatCurrency } from "@/lib/formatters";
import { cn } from "@/lib/utils";

import {
  buildScenarioExperience,
  hasPendingScenarioChanges,
  pickDefaultScenarioSelection,
  resolveScenarioDraft,
  type ScenarioSelection,
} from "./scenarios-derivations";

type ScenariosViewProps = {
  payload: ModelLabPayload;
};

export function ScenariosView({ payload }: ScenariosViewProps): React.ReactElement {
  const initialSelection = pickDefaultScenarioSelection(payload);
  const [draftSelection, setDraftSelection] = useState<ScenarioSelection>(initialSelection);
  const [appliedSelection, setAppliedSelection] = useState<ScenarioSelection>(initialSelection);

  const draft = resolveScenarioDraft(payload, draftSelection);
  const experience = buildScenarioExperience(payload, appliedSelection);
  const hasPendingChanges = hasPendingScenarioChanges(appliedSelection, draft.selection);

  const updateDraftSelection = (partialSelection: Partial<ScenarioSelection>) => {
    setDraftSelection((currentSelection) =>
      resolveScenarioDraft(payload, { ...currentSelection, ...partialSelection }).selection,
    );
  };

  const resetToReference = () => {
    const defaultSelection = pickDefaultScenarioSelection(payload);
    setDraftSelection(defaultSelection);
    setAppliedSelection(defaultSelection);
  };

  return (
    <div className="space-y-10 pb-6 md:space-y-12">
      <section className="relative overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-[color-mix(in_srgb,var(--color-piedra),white_32%)] shadow-[0_24px_80px_rgba(20,36,45,0.05)]">
        <div className="absolute inset-0 opacity-85">
          <ScenariosBackdrop />
        </div>
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.58)_0%,rgba(255,255,255,0.22)_100%)]" />

        <div className="relative z-10 px-6 py-10 sm:px-8 md:px-10 md:py-12 lg:px-12 lg:py-14">
          <div className="max-w-4xl space-y-4">
            <h1 className="max-w-[42rem] font-display text-5xl leading-[0.9] tracking-[-0.05em] text-[var(--color-obsidiana)] sm:text-6xl lg:text-[4.45rem]">
              Escenarios
            </h1>
            <p className="max-w-[44rem] text-base leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_8%)] md:text-lg">
              Explora cómo podría cambiar el precio cuando se mueven la demanda, el clima, la
              hora y el trayecto.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <aside className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_34%)] px-5 py-6 shadow-[0_20px_60px_rgba(20,36,45,0.04)] sm:px-6">
          <div className="space-y-6 border-l-2 border-[var(--color-cobre)] pl-5">
            <div className="space-y-2">
              <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-[var(--color-cobre-oscuro)]">
                Configuración del escenario
              </p>
              <h2 className="font-display text-[2rem] leading-[0.94] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                Mueve las variables y compara la lectura.
              </h2>
            </div>

            <div
              className={cn(
                "rounded-none border px-4 py-3 text-sm leading-7 transition-colors",
                hasPendingChanges
                  ? "border-[color-mix(in_srgb,var(--color-cobre),white_56%)] bg-[color-mix(in_srgb,var(--color-cobre),white_94%)] text-[var(--color-obsidiana)]"
                  : "border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_54%)] text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]",
              )}
              aria-live="polite"
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-cobre-oscuro)]">
                {hasPendingChanges ? "Cambios pendientes" : "Escenario aplicado"}
              </p>
              <p className="mt-1">
                {hasPendingChanges
                  ? "La lectura de la derecha sigue mostrando el escenario aplicado hasta que confirmes los cambios."
                  : "La lectura de la derecha ya refleja la combinación visible en esta mesa."}
              </p>
            </div>

            <div className="grid gap-4">
              <ScenarioSelectField
                label="Origen del trayecto"
                value={draft.selection.source}
                onValueChange={(value) => updateDraftSelection({ source: value })}
                options={draft.options.sources}
                screenReaderLabel="Seleccionar origen del trayecto"
              />

              <ScenarioSelectField
                label="Destino"
                value={draft.selection.destination}
                onValueChange={(value) => updateDraftSelection({ destination: value })}
                options={draft.options.destinations}
                screenReaderLabel="Seleccionar destino del trayecto"
              />

              <ScenarioSelectField
                label="Servicio"
                value={draft.selection.cabType}
                onValueChange={(value) => updateDraftSelection({ cabType: value })}
                options={draft.options.cabTypes}
                screenReaderLabel="Seleccionar servicio"
              />

              <ScenarioSelectField
                label="Franja horaria"
                value={draft.selection.timeBlock}
                onValueChange={(value) => updateDraftSelection({ timeBlock: value })}
                options={draft.options.timeBlocks.map((timeBlock) => ({
                  value: timeBlock.id,
                  label: timeBlock.label,
                }))}
                screenReaderLabel="Seleccionar franja horaria"
              />

              <ScenarioChoiceGroup
                label="Perfil climático"
                value={draft.selection.weatherProfile}
                onValueChange={(value) => updateDraftSelection({ weatherProfile: value })}
                options={draft.options.weatherProfiles.map((profile) => ({
                  value: profile.id,
                  label: profile.label,
                }))}
              />

              <ScenarioChoiceGroup
                label="Nivel de demanda"
                value={String(draft.selection.surgeMultiplier)}
                onValueChange={(value) =>
                  updateDraftSelection({ surgeMultiplier: Number(value) })
                }
                options={draft.options.surgeLevels.map((level) => ({
                  value: String(level),
                  label: getDemandLabel(level),
                }))}
              />

              <button
                type="button"
                disabled={!hasPendingChanges}
                className="inline-flex min-h-12 w-full items-center justify-center border border-[var(--color-cobre-oscuro)] bg-[var(--color-cobre-oscuro)] px-5 text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-piedra)] transition-colors duration-200 hover:bg-[color-mix(in_srgb,var(--color-cobre-oscuro),white_8%)] disabled:cursor-not-allowed disabled:border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] disabled:bg-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] disabled:text-[color-mix(in_srgb,var(--color-obsidiana),white_30%)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)]"
                aria-disabled={!hasPendingChanges}
                onClick={() => setAppliedSelection(draft.selection)}
              >
                Aplicar escenario
              </button>
            </div>
          </div>
        </aside>

        <div className="space-y-6">
          {experience.selectedScenario ? (
            <>
              <section className="overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-piedra),white_16%)_0%,white_100%)] shadow-[0_20px_60px_rgba(20,36,45,0.04)]">
                <div className="grid gap-0 lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]">
                  <div className="border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] px-6 py-6 sm:px-7 lg:border-b-0 lg:border-r">
                    <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-cobre-oscuro)]">
                      Tarifa estimada
                    </p>
                    <div className="mt-4 flex flex-wrap items-end gap-3">
                      <p className="font-display text-[4rem] leading-none tracking-[-0.07em] text-[var(--color-obsidiana)] sm:text-[4.8rem]">
                        {formatCurrency(experience.selectedScenario.predicted_price)}
                      </p>
                      <p className="pb-2 text-sm font-medium text-[var(--color-cobre-oscuro)]">
                        {formatSignedPercentage(experience.deltaPct)}
                      </p>
                    </div>
                    <p className="mt-4 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                      {experience.routeLabel} · {experience.selectedScenario.cab_type} ·{" "}
                      {experience.timeLabel}
                    </p>
                  </div>

                  <div className="grid gap-0 sm:grid-cols-2 lg:grid-cols-1">
                    <ResultMetaBlock
                      label="Rango esperado"
                      value={`${formatCurrency(experience.selectedScenario.price_band_low)} — ${formatCurrency(experience.selectedScenario.price_band_high)}`}
                      detail="Margen estimado para este escenario."
                    />
                    <ResultMetaBlock
                      label="Cambio frente a la referencia"
                      value={formatSignedCurrency(experience.deltaAbs)}
                      detail={getDeltaNarrative(experience.deltaPct)}
                    />
                  </div>
                </div>
              </section>

              <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)]">
                <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_36%)] px-6 py-6 shadow-[0_16px_46px_rgba(20,36,45,0.04)]">
                  <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-cobre-oscuro)]">
                    Comparativa de escenarios
                  </p>
                  <div className="mt-6 space-y-5">
                    <ComparisonRow
                      label="Base"
                      value={experience.baseScenario?.predicted_price ?? 0}
                      maxValue={experience.comparisonMax}
                      tone="neutral"
                    />
                    <ComparisonRow
                      label="Ajustado"
                      value={experience.selectedScenario.predicted_price}
                      maxValue={experience.comparisonMax}
                      tone="cobre"
                    />
                  </div>
                </div>

                <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_24%)] px-6 py-6 shadow-[0_16px_46px_rgba(20,36,45,0.04)]">
                  <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-cobre-oscuro)]">
                    Lectura rápida
                  </p>
                  <div className="mt-4 space-y-3 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                    <p>
                      Referencia:{" "}
                      <span className="font-medium text-[var(--color-obsidiana)]">
                        {formatCurrency(experience.baseScenario?.predicted_price ?? 0)}
                      </span>
                    </p>
                    <p>
                      Clima visible:{" "}
                      <span className="font-medium text-[var(--color-obsidiana)]">
                        {experience.weatherLabel}
                      </span>
                    </p>
                    <p>
                      Nivel de demanda:{" "}
                      <span className="font-medium capitalize text-[var(--color-obsidiana)]">
                        {experience.demandLabel}
                      </span>
                    </p>
                    <p>
                      Motor visible:{" "}
                      <span className="font-medium text-[var(--color-obsidiana)]">
                        {payload.simulator.controls.simulator_mode === "hybrid_fallback"
                          ? "Capa híbrida explicable"
                          : "Predicción directa"}
                      </span>
                    </p>
                  </div>
                </div>
              </section>

              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {experience.factors.map((factor, index) => (
                  <article
                    key={factor.title}
                    className={cn(
                      "border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_28%)] px-5 py-5 shadow-[0_14px_40px_rgba(20,36,45,0.03)]",
                      index === 0 &&
                        "border-[color-mix(in_srgb,var(--color-cobre),white_62%)] bg-[color-mix(in_srgb,var(--color-cobre),white_94%)]",
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "h-7 w-1 shrink-0 bg-[color-mix(in_srgb,var(--color-obsidiana),white_72%)]",
                          index === 0 && "bg-[var(--color-cobre)]",
                          factor.title === "Clima" && "bg-[var(--color-laguna)]",
                        )}
                      />
                      <h3 className="font-display text-[1.65rem] leading-none tracking-[-0.04em] text-[var(--color-obsidiana)]">
                        {factor.title}
                      </h3>
                    </div>
                    <p className="mt-4 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                      {factor.body}
                    </p>
                  </article>
                ))}
              </section>
            </>
          ) : (
            <section className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_34%)] px-6 py-8 shadow-[0_20px_60px_rgba(20,36,45,0.04)]">
              <div className="space-y-5">
                <div className="space-y-2">
                  <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-cobre-oscuro)]">
                    Sin coincidencias
                  </p>
                  <h2 className="font-display text-[2.1rem] leading-[0.95] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                    No hay un escenario exportado para esta combinación.
                  </h2>
                </div>
                <p className="max-w-2xl text-sm leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                  Vuelve a la referencia o cambia la ruta, el clima o la franja horaria para seguir
                  comparando.
                </p>
                <button
                  type="button"
                  className="inline-flex min-h-12 items-center justify-center border border-[var(--color-cobre-oscuro)] bg-[var(--color-cobre-oscuro)] px-5 text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-piedra)] transition-colors duration-200 hover:bg-[color-mix(in_srgb,var(--color-cobre-oscuro),white_8%)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)]"
                  onClick={resetToReference}
                >
                  Volver a la referencia
                </button>
              </div>
            </section>
          )}
        </div>
      </section>

      <section className="border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-8 md:pt-10">
        <div className="grid gap-6 lg:grid-cols-2 lg:gap-10">
          <div className="space-y-3">
            <h2 className="font-display text-[2.25rem] leading-[0.96] tracking-[-0.04em] text-[var(--color-obsidiana)] md:text-[2.65rem]">
              {experience.editorial.heading}
            </h2>
            <p className="text-base leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
              {experience.editorial.columns[0]}
            </p>
          </div>
          <div>
            <p className="text-base leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
              {experience.editorial.columns[1]}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

type ScenarioSelectFieldProps = {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  options: string[] | Array<{ value: string; label: string }>;
  screenReaderLabel: string;
};

function ScenarioSelectField({
  label,
  value,
  onValueChange,
  options,
  screenReaderLabel,
}: ScenarioSelectFieldProps): React.ReactElement {
  const normalizedOptions =
    typeof options[0] === "string"
      ? (options as string[]).map((option) => ({ value: option, label: option }))
      : (options as Array<{ value: string; label: string }>);

  return (
    <label className="space-y-2">
      <span className="text-[11px] font-medium uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_24%)]">
        {label}
      </span>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger
          className="h-12 rounded-none border-[color-mix(in_srgb,var(--color-obsidiana),white_82%)] bg-white/86 px-4"
          screenReaderLabel={screenReaderLabel}
        >
          <SelectValue placeholder={label} />
        </SelectTrigger>
        <SelectContent>
          {normalizedOptions.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}

type ScenarioChoiceGroupProps = {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
};

function ScenarioChoiceGroup({
  label,
  value,
  onValueChange,
  options,
}: ScenarioChoiceGroupProps): React.ReactElement {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_24%)]">
        {label}
      </p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const isActive = option.value === value;

          return (
            <button
              key={option.value}
              type="button"
              className={cn(
                "inline-flex min-h-11 items-center justify-center border px-4 text-[11px] font-medium uppercase tracking-[0.22em] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-piedra)]",
                isActive
                  ? "border-[var(--color-cobre-oscuro)] bg-[var(--color-cobre-oscuro)] text-[var(--color-piedra)]"
                  : "border-[color-mix(in_srgb,var(--color-obsidiana),white_82%)] bg-white/78 text-[var(--color-obsidiana)] hover:border-[var(--color-cobre)] hover:bg-white",
              )}
              aria-pressed={isActive}
              onClick={() => onValueChange(option.value)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

type ResultMetaBlockProps = {
  label: string;
  value: string;
  detail: string;
};

function ResultMetaBlock({ label, value, detail }: ResultMetaBlockProps): React.ReactElement {
  return (
    <div className="border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_90%)] px-6 py-5 last:border-b-0">
      <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_26%)]">
        {label}
      </p>
      <p className="mt-3 font-display text-[2rem] leading-none tracking-[-0.04em] text-[var(--color-obsidiana)]">
        {value}
      </p>
      <p className="mt-3 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_16%)]">
        {detail}
      </p>
    </div>
  );
}

type ComparisonRowProps = {
  label: string;
  value: number;
  maxValue: number;
  tone: "neutral" | "cobre";
};

function ComparisonRow({
  label,
  value,
  maxValue,
  tone,
}: ComparisonRowProps): React.ReactElement {
  const width = `${Math.max((value / maxValue) * 100, 8)}%`;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="font-medium uppercase tracking-[0.18em] text-[color-mix(in_srgb,var(--color-obsidiana),white_24%)]">
          {label}
        </span>
        <span className="font-display text-[1.9rem] leading-none tracking-[-0.04em] text-[var(--color-obsidiana)]">
          {formatCurrency(value)}
        </span>
      </div>
      <div className="h-12 bg-[color-mix(in_srgb,var(--color-obsidiana),white_94%)] p-2">
        <div
          className={cn(
            "h-full transition-[width] duration-300",
            tone === "cobre"
              ? "bg-[color-mix(in_srgb,var(--color-cobre),white_10%)]"
              : "bg-[color-mix(in_srgb,var(--color-obsidiana),white_72%)]",
          )}
          style={{ width }}
        />
      </div>
    </div>
  );
}

function formatSignedCurrency(value: number): string {
  if (value === 0) {
    return formatCurrency(0);
  }

  return `${value > 0 ? "+" : "-"}${formatCurrency(Math.abs(value))}`;
}

function formatSignedPercentage(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${sign}${Math.abs(value * 100).toFixed(1)}%`;
}

function getDeltaNarrative(deltaPct: number): string {
  if (deltaPct >= 0.15) {
    return "Abre una diferencia clara frente a la referencia.";
  }

  if (deltaPct >= 0.05) {
    return "Sube de forma moderada frente a la referencia.";
  }

  if (deltaPct <= -0.05) {
    return "Cae frente al escenario base.";
  }

  return "Casi no cambia frente al escenario base.";
}

function getDemandLabel(level: number): string {
  if (level >= 1.5) {
    return "Pico";
  }

  if (level >= 1.25) {
    return "Alta";
  }

  return "Base";
}

function ScenariosBackdrop(): React.ReactElement {
  return (
    <svg
      className="h-full w-full"
      viewBox="0 0 1200 520"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <pattern id="scenario-grid" width="28" height="28" patternUnits="userSpaceOnUse">
          <path d="M28 0H0V28" stroke="rgba(20,36,45,0.05)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="1200" height="520" fill="url(#scenario-grid)" />
      <path
        d="M0 360C118 336 210 340 316 378C401 409 489 417 584 394C664 375 744 334 828 334C905 334 963 365 1038 374C1097 381 1145 373 1200 346"
        stroke="rgba(178,115,64,0.12)"
        strokeWidth="16"
        strokeLinecap="round"
      />
      <path
        d="M0 406C118 382 210 386 316 424C401 455 489 463 584 440C664 421 744 380 828 380C905 380 963 411 1038 420C1097 427 1145 419 1200 392"
        stroke="rgba(178,115,64,0.08)"
        strokeWidth="16"
        strokeLinecap="round"
      />
    </svg>
  );
}

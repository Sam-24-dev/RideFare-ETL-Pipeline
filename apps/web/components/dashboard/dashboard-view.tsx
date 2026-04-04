"use client";

import { Fragment, useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import { CloudRain, RotateCcw, Thermometer, Waves } from "lucide-react";

import { EChartsChart } from "@/components/charts/echarts-chart";
import {
  DASHBOARD_ALL_VALUE,
  type DashboardFiltersState,
  buildClimateSummary,
  buildCorridorRankingFromVisibleSample,
  buildDashboardEmptyStateMessage,
  buildDashboardMetricSummary,
  buildEditorialNote,
  buildHourlyPatternMatrix,
  buildServiceBreakdown,
  buildTemporalPriceSeries,
  filterDashboardData,
  getDashboardServiceColor,
} from "@/components/dashboard/dashboard-derivations";
import { HomeActionLink } from "@/components/home/home-action-link";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DashboardPayload } from "@/lib/data/loaders";
import { formatCurrency, formatMultiplier } from "@/lib/formatters";

type DashboardViewProps = {
  payload: DashboardPayload;
};

type TemporalTooltipPoint = {
  value: number | null;
  rides: number;
  avgSurge: number | null;
  hourLabel: string;
  serviceLabel: string;
  isPeak: boolean;
};

type TemporalTooltipParam = {
  color?: string;
  data?: TemporalTooltipPoint;
};

type HourlyPatternSelection = {
  key: string;
  service: string;
  hour: string;
  rides: number;
  price: number;
  avgSurge: number | null;
  color: string;
};

type TooltipPositionSize = {
  contentSize: [number, number];
  viewSize: [number, number];
};

export function DashboardView({ payload }: DashboardViewProps): React.ReactElement {
  const [filters, setFilters] = useState<DashboardFiltersState>({
    source: DASHBOARD_ALL_VALUE,
    cabType: DASHBOARD_ALL_VALUE,
    timeWindow: DASHBOARD_ALL_VALUE,
  });
  const [selectedPatternCellKey, setSelectedPatternCellKey] = useState<string | null>(null);

  const derived = useMemo(() => {
    const filtered = filterDashboardData(payload, filters);

    return {
      filtered,
      metrics: buildDashboardMetricSummary(
        filtered.timeseries,
        filtered.routeBreakdown,
        filtered.selectedWindow,
      ),
      temporalSeries: buildTemporalPriceSeries(filtered.timeseries),
      hourlyPatterns: buildHourlyPatternMatrix(filtered.timeseries),
      corridorRanking: buildCorridorRankingFromVisibleSample(
        filtered.timeseries,
        filtered.routeBreakdown,
      ),
      serviceBreakdown: buildServiceBreakdown(filtered.timeseries, filtered.routeBreakdown),
      climateSummary: buildClimateSummary(filtered.weatherImpact),
    };
  }, [filters, payload]);

  const editorialNote = useMemo(
    () => buildEditorialNote(derived.corridorRanking, derived.climateSummary),
    [derived.climateSummary, derived.corridorRanking],
  );
  const selectedPatternCell = useMemo<HourlyPatternSelection | null>(() => {
    const visibleCells = derived.hourlyPatterns.services.flatMap((service, serviceIndex) =>
      service.cells
        .filter((cell) => cell.price !== null)
        .map((cell) => ({
          key: `${service.key}-${cell.hour}`,
          service: service.label,
          hour: cell.hour,
          rides: cell.rides,
          price: cell.price ?? 0,
          avgSurge: cell.avgSurge,
          color: getDashboardServiceColor(service.label, serviceIndex),
        })),
    );

    if (!visibleCells.length) {
      return null;
    }

    return visibleCells.find((cell) => cell.key === selectedPatternCellKey) ?? visibleCells[0]!;
  }, [derived.hourlyPatterns, selectedPatternCellKey]);

  const topRoute = derived.corridorRanking[0];
  const hasVisibleSample = derived.filtered.timeseries.length > 0;
  const emptyStateMessage = useMemo(
    () => buildDashboardEmptyStateMessage(payload, filters),
    [filters, payload],
  );

  const chartOption = useMemo<EChartsOption>(() => {
    const series = derived.temporalSeries.series;

    return {
      animationDuration: 350,
      grid: { left: 12, right: 18, top: 16, bottom: 32, containLabel: true },
      tooltip: {
        trigger: "axis",
        confine: true,
        backgroundColor: "rgba(15,20,24,0.92)",
        borderWidth: 0,
        textStyle: { color: "#f4efe7" },
        formatter: (params) => buildTemporalTooltip(params as TemporalTooltipParam[]),
        position: (point, _params, _dom, _rect, size) =>
          resolveTemporalTooltipPosition(point, size as TooltipPositionSize | undefined),
      },
      legend: {
        right: 0,
        top: 0,
        itemWidth: 10,
        itemHeight: 10,
        textStyle: {
          color: "#53616b",
          fontSize: 11,
        },
      },
      xAxis: {
        type: "category",
        data: derived.temporalSeries.labels,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: "rgba(21,36,45,0.12)" } },
        axisLabel: { color: "#53616b", margin: 12 },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: "#53616b",
          formatter: (value: number) => formatCurrency(value),
        },
        splitLine: {
          lineStyle: { color: "rgba(21,36,45,0.08)" },
        },
      },
      series: series.map((entry) => ({
        name: entry.label,
        type: "bar",
        data: entry.values,
        barWidth: 34,
        itemStyle: {
          color: entry.color,
          borderRadius: [0, 0, 0, 0],
          opacity: entry.color === "#1f5a7e" ? 0.9 : 0.78,
        },
      })),
    };
  }, [derived.temporalSeries.labels, derived.temporalSeries.series]);

  return (
    <div className="space-y-10 pb-6 md:space-y-12">
      <section className="relative overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-[color-mix(in_srgb,var(--color-piedra),white_28%)] shadow-[0_24px_80px_rgba(20,36,45,0.05)]">
        <div className="absolute inset-0 opacity-80">
          <DashboardHeaderBackdrop />
        </div>
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.42)_0%,rgba(255,255,255,0.12)_100%)]" />

        <div className="relative z-10 space-y-8 px-6 py-6 sm:px-8 md:px-9 lg:px-12 lg:py-8">
          <div className={hasVisibleSample ? "grid gap-8 lg:grid-cols-[minmax(0,1fr)_18rem]" : ""}>
            <div className="space-y-4 border-l-[3px] border-[var(--color-cobre)] pl-5">
              <h1 className="max-w-[40rem] font-display text-4xl leading-[0.92] tracking-[-0.05em] text-[var(--color-obsidiana)] sm:text-5xl lg:text-[4rem]">
                Dashboard de Inteligencia Urbana
              </h1>
              <p className="max-w-[36rem] text-[1rem] leading-8 text-[color-mix(in_srgb,var(--color-obsidiana),white_8%)] md:text-[1.05rem]">
                Una lectura pública para seguir cómo cambian las tarifas, qué trayectos dominan y
                dónde el clima deja una señal visible.
              </p>
            </div>

            {hasVisibleSample ? (
              <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_42%)] p-4">
                <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-cobre-oscuro)]">
                  Trayecto destacado
                </p>
                <p className="mt-3 font-display text-[1.7rem] leading-[0.98] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                  {topRoute?.corridor ?? "Sin trayecto visible"}
                </p>
                <p className="mt-4 text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  El trayecto que más resalta con los filtros elegidos.
                </p>
              </div>
            ) : null}
          </div>

          <div className="grid gap-3 border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_46%)] p-4 md:grid-cols-[repeat(3,minmax(0,1fr))_auto]">
            <DashboardFilterField
              label="Región"
              value={filters.source}
              placeholder="Todas las regiones"
              screenReaderLabel="Filtrar dashboard por región"
              onValueChange={(value) => setFilters((previous) => ({ ...previous, source: value }))}
              options={[
                { value: DASHBOARD_ALL_VALUE, label: "Todas las regiones" },
                ...payload.filters.sources.map((source) => ({ value: source, label: source })),
              ]}
            />

            <DashboardFilterField
              label="Temporalidad"
              value={filters.timeWindow}
              placeholder="Todo el recorte"
              screenReaderLabel="Filtrar dashboard por temporalidad"
              onValueChange={(value) =>
                setFilters((previous) => ({ ...previous, timeWindow: value }))
              }
              options={[
                { value: DASHBOARD_ALL_VALUE, label: "Todo el recorte" },
                ...payload.filters.time_windows.map((window) => ({
                  value: window.id,
                  label: window.label,
                })),
              ]}
            />

            <DashboardFilterField
              label="Servicio"
              value={filters.cabType}
              placeholder="Todos los servicios"
              screenReaderLabel="Filtrar dashboard por servicio"
              onValueChange={(value) =>
                setFilters((previous) => ({ ...previous, cabType: value }))
              }
              options={[
                { value: DASHBOARD_ALL_VALUE, label: "Todos los servicios" },
                ...payload.filters.cab_types.map((cabType) => ({ value: cabType, label: cabType })),
              ]}
            />

            <div className="flex items-end">
              <button
                type="button"
                onClick={() =>
                  setFilters({
                    source: DASHBOARD_ALL_VALUE,
                    cabType: DASHBOARD_ALL_VALUE,
                    timeWindow: DASHBOARD_ALL_VALUE,
                  })
                }
                className="inline-flex h-11 items-center justify-center gap-2 border border-[color-mix(in_srgb,var(--color-obsidiana),white_82%)] bg-white/84 px-4 text-[11px] font-medium uppercase tracking-[0.22em] text-[var(--color-obsidiana)] transition-colors hover:border-[var(--color-laguna)] hover:bg-white"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Limpiar
              </button>
            </div>
          </div>

          {hasVisibleSample ? (
            <div className="grid gap-px overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] md:grid-cols-2 xl:grid-cols-4">
              <DashboardKpi
                label="Tarifa media"
                value={formatCurrency(derived.metrics.avgPrice)}
                hint="Precio promedio en esta vista."
                tone="cobre"
              />
              <DashboardKpi
                label="Presión de demanda"
                value={formatMultiplier(derived.metrics.avgSurge)}
                hint="Indica si la demanda está subiendo el precio."
              />
              <DashboardKpi
                label="Trayecto destacado"
                value={topRoute?.corridor ?? "Sin trayecto"}
                hint="El que más resalta en esta vista."
                tone="laguna"
                compact
              />
              <DashboardKpi
                label="Ventana visible"
                value={derived.metrics.windowValue}
                hint="Periodo que estás explorando."
              />
            </div>
          ) : (
            <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_32%)] p-8">
              <div className="max-w-2xl space-y-4">
                <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre)]">
                  Sin coincidencias
                </p>
                <h2 className="font-display text-4xl tracking-[-0.04em] text-[var(--color-obsidiana)]">
                  No hay una lectura visible para ese recorte.
                </h2>
                <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  {emptyStateMessage}
                </p>
                <button
                  type="button"
                  onClick={() =>
                    setFilters({
                      source: DASHBOARD_ALL_VALUE,
                      cabType: DASHBOARD_ALL_VALUE,
                      timeWindow: DASHBOARD_ALL_VALUE,
                    })
                  }
                  className="inline-flex items-center justify-center border border-[var(--color-cobre-oscuro)] bg-[var(--color-cobre-oscuro)] px-5 py-3 text-[11px] font-medium uppercase tracking-[0.22em] text-[#f4efe7] transition-colors hover:border-[color-mix(in_srgb,var(--color-cobre-oscuro),white_10%)] hover:bg-[color-mix(in_srgb,var(--color-cobre-oscuro),white_10%)]"
                >
                  Volver al recorte completo
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {hasVisibleSample ? (
        <>
          <section className="space-y-4">
            <div className="space-y-2">
              <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre-oscuro)]">
                Tarifas por hora
              </p>
              <h2 className="font-display text-[2.2rem] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.6rem] md:text-4xl">
                Cómo cambian las tarifas durante el día
              </h2>
            </div>

            <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_38%)] px-4 py-5 md:px-6">
              <EChartsChart option={chartOption} className="h-[21rem] sm:h-[24rem] md:h-[30rem]" />
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
            <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_34%)] p-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre-oscuro)]">
                  Trayectos destacados
                </p>
                <h2 className="font-display text-[2.2rem] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.5rem] md:text-4xl">
                  Los trayectos que más resaltan en esta vista.
                </h2>
                <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  Aquí se concentran las señales más claras del recorte actual.
                </p>
              </div>
              <div className="mt-6 space-y-4">
                {derived.corridorRanking.map((route, index) => (
                  <div
                    key={route.corridor}
                    className="grid gap-4 border-b border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pb-4 md:grid-cols-[auto_minmax(0,1fr)_auto]"
                  >
                    <p className="font-data text-sm font-medium uppercase tracking-[0.2em] text-[var(--color-cobre)]">
                      {String(index + 1).padStart(2, "0")}
                    </p>
                    <div className="space-y-1">
                      <p className="font-medium text-[var(--color-obsidiana)]">{route.corridor}</p>
                      <p className="text-sm text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                        {route.context}
                      </p>
                    </div>
                    <div className="text-left md:text-right">
                      <p className="font-display text-3xl tracking-[-0.05em] text-[var(--color-obsidiana)]">
                        {formatCurrency(route.price)}
                      </p>
                      <p
                        className={
                          route.stateTone === "cobre"
                            ? "text-sm text-[var(--color-cobre)]"
                            : route.stateTone === "laguna"
                              ? "text-sm text-[var(--color-laguna)]"
                              : "text-sm text-[color-mix(in_srgb,var(--color-obsidiana),white_16%)]"
                        }
                      >
                        {route.stateLabel}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <aside className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_44%)] p-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre-oscuro)]">
                  Clima y tarifas
                </p>
                <h2 className="font-display text-[2.2rem] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.5rem] md:text-4xl">
                  {derived.climateSummary.headline}
                </h2>
                <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  {derived.climateSummary.note}
                </p>
              </div>

              <div className="mt-6 space-y-4 border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-5">
                <ClimateStat
                  icon={<CloudRain className="h-4 w-4 text-[var(--color-laguna)]" />}
                  label="Humedad media"
                  value={`${Math.round(derived.climateSummary.averageHumidity)}%`}
                />
                <ClimateStat
                  icon={<Thermometer className="h-4 w-4 text-[var(--color-cobre)]" />}
                  label="Temperatura visible"
                  value={`${formatCelsiusFromFahrenheit(derived.climateSummary.averageTempF)} °C`}
                />
                <ClimateStat
                  icon={<Waves className="h-4 w-4 text-[var(--color-laguna)]" />}
                  label="Nubosidad"
                  value={`${Math.round(derived.climateSummary.averageClouds)}%`}
                />
              </div>
            </aside>
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_34%)] p-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre-oscuro)]">
                  Patrones horarios
                </p>
                <h2 className="font-display text-[2.2rem] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.5rem] md:text-4xl">
                  En qué momentos se concentra la actividad
                </h2>
                <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  Lectura rápida por hora y servicio.
                </p>
              </div>

              <div className="mt-6 overflow-hidden border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_44%)] p-4">
                <div
                  className="grid gap-2"
                  style={{
                    gridTemplateColumns: `minmax(7rem,auto) repeat(${Math.max(
                      derived.hourlyPatterns.hours.length,
                      1,
                    )}, minmax(0,1fr))`,
                  }}
                >
                  <div />
                  {derived.hourlyPatterns.hours.map((hour) => (
                    <div
                      key={hour}
                      className="text-center text-[10px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]"
                    >
                      {hour}
                    </div>
                  ))}

                  {derived.hourlyPatterns.services.map((service, serviceIndex) => (
                    <Fragment key={service.key}>
                      <div className="flex items-center text-sm font-medium text-[var(--color-obsidiana)]">
                        {service.label}
                      </div>
                      {service.cells.map((cell) => {
                        const cellKey = `${service.key}-${cell.hour}`;
                        const isSelected = selectedPatternCell?.key === cellKey;

                        return (
                          <button
                            key={cellKey}
                            type="button"
                            onClick={() => {
                              if (cell.price !== null) {
                                setSelectedPatternCellKey(cellKey);
                              }
                            }}
                            disabled={cell.price === null}
                            aria-pressed={isSelected}
                            aria-label={
                              cell.price === null
                                ? `${service.label} · ${cell.hour}. Sin lectura visible.`
                                : buildPatternTooltip(service.label, cell)
                            }
                            className={
                              cell.price === null
                                ? "group relative aspect-square cursor-default border border-[color-mix(in_srgb,var(--color-obsidiana),white_92%)] bg-transparent p-0 disabled:opacity-100"
                                : isSelected
                                  ? "group relative aspect-square border border-[var(--color-obsidiana)] bg-transparent p-0 ring-1 ring-[var(--color-obsidiana)] transition-shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)]"
                                  : "group relative aspect-square border border-[color-mix(in_srgb,var(--color-obsidiana),white_92%)] bg-transparent p-0 transition-shadow hover:shadow-[inset_0_0_0_1px_rgba(21,36,45,0.18)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-laguna)]"
                            }
                            style={{
                              backgroundColor:
                                cell.intensity === 0
                                  ? "rgba(255,255,255,0.72)"
                                  : `color-mix(in srgb, ${getDashboardServiceColor(
                                      service.label,
                                      serviceIndex,
                                    )} ${Math.round(
                                      18 + cell.intensity * 62,
                                    )}%, white)`,
                            }}
                          >
                            {cell.price !== null ? (
                              <span className="pointer-events-none absolute inset-x-1 bottom-1 text-[10px] font-medium text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)] opacity-0 transition-opacity group-hover:opacity-100">
                                {cell.rides}
                              </span>
                            ) : null}
                          </button>
                        );
                      })}
                    </Fragment>
                  ))}
                </div>
                <p className="mt-4 text-[11px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_22%)]">
                  {derived.hourlyPatterns.supportLabel}
                </p>
                {selectedPatternCell ? (
                  <div className="mt-4 border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-4">
                    <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-end">
                      <div className="space-y-1">
                        <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-cobre-oscuro)]">
                          Detalle visible
                        </p>
                        <p className="text-base font-medium text-[var(--color-obsidiana)]">
                          {selectedPatternCell.service} · {selectedPatternCell.hour}
                        </p>
                        <p className="text-sm text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
                          Viajes visibles: {selectedPatternCell.rides}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]">
                          Tarifa media
                        </p>
                        <p className="font-display text-[1.7rem] tracking-[-0.05em] text-[var(--color-obsidiana)]">
                          {formatCurrency(selectedPatternCell.price)}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]">
                          Presión de demanda
                        </p>
                        <p
                          className="font-display text-[1.7rem] tracking-[-0.05em]"
                          style={{ color: selectedPatternCell.color }}
                        >
                          {formatMultiplier(selectedPatternCell.avgSurge ?? 0)}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>

            <div className="border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-[color-mix(in_srgb,var(--color-piedra),white_38%)] p-6">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre-oscuro)]">
                  Desglose por servicio
                </p>
                <h2 className="font-display text-[2.2rem] tracking-[-0.04em] text-[var(--color-obsidiana)] sm:text-[2.5rem] md:text-4xl">
                  Cómo cambia el precio entre servicios
                </h2>
                <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                  Comparación directa de la vista actual.
                </p>
              </div>

              <div className="mt-6 space-y-4">
                {derived.serviceBreakdown.map((service) => (
                  <article
                    key={service.service}
                    className="space-y-4 border border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] bg-[color-mix(in_srgb,var(--color-piedra),white_46%)] p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.24em] text-[var(--color-cobre-oscuro)]">
                          Servicio
                        </p>
                        <h3 className="mt-2 font-display text-[2rem] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                          {service.service}
                        </h3>
                      </div>
                      <p className="font-display text-[2rem] tracking-[-0.05em] text-[var(--color-cobre)]">
                        {formatCurrency(service.avgPrice)}
                      </p>
                    </div>

                    <div className="grid gap-4 border-t border-[color-mix(in_srgb,var(--color-obsidiana),white_88%)] pt-4 sm:grid-cols-2">
                      <div className="space-y-1">
                        <p className="text-[10px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]">
                          Presión de demanda
                        </p>
                        <p className="font-display text-[1.75rem] tracking-[-0.04em] text-[var(--color-obsidiana)]">
                          {formatMultiplier(service.avgSurge)}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] uppercase tracking-[0.22em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]">
                          Trayecto destacado
                        </p>
                        <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_8%)]">
                          {service.highlightedCorridor}
                        </p>
                      </div>
                    </div>

                    <p className="text-sm leading-7 text-[color-mix(in_srgb,var(--color-obsidiana),white_10%)]">
                      {service.summary}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="border-t border-[color-mix(in_srgb,var(--color-cobre),white_32%)] pt-8">
            <div className="grid gap-6 lg:grid-cols-[10rem_minmax(0,1fr)]">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.26em] text-[var(--color-cobre-oscuro)]">
                  {editorialNote.title}
                </p>
              </div>
              <div className="space-y-4">
                <p className="font-display text-[1.75rem] leading-[1.28] tracking-[-0.03em] text-[var(--color-obsidiana)] md:text-[2.25rem]">
                  {editorialNote.quote}
                </p>
                <div className="flex flex-wrap gap-3">
                  <HomeActionLink
                    href="/como-funciona"
                    variant="secondary"
                    className="rounded-none px-5 py-3"
                  >
                    Cómo funciona
                  </HomeActionLink>
                  <HomeActionLink href="/escenarios" className="rounded-none px-5 py-3">
                    Ver escenarios
                  </HomeActionLink>
                </div>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

type DashboardFilterFieldProps = {
  label: string;
  value: string;
  placeholder: string;
  screenReaderLabel: string;
  options: Array<{ value: string; label: string }>;
  onValueChange: (value: string) => void;
};

type DashboardKpiProps = {
  label: string;
  value: string;
  hint: string;
  tone?: "default" | "cobre" | "laguna";
  compact?: boolean;
};

type ClimateStatProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
};

function DashboardFilterField({
  label,
  value,
  placeholder,
  screenReaderLabel,
  options,
  onValueChange,
}: DashboardFilterFieldProps): React.ReactElement {
  return (
    <div className="space-y-2">
      <p className="text-[10px] uppercase tracking-[0.24em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]">
        {label}
      </p>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger
          className="h-12 rounded-none border-[color-mix(in_srgb,var(--color-obsidiana),white_84%)] bg-white/78"
          screenReaderLabel={screenReaderLabel}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent className="rounded-none">
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function DashboardKpi({
  label,
  value,
  hint,
  tone = "default",
  compact = false,
}: DashboardKpiProps): React.ReactElement {
  return (
    <div className="bg-[color-mix(in_srgb,var(--color-piedra),white_40%)] px-5 py-5">
      <p className="text-[10px] uppercase tracking-[0.24em] text-[color-mix(in_srgb,var(--color-obsidiana),white_18%)]">
        {label}
      </p>
      <p
        className={
          tone === "cobre"
            ? compact
              ? "mt-4 font-display text-[1.8rem] leading-[1.08] tracking-[-0.05em] text-[var(--color-cobre)] md:text-[2rem]"
              : "mt-4 font-display text-4xl tracking-[-0.05em] text-[var(--color-cobre)]"
            : tone === "laguna"
              ? compact
                ? "mt-4 font-display text-[1.8rem] leading-[1.08] tracking-[-0.05em] text-[var(--color-laguna)] md:text-[2rem]"
                : "mt-4 font-display text-4xl tracking-[-0.05em] text-[var(--color-laguna)]"
              : compact
                ? "mt-4 font-display text-[1.8rem] leading-[1.08] tracking-[-0.05em] text-[var(--color-obsidiana)] md:text-[2rem]"
                : "mt-4 font-display text-4xl tracking-[-0.05em] text-[var(--color-obsidiana)]"
        }
      >
        {value}
      </p>
      <p className="mt-2 text-sm text-[color-mix(in_srgb,var(--color-obsidiana),white_12%)]">
        {hint}
      </p>
    </div>
  );
}

function ClimateStat({ icon, label, value }: ClimateStatProps): React.ReactElement {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-9 w-9 items-center justify-center border border-[color-mix(in_srgb,var(--color-obsidiana),white_86%)] bg-white/84">
          {icon}
        </span>
        <span className="text-sm text-[color-mix(in_srgb,var(--color-obsidiana),white_14%)]">
          {label}
        </span>
      </div>
      <span className="font-display text-3xl tracking-[-0.05em] text-[var(--color-obsidiana)]">
        {value}
      </span>
    </div>
  );
}

function DashboardHeaderBackdrop(): React.ReactElement {
  return (
    <svg
      className="h-full w-full"
      viewBox="0 0 1200 460"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        d="M710 86C810 114 904 90 1024 42C1091 15 1145 7 1200 20"
        stroke="rgba(178,115,64,0.16)"
        strokeWidth="1.2"
      />
      <path
        d="M524 172C649 138 742 177 860 224C971 268 1074 257 1200 201"
        stroke="rgba(31,90,126,0.14)"
        strokeWidth="1.25"
      />
      <path
        d="M480 258C596 248 681 272 780 320C907 381 1038 356 1200 280"
        stroke="rgba(178,115,64,0.14)"
        strokeWidth="1.1"
      />
      <path
        d="M452 278C572 260 675 228 792 180C942 118 1079 147 1200 240"
        stroke="rgba(178,115,64,0.12)"
        strokeWidth="1"
      />
      <path
        d="M510 104C655 113 760 159 908 242C1010 300 1110 310 1200 274"
        stroke="rgba(21,36,45,0.06)"
        strokeWidth="1"
      />
    </svg>
  );
}

function buildTemporalTooltip(params: TemporalTooltipParam[]): string {
  const visibleParams = params.filter((param) => param.data?.value !== null);

  if (!visibleParams.length) {
    return "Sin lectura visible para esta hora.";
  }

  return visibleParams
    .map((param) => {
      const point = param.data!;
      const lines = [
        `<strong>${point.serviceLabel} · ${point.hourLabel}</strong>`,
        `Viajes visibles: ${point.rides}`,
        `Tarifa media: ${formatCurrency(point.value ?? 0)}`,
        `Presión de demanda: ${formatMultiplier(point.avgSurge ?? 0)}`,
      ];

      if (point.isPeak && point.rides > 1) {
        lines.push("Esta es una de las horas con más actividad de este servicio.");
      }

      return `<div style="margin-bottom:8px;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;"><span style="display:inline-block;width:10px;height:10px;background:${param.color ?? "#b27340"};"></span>${lines[0]}</div><div>${lines
        .slice(1)
        .join("<br/>")}</div></div>`;
    })
    .join("");
}

function buildPatternTooltip(
  service: string,
  cell: {
    hour: string;
    price: number | null;
    rides: number;
    avgSurge: number | null;
  },
): string {
  if (cell.price === null) {
    return `${service} · ${cell.hour}\nSin lectura visible.`;
  }

  return [
    `${service} · ${cell.hour}`,
    `Viajes visibles: ${cell.rides}`,
    `Tarifa media: ${formatCurrency(cell.price)}`,
    `Presión de demanda: ${formatMultiplier(cell.avgSurge ?? 0)}`,
  ].join("\n");
}

function resolveTemporalTooltipPosition(
  point: number | [number, number],
  size?: TooltipPositionSize,
): [number, number] {
  const [x, y] = Array.isArray(point) ? point : [point, 0];
  const contentWidth = size?.contentSize?.[0] ?? 220;
  const contentHeight = size?.contentSize?.[1] ?? 140;
  const viewWidth = size?.viewSize?.[0] ?? 320;
  const viewHeight = size?.viewSize?.[1] ?? 320;
  const margin = 12;
  const safeX = Math.min(
    Math.max(x + margin, margin),
    Math.max(viewWidth - contentWidth - margin, margin),
  );
  const preferredY = y - contentHeight - margin;
  const safeY =
    preferredY >= margin
      ? preferredY
      : Math.min(y + margin, Math.max(viewHeight - contentHeight - margin, margin));

  return [safeX, safeY];
}

function formatCelsiusFromFahrenheit(value: number): string {
  const celsius = ((value - 32) * 5) / 9;
  return celsius.toFixed(1);
}

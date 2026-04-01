"use client";

import { useState } from "react";
import type { EChartsOption } from "echarts";

import { EChartsChart } from "@/components/charts/echarts-chart";
import { CardShell } from "@/components/layout/card-shell";
import { FilterBar } from "@/components/layout/filter-bar";
import { MetricCard } from "@/components/layout/metric-card";
import { SectionHeader } from "@/components/layout/section-header";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DashboardPayload } from "@/lib/data/loaders";
import {
  formatCompactDate,
  formatCurrency,
  formatInteger,
  formatMultiplier,
} from "@/lib/formatters";

type DashboardViewProps = {
  payload: DashboardPayload;
};

type FiltersState = {
  source: string;
  destination: string;
  cabType: string;
  timeWindow: string;
};

const ALL_VALUE = "all";

export function DashboardView({ payload }: DashboardViewProps): React.ReactElement {
  const [filters, setFilters] = useState<FiltersState>({
    source: ALL_VALUE,
    destination: ALL_VALUE,
    cabType: ALL_VALUE,
    timeWindow: ALL_VALUE,
  });

  const selectedWindow = payload.filters.time_windows.find(
    (window) => window.id === filters.timeWindow,
  );
  const filteredTimeseries = payload.timeseries.filter((row) => {
    if (filters.source !== ALL_VALUE && row.source !== filters.source) {
      return false;
    }
    if (filters.destination !== ALL_VALUE && row.destination !== filters.destination) {
      return false;
    }
    if (filters.cabType !== ALL_VALUE && row.cab_type !== filters.cabType) {
      return false;
    }
    if (selectedWindow) {
      const hour = new Date(row.ride_hour).getHours();
      return selectedWindow.hours.includes(hour);
    }
    return true;
  });
  const filteredRoutes = payload.routeBreakdown.filter((row) => {
    if (filters.source !== ALL_VALUE && row.source !== filters.source) {
      return false;
    }
    if (filters.destination !== ALL_VALUE && row.destination !== filters.destination) {
      return false;
    }
    if (filters.cabType !== ALL_VALUE && row.cab_type !== filters.cabType) {
      return false;
    }
    return true;
  });
  const filteredWeather = payload.weatherImpact.filter((row) => {
    if (filters.source !== ALL_VALUE && row.source !== filters.source) {
      return false;
    }
    if (filters.destination !== ALL_VALUE && row.destination !== filters.destination) {
      return false;
    }
    if (filters.cabType !== ALL_VALUE && row.cab_type !== filters.cabType) {
      return false;
    }
    if (selectedWindow) {
      const hour = new Date(row.ride_hour).getHours();
      return selectedWindow.hours.includes(hour);
    }
    return true;
  });

  const aggregatedTrend = aggregateTrend(filteredTimeseries);
  const heatmapMatrix = aggregateHeatmap(filteredTimeseries);
  const avgPrice = averageOf(filteredTimeseries.map((row) => row.avg_price));
  const avgSurge = averageOf(filteredTimeseries.map((row) => row.avg_surge_multiplier));
  const totalRides = filteredTimeseries.reduce((sum, row) => sum + row.total_rides, 0);
  const bestRoute = filteredRoutes[0];

  const trendOption: EChartsOption = {
    animationDuration: 450,
    grid: { left: 12, right: 18, top: 18, bottom: 28, containLabel: true },
    tooltip: { trigger: "axis" },
    legend: {
      top: 0,
      textStyle: { color: "#53616b" },
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: aggregatedTrend.map((item) => item.label),
      axisLabel: { color: "#53616b" },
      axisLine: { lineStyle: { color: "#d9d0c4" } },
    },
    yAxis: [
      {
        type: "value",
        axisLabel: { color: "#53616b" },
        splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
      },
      {
        type: "value",
        axisLabel: { color: "#53616b" },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "Tarifa media",
        type: "line",
        smooth: true,
        data: aggregatedTrend.map((item) => Number(item.avgPrice.toFixed(2))),
        lineStyle: { color: "#b27340", width: 3 },
        areaStyle: {
          color: "rgba(178,115,64,0.14)",
        },
        symbolSize: 6,
      },
      {
        name: "Viajes",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        data: aggregatedTrend.map((item) => item.totalRides),
        lineStyle: { color: "#1f5a7e", width: 2 },
        symbolSize: 6,
      },
    ],
  };

  const heatmapOption: EChartsOption = {
    animationDuration: 350,
    grid: { left: 50, right: 20, top: 20, bottom: 28, containLabel: true },
    tooltip: { position: "top" },
    xAxis: {
      type: "category",
      data: Array.from({ length: 24 }, (_, hour) => `${hour}:00`),
      axisLabel: { color: "#53616b", interval: 3 },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category",
      data: heatmapMatrix.cabTypes,
      axisLabel: { color: "#53616b" },
      splitArea: { show: true },
    },
    visualMap: {
      min: 0,
      max: Math.max(...heatmapMatrix.points.map((point) => point[2] as number), 1),
      orient: "horizontal",
      left: "center",
      bottom: 0,
      inRange: {
        color: ["#edf4fb", "#9eb8ca", "#1f5a7e"],
      },
      textStyle: { color: "#53616b" },
    },
    series: [
      {
        type: "heatmap",
        data: heatmapMatrix.points,
        emphasis: {
          itemStyle: {
            shadowBlur: 12,
            shadowColor: "rgba(17,25,39,0.22)",
          },
        },
      },
    ],
  };

  const weatherOption: EChartsOption = {
    animationDuration: 350,
    grid: { left: 20, right: 20, top: 20, bottom: 28, containLabel: true },
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        const datum = Array.isArray(params) ? params[0] : params;
        const value = Array.isArray(datum?.value) ? datum.value : [];
        const name = typeof datum?.name === "string" ? datum.name : "Punto horario";
        return [
          `<strong>${name}</strong>`,
          `Temp: ${value[0] ?? "-"} °C`,
          `Precio: ${formatCurrency(Number(value[1] ?? 0))}`,
          `Humedad: ${value[2] ?? "-"}%`,
        ].join("<br/>");
      },
    },
    xAxis: {
      type: "value",
      name: "Temperatura promedio",
      nameLocation: "middle",
      nameGap: 28,
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    yAxis: {
      type: "value",
      name: "Tarifa media",
      nameLocation: "middle",
      nameGap: 42,
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    series: [
      {
        type: "scatter",
        symbolSize: (value) => Math.max(10, Number(value[3]) * 1.2),
        itemStyle: {
          color: "#b27340",
          opacity: 0.82,
        },
        data: filteredWeather.map((row) => [
          row.avg_temp,
          row.avg_price,
          row.avg_humidity,
          row.total_rides,
        ]),
      },
    ],
  };

  return (
    <div className="space-y-10">
      <SectionHeader
        eyebrow="Lectura pública"
        title="Tarifas, volumen y clima en una sola superficie analítica"
        description="El dashboard usa agregaciones exportadas por el pipeline y aplica filtros en cliente sobre artefactos tipados, sin llamadas a backend."
      />

      <FilterBar>
        <Select
          value={filters.source}
          onValueChange={(value) => setFilters((previous) => ({ ...previous, source: value }))}
        >
          <SelectTrigger screenReaderLabel="Filtrar por origen">
            <SelectValue placeholder="Origen" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>Todos los orígenes</SelectItem>
            {payload.filters.sources.map((source) => (
              <SelectItem key={source} value={source}>
                {source}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.destination}
          onValueChange={(value) =>
            setFilters((previous) => ({ ...previous, destination: value }))
          }
        >
          <SelectTrigger screenReaderLabel="Filtrar por destino">
            <SelectValue placeholder="Destino" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>Todos los destinos</SelectItem>
            {payload.filters.destinations.map((destination) => (
              <SelectItem key={destination} value={destination}>
                {destination}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.cabType}
          onValueChange={(value) => setFilters((previous) => ({ ...previous, cabType: value }))}
        >
          <SelectTrigger screenReaderLabel="Filtrar por tipo de servicio">
            <SelectValue placeholder="Servicio" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>Todos los servicios</SelectItem>
            {payload.filters.cab_types.map((cabType) => (
              <SelectItem key={cabType} value={cabType}>
                {cabType}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.timeWindow}
          onValueChange={(value) =>
            setFilters((previous) => ({ ...previous, timeWindow: value }))
          }
        >
          <SelectTrigger screenReaderLabel="Filtrar por franja horaria">
            <SelectValue placeholder="Franja horaria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>Todo el periodo</SelectItem>
            {payload.filters.time_windows.map((window) => (
              <SelectItem key={window.id} value={window.id}>
                {window.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FilterBar>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Tarifa media"
          value={formatCurrency(avgPrice)}
          hint={`Periodo visible: ${formatCompactDate(payload.overview.time_range.min)}`}
          accent="cobre"
        />
        <MetricCard
          label="Surge medio"
          value={formatMultiplier(avgSurge)}
          hint="Promedio de multiplicador de demanda"
          accent="laguna"
        />
        <MetricCard
          label="Viajes visibles"
          value={formatInteger(totalRides)}
          hint="Suma de agregaciones filtradas"
        />
        <MetricCard
          label="Ruta líder"
          value={
            bestRoute
              ? `${bestRoute.source} → ${bestRoute.destination}`
              : "Sin coincidencias"
          }
          hint={bestRoute ? `${bestRoute.cab_type} · ${formatCurrency(bestRoute.avg_price)}` : ""}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <CardShell className="p-6">
          <SectionHeader
            eyebrow="Pulse"
            title="Evolución horaria del precio"
            description="La línea cobre sigue la tarifa media; la azul laguna acompaña el volumen de viajes para detectar dónde sube precio sin una explosión equivalente de demanda."
          />
          <EChartsChart option={trendOption} className="mt-6 h-96" />
        </CardShell>

        <CardShell className="p-6">
          <SectionHeader
            eyebrow="Intensidad"
            title="Mapa horario por tipo de servicio"
            description="La matriz revela qué franjas concentran mayor actividad en cada cab type."
          />
          <EChartsChart option={heatmapOption} className="mt-6 h-96" />
        </CardShell>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <CardShell className="p-6">
          <SectionHeader
            eyebrow="Rutas"
            title="Ranking editorial de recorridos"
            description="Una lectura corta de las rutas con más viajes y mejor señal de precio."
          />
          <div className="mt-6 space-y-3">
            {filteredRoutes.slice(0, 6).map((route) => (
              <div
                key={`${route.source}-${route.destination}-${route.cab_type}`}
                className="grid gap-2 rounded-[1.5rem] border border-[var(--color-borde)] bg-[var(--color-laguna-suave)]/50 p-4 md:grid-cols-[minmax(0,1fr)_auto]"
              >
                <div className="space-y-1">
                  <p className="font-medium text-[var(--color-obsidiana)]">
                    {route.source} → {route.destination}
                  </p>
                  <p className="text-sm text-[var(--color-pizarra)]">
                    {route.cab_type} · {formatInteger(route.total_rides)} viajes · distancia media{" "}
                    {route.avg_distance.toFixed(1)} mi
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-display text-3xl tracking-[-0.04em] text-[var(--color-cobre)]">
                    {formatCurrency(route.avg_price)}
                  </p>
                  <p className="text-sm text-[var(--color-pizarra)]">
                    surge {formatMultiplier(route.avg_surge_multiplier)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardShell>

        <CardShell className="p-6">
          <SectionHeader
            eyebrow="Clima"
            title="Temperatura y precio"
            description="Cada punto representa una hora agregada; el tamaño refleja el número de viajes visibles."
          />
          <EChartsChart option={weatherOption} className="mt-6 h-[28rem]" />
        </CardShell>
      </section>
    </div>
  );
}

function aggregateTrend(payload: DashboardPayload["timeseries"]) {
  const buckets = new Map<
    string,
    {
      totalRides: number;
      weightedPrice: number;
      weightedSurge: number;
      label: string;
    }
  >();

  for (const row of payload) {
    const current = buckets.get(row.ride_hour) ?? {
      totalRides: 0,
      weightedPrice: 0,
      weightedSurge: 0,
      label: new Intl.DateTimeFormat("es-EC", {
        day: "numeric",
        month: "short",
        hour: "numeric",
      }).format(new Date(row.ride_hour)),
    };
    current.totalRides += row.total_rides;
    current.weightedPrice += row.avg_price * row.total_rides;
    current.weightedSurge += row.avg_surge_multiplier * row.total_rides;
    buckets.set(row.ride_hour, current);
  }

  return Array.from(buckets.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([, value]) => ({
      label: value.label,
      avgPrice: value.totalRides > 0 ? value.weightedPrice / value.totalRides : 0,
      avgSurge: value.totalRides > 0 ? value.weightedSurge / value.totalRides : 0,
      totalRides: value.totalRides,
    }));
}

function aggregateHeatmap(payload: DashboardPayload["timeseries"]) {
  const cabTypes = Array.from(new Set(payload.map((row) => row.cab_type)));
  const matrix = new Map<string, number>();

  for (const row of payload) {
    const hour = new Date(row.ride_hour).getHours();
    const key = `${row.cab_type}:${hour}`;
    matrix.set(key, (matrix.get(key) ?? 0) + row.total_rides);
  }

  const points: [number, number, number][] = [];
  for (const [cabTypeIndex, cabType] of cabTypes.entries()) {
    for (let hour = 0; hour < 24; hour += 1) {
      points.push([hour, cabTypeIndex, matrix.get(`${cabType}:${hour}`) ?? 0]);
    }
  }

  return { cabTypes, points };
}

function averageOf(values: number[]): number {
  if (!values.length) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

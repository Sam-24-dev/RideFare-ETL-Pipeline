"use client";

import { useState } from "react";
import type { EChartsOption } from "echarts";

import { EChartsChart } from "@/components/charts/echarts-chart";
import { CardShell } from "@/components/layout/card-shell";
import { MetricCard } from "@/components/layout/metric-card";
import { SectionHeader } from "@/components/layout/section-header";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ModelLabPayload } from "@/lib/data/loaders";
import { formatCompactDate, formatCurrency, formatMultiplier } from "@/lib/formatters";

type ModelLabViewProps = {
  payload: ModelLabPayload;
};

export function ModelLabView({ payload }: ModelLabViewProps): React.ReactElement {
  const championMetrics =
    payload.metrics.find((entry) => entry.model_name === payload.overview.champion_model) ??
    payload.metrics[0];
  const benchmarkOption: EChartsOption = {
    animationDuration: 300,
    grid: { left: 12, right: 20, top: 20, bottom: 28, containLabel: true },
    tooltip: { trigger: "axis" },
    legend: { top: 0, textStyle: { color: "#53616b" } },
    xAxis: {
      type: "category",
      data: payload.metrics.map((entry) => entry.model_name),
      axisLabel: { color: "#53616b" },
      axisLine: { lineStyle: { color: "#d9d0c4" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    series: [
      {
        name: "RMSE",
        type: "bar",
        data: payload.metrics.map((entry) => entry.holdout.rmse),
        itemStyle: { color: "#b27340" },
      },
      {
        name: "MAE",
        type: "bar",
        data: payload.metrics.map((entry) => entry.holdout.mae),
        itemStyle: { color: "#1f5a7e" },
      },
    ],
  };
  const predictionOption: EChartsOption = {
    animationDuration: 350,
    grid: { left: 20, right: 20, top: 20, bottom: 30, containLabel: true },
    tooltip: { trigger: "item" },
    xAxis: {
      type: "value",
      name: "Actual",
      nameLocation: "middle",
      nameGap: 28,
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    yAxis: {
      type: "value",
      name: "Predicho",
      nameLocation: "middle",
      nameGap: 32,
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    series: [
      {
        type: "scatter",
        data: payload.predictionSnapshot.map((row) => [row.actual, row.predicted, row.ride_name]),
        symbolSize: 18,
        itemStyle: { color: "#1f5a7e", opacity: 0.8 },
      },
    ],
  };
  const residualOption: EChartsOption = {
    animationDuration: 300,
    grid: { left: 20, right: 20, top: 20, bottom: 28, containLabel: true },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: payload.predictionSnapshot.map((row) => `#${row.ride_id}`),
      axisLabel: { color: "#53616b" },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    series: [
      {
        type: "bar",
        data: payload.predictionSnapshot.map((row) => row.residual),
        itemStyle: { color: "#b27340" },
      },
    ],
  };
  const importanceOption: EChartsOption = {
    animationDuration: 300,
    grid: { left: 90, right: 20, top: 20, bottom: 20, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    yAxis: {
      type: "category",
      data: payload.featureImportance.slice(0, 8).map((item) => item.feature).reverse(),
      axisLabel: { color: "#53616b" },
    },
    series: [
      {
        type: "bar",
        data: payload.featureImportance
          .slice(0, 8)
          .map((item) => item.importance)
          .reverse(),
        itemStyle: { color: "#b27340" },
      },
    ],
  };
  const shapOption: EChartsOption = {
    animationDuration: 300,
    grid: { left: 110, right: 20, top: 20, bottom: 20, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { color: "#53616b" },
      splitLine: { lineStyle: { color: "rgba(83,97,107,0.12)" } },
    },
    yAxis: {
      type: "category",
      data: payload.shapSummary.global_importance
        .slice(0, 8)
        .map((item) => item.feature)
        .reverse(),
      axisLabel: { color: "#53616b" },
    },
    series: [
      {
        type: "bar",
        data: payload.shapSummary.global_importance
          .slice(0, 8)
          .map((item) => item.mean_abs_shap)
          .reverse(),
        itemStyle: { color: "#1f5a7e" },
      },
    ],
  };

  return (
    <div className="space-y-10">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Modelo líder"
          value={payload.overview.champion_model}
          hint={`Run ${payload.overview.run_id}`}
          accent="cobre"
        />
        <MetricCard
          label="RMSE holdout"
          value={formatCurrency(championMetrics?.holdout.rmse ?? 0)}
          hint="Error cuadrático medio sobre la ventana final"
          accent="laguna"
        />
        <MetricCard
          label="Filas modeladas"
          value={payload.overview.row_count.toLocaleString("es-EC")}
          hint={`Desde ${formatCompactDate(payload.overview.time_range.min)}`}
        />
        <MetricCard
          label="Columnas activas"
          value={payload.overview.feature_columns.length.toString()}
          hint="Features incluidas en el contrato estable"
        />
      </section>

      <Tabs defaultValue="benchmark" className="space-y-6">
        <TabsList>
          <TabsTrigger value="benchmark">Comparativa</TabsTrigger>
          <TabsTrigger value="explicabilidad">Explicabilidad</TabsTrigger>
          <TabsTrigger value="simulador">Simulador</TabsTrigger>
        </TabsList>

        <TabsContent value="benchmark" className="space-y-6">
          <CardShell className="p-6">
            <SectionHeader
              eyebrow="Comparativa"
              title="Modelos comparados sobre una misma ventana temporal"
              description="La decisión final se hace sobre holdout temporal, no con split aleatorio. Aquí se comparan naïve baseline, lineal, random forest y XGBoost."
            />
            <EChartsChart option={benchmarkOption} className="mt-6 h-96" />
          </CardShell>

          <section className="grid gap-6 xl:grid-cols-2">
            <CardShell className="p-6">
              <SectionHeader
                eyebrow="Scatter"
                title="Actual vs. predicho"
                description="Lectura rápida de la cercanía entre realidad y estimación."
              />
              <EChartsChart option={predictionOption} className="mt-6 h-80" />
            </CardShell>
            <CardShell className="p-6">
              <SectionHeader
                eyebrow="Residuo"
                title="Desviación en el holdout"
                description="Una vista compacta de cuánto se aleja cada predicción del valor real."
              />
              <EChartsChart option={residualOption} className="mt-6 h-80" />
            </CardShell>
          </section>
        </TabsContent>

        <TabsContent value="explicabilidad" className="space-y-6">
          <section className="grid gap-6 xl:grid-cols-2">
            <CardShell className="p-6">
              <SectionHeader
                eyebrow="Feature importance"
                title="Qué mueve el modelo"
                description="Importancia global por feature para el modelo base de escenarios."
              />
              <EChartsChart option={importanceOption} className="mt-6 h-80" />
            </CardShell>
            <CardShell className="p-6">
              <SectionHeader
                eyebrow="SHAP"
                title="Contribuciones medias absolutas"
                description="La lectura de SHAP ayuda a explicar señales dominantes sin prometer causalidad."
              />
              <EChartsChart option={shapOption} className="mt-6 h-80" />
            </CardShell>
          </section>

          <CardShell className="p-6">
            <SectionHeader
              eyebrow="Muestras"
              title="Explicaciones de casos individuales"
              description="Se muestran las contribuciones más relevantes de una muestra acotada del holdout."
            />
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {payload.shapSummary.samples.slice(0, 4).map((sample) => (
                <div
                  key={`${sample.ride_id}-${sample.ride_hour}`}
                  className="rounded-[1.5rem] border border-[var(--color-borde)] bg-[var(--color-laguna-suave)]/40 p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-[var(--color-obsidiana)]">
                        Ride #{sample.ride_id}
                      </p>
                      <p className="text-sm text-[var(--color-pizarra)]">
                        {formatCompactDate(sample.ride_hour)}
                      </p>
                    </div>
                    <p className="text-sm text-[var(--color-pizarra)]">
                      Base {formatCurrency(sample.base_value ?? 0)}
                    </p>
                  </div>
                  <div className="mt-4 space-y-2 text-sm text-[var(--color-pizarra)]">
                    {(sample.top_contributions ?? []).map((contribution) => (
                      <div
                        key={`${sample.ride_id}-${contribution.feature}`}
                        className="flex items-center justify-between gap-3"
                      >
                        <span>{contribution.feature}</span>
                        <span>{formatCurrency(contribution.shap_value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardShell>
        </TabsContent>

        <TabsContent value="simulador">
          <ScenarioSimulator payload={payload} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

type ScenarioSimulatorProps = {
  payload: ModelLabPayload;
};

function ScenarioSimulator({ payload }: ScenarioSimulatorProps): React.ReactElement {
  const controls = payload.simulator.controls;
  const [source, setSource] = useState(controls.sources[0] ?? "");
  const [destination, setDestination] = useState(
    controls.destinations_by_source[controls.sources[0] ?? ""]?.[0] ?? "",
  );
  const [cabType, setCabType] = useState(controls.cab_types[0] ?? "");
  const [timeBlock, setTimeBlock] = useState(controls.time_blocks[0]?.id ?? "");
  const [weatherProfile, setWeatherProfile] = useState(controls.weather_profiles[0]?.id ?? "");
  const [surgeLevel, setSurgeLevel] = useState(String(controls.surge_levels[0] ?? 1));
  const [distanceFactor, setDistanceFactor] = useState(
    String(controls.distance_factors[0]?.factor ?? 1),
  );

  const destinationOptions = controls.destinations_by_source[source] ?? [];

  const selectedScenario = payload.simulator.grid.find(
    (row) =>
      row.source === source &&
      row.destination === destination &&
      row.cab_type === cabType &&
      row.time_block === timeBlock &&
      row.weather_profile === weatherProfile &&
      row.surge_multiplier === Number(surgeLevel) &&
      row.distance_factor === Number(distanceFactor),
  );

  const selectedProfile = controls.weather_profiles.find((profile) => profile.id === weatherProfile);

  return (
    <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <CardShell className="p-6">
        <SectionHeader
          eyebrow="Escenarios"
          title="Simulador estático basado en artefactos exportados"
          description="No hay inferencia en navegador. El resultado sale de una grilla precomputada con el modelo XGBoost y una banda derivada de su error holdout."
        />
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <Select
            value={source}
            onValueChange={(value) => {
              setSource(value);
              setDestination(controls.destinations_by_source[value]?.[0] ?? "");
            }}
          >
            <SelectTrigger screenReaderLabel="Seleccionar origen del simulador">
              <SelectValue placeholder="Origen" />
            </SelectTrigger>
            <SelectContent>
              {controls.sources.map((item) => (
                <SelectItem key={item} value={item}>
                  {item}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={destination} onValueChange={setDestination}>
            <SelectTrigger screenReaderLabel="Seleccionar destino del simulador">
              <SelectValue placeholder="Destino" />
            </SelectTrigger>
            <SelectContent>
              {destinationOptions.map((item) => (
                <SelectItem key={item} value={item}>
                  {item}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={cabType} onValueChange={setCabType}>
            <SelectTrigger screenReaderLabel="Seleccionar servicio del simulador">
              <SelectValue placeholder="Servicio" />
            </SelectTrigger>
            <SelectContent>
              {controls.cab_types.map((item) => (
                <SelectItem key={item} value={item}>
                  {item}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={timeBlock} onValueChange={setTimeBlock}>
            <SelectTrigger screenReaderLabel="Seleccionar franja horaria del simulador">
              <SelectValue placeholder="Franja" />
            </SelectTrigger>
            <SelectContent>
              {controls.time_blocks.map((item) => (
                <SelectItem key={item.id} value={item.id}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={weatherProfile} onValueChange={setWeatherProfile}>
            <SelectTrigger screenReaderLabel="Seleccionar perfil climático del simulador">
              <SelectValue placeholder="Clima" />
            </SelectTrigger>
            <SelectContent>
              {controls.weather_profiles.map((item) => (
                <SelectItem key={item.id} value={item.id}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={surgeLevel} onValueChange={setSurgeLevel}>
            <SelectTrigger screenReaderLabel="Seleccionar nivel de surge">
              <SelectValue placeholder="Surge" />
            </SelectTrigger>
            <SelectContent>
              {controls.surge_levels.map((item) => (
                <SelectItem key={String(item)} value={String(item)}>
                  {formatMultiplier(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="md:col-span-2">
            <Select value={distanceFactor} onValueChange={setDistanceFactor}>
              <SelectTrigger screenReaderLabel="Seleccionar ajuste de distancia">
                <SelectValue placeholder="Ajuste de distancia" />
              </SelectTrigger>
              <SelectContent>
                {controls.distance_factors.map((item) => (
                  <SelectItem key={item.id} value={String(item.factor)}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardShell>

      <CardShell accent="cobre" className="p-6">
        <SectionHeader
          eyebrow="Resultado"
          title={
            selectedScenario ? formatCurrency(selectedScenario.predicted_price) : "Sin escenario"
          }
          description={
            selectedScenario
              ? `${selectedScenario.source} → ${selectedScenario.destination} · ${selectedScenario.cab_type}`
              : "Ajusta los controles para ver una predicción exportada."
          }
        />
        {selectedScenario ? (
          <div className="mt-6 space-y-4 text-sm text-[var(--color-pizarra)]">
            <div className="rounded-[1.5rem] border border-[var(--color-borde)] bg-white/75 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-cobre)]">
                Banda sugerida
              </p>
              <p className="mt-2 font-display text-4xl tracking-[-0.04em] text-[var(--color-obsidiana)]">
                {formatCurrency(selectedScenario.price_band_low)} —{" "}
                {formatCurrency(selectedScenario.price_band_high)}
              </p>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-[1.5rem] border border-[var(--color-borde)] bg-white/65 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-pizarra)]">
                  Distancia base
                </p>
                <p className="mt-2 text-lg font-medium text-[var(--color-obsidiana)]">
                  {selectedScenario.route_distance_median.toFixed(1)} mi
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-[var(--color-borde)] bg-white/65 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-pizarra)]">
                  Perfil climático
                </p>
                <p className="mt-2 text-lg font-medium text-[var(--color-obsidiana)]">
                  {selectedProfile?.label}
                </p>
              </div>
            </div>
            {selectedProfile ? (
              <p className="leading-7">
                {selectedProfile.description} La predicción usa una distancia ajustada por un factor{" "}
                de {Number(distanceFactor).toFixed(2)} y un surge de {formatMultiplier(Number(surgeLevel))}.
              </p>
            ) : null}
          </div>
        ) : (
          <p className="mt-6 text-sm text-[var(--color-pizarra)]">
            No existe un escenario exportado para esa combinación. Prueba con otra ruta o franja.
          </p>
        )}
      </CardShell>
    </section>
  );
}

import type {
  DashboardFilters,
  DashboardRouteBreakdown,
  DashboardTimeseries,
  DashboardWeatherImpact,
} from "@/lib/data/contracts";
import type { DashboardPayload } from "@/lib/data/loaders";

export const DASHBOARD_ALL_VALUE = "all";

export type DashboardFiltersState = {
  source: string;
  cabType: string;
  timeWindow: string;
};

export type DashboardMetricSummary = {
  avgPrice: number;
  avgSurge: number;
  visibleRoutes: number;
  windowValue: string;
  windowHint: string;
};

export type DashboardSeries = {
  labels: string[];
  series: Array<{
    key: string;
    label: string;
    color: string;
    values: Array<{
      value: number | null;
      rides: number;
      avgSurge: number | null;
      hourLabel: string;
      serviceLabel: string;
      isPeak: boolean;
    }>;
  }>;
  supportLabel: string;
};

export type DashboardHourlyPatternMatrix = {
  hours: string[];
  services: Array<{
    key: string;
    label: string;
      cells: Array<{
        hour: string;
        intensity: number;
        price: number | null;
        rides: number;
        avgSurge: number | null;
      }>;
    }>;
  supportLabel: string;
};

export type DashboardRouteEntry = {
  corridor: string;
  context: string;
  price: number;
  stateLabel: string;
  stateTone: "cobre" | "laguna" | "neutral";
};

export type DashboardServiceEntry = {
  service: string;
  avgPrice: number;
  avgSurge: number;
  totalRides: number;
  highlightedCorridor: string;
  summary: string;
};

export type DashboardClimateSummary = {
  state: "weak" | "visible" | "route-dominant";
  headline: string;
  note: string;
  averageTempF: number;
  averageHumidity: number;
  averageClouds: number;
};

export type DashboardEditorialNote = {
  title: string;
  quote: string;
  caption: string;
};

export type DashboardFilteredData = {
  selectedWindow: DashboardFilters["time_windows"][number] | undefined;
  timeseries: DashboardTimeseries;
  routeBreakdown: DashboardRouteBreakdown;
  weatherImpact: DashboardWeatherImpact;
};

const hourFormatter = new Intl.DateTimeFormat("es-EC", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

const dayFormatter = new Intl.DateTimeFormat("es-EC", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

const SERVICE_COLORS: Record<string, string> = {
  Lyft: "#b27340",
  Uber: "#1f5a7e",
};

const FALLBACK_SERVICE_COLORS = ["#6f7f88", "#8f725a", "#5b7289"];

export function getDashboardServiceColor(service: string, index = 0): string {
  return SERVICE_COLORS[service] ?? FALLBACK_SERVICE_COLORS[index % FALLBACK_SERVICE_COLORS.length]!;
}

export function filterDashboardData(
  payload: Pick<DashboardPayload, "filters" | "timeseries" | "routeBreakdown" | "weatherImpact">,
  filters: DashboardFiltersState,
): DashboardFilteredData {
  const selectedWindow = payload.filters.time_windows.find(
    (window) => window.id === filters.timeWindow,
  );

  const timeseries = payload.timeseries.filter((row) => {
    if (filters.source !== DASHBOARD_ALL_VALUE && row.source !== filters.source) {
      return false;
    }
    if (filters.cabType !== DASHBOARD_ALL_VALUE && row.cab_type !== filters.cabType) {
      return false;
    }
    if (selectedWindow) {
      const hour = new Date(row.ride_hour).getHours();
      return selectedWindow.hours.includes(hour);
    }
    return true;
  });

  const routeBreakdown = payload.routeBreakdown.filter((row) => {
    if (filters.source !== DASHBOARD_ALL_VALUE && row.source !== filters.source) {
      return false;
    }
    if (filters.cabType !== DASHBOARD_ALL_VALUE && row.cab_type !== filters.cabType) {
      return false;
    }
    return true;
  });

  const weatherImpact = payload.weatherImpact.filter((row) => {
    if (filters.source !== DASHBOARD_ALL_VALUE && row.source !== filters.source) {
      return false;
    }
    if (filters.cabType !== DASHBOARD_ALL_VALUE && row.cab_type !== filters.cabType) {
      return false;
    }
    if (selectedWindow) {
      const hour = new Date(row.ride_hour).getHours();
      return selectedWindow.hours.includes(hour);
    }
    return true;
  });

  return {
    selectedWindow,
    timeseries,
    routeBreakdown,
    weatherImpact,
  };
}

export function buildDashboardMetricSummary(
  timeseries: DashboardTimeseries,
  routes: DashboardRouteBreakdown,
  selectedWindow?: DashboardFilters["time_windows"][number],
): DashboardMetricSummary {
  const hours = [...timeseries].map((row) => row.ride_hour).sort();
  const firstHour = hours[0] ? new Date(hours[0]) : null;
  const lastHour = hours.at(-1) ? new Date(hours.at(-1) as string) : null;

  let windowValue = "Sin datos";
  if (selectedWindow) {
    windowValue = selectedWindow.label;
  } else if (firstHour && lastHour) {
    const firstLabel = hourFormatter.format(firstHour);
    const lastLabel = hourFormatter.format(lastHour);
    windowValue = firstLabel === lastLabel ? firstLabel : `${firstLabel} → ${lastLabel}`;
  }

  return {
    avgPrice: weightedAverage(
      timeseries.map((row) => ({
        value: row.avg_price,
        weight: row.total_rides,
      })),
    ),
    avgSurge: weightedAverage(
      timeseries.map((row) => ({
        value: row.avg_surge_multiplier,
        weight: row.total_rides,
      })),
    ),
    visibleRoutes: routes.length,
    windowValue,
    windowHint: firstHour ? dayFormatter.format(firstHour) : "Sin lectura visible",
  };
}

export function buildTemporalPriceSeries(timeseries: DashboardTimeseries): DashboardSeries {
  const hours = Array.from(new Set(timeseries.map((row) => row.ride_hour))).sort();
  const cabTypes = Array.from(new Set(timeseries.map((row) => row.cab_type))).sort();

  return {
    labels: hours.map((hour) => hourFormatter.format(new Date(hour))),
    series: cabTypes.map((cabType, index) => {
      const hourlyRows = hours.map((hour) => {
        const matchingRows = timeseries.filter(
          (row) => row.ride_hour === hour && row.cab_type === cabType,
        );

        if (!matchingRows.length) {
          return {
            value: null,
            rides: 0,
            avgSurge: null,
            hourLabel: hourFormatter.format(new Date(hour)),
            serviceLabel: cabType,
            isPeak: false,
          };
        }

        const rides = matchingRows.reduce((sum, row) => sum + row.total_rides, 0);
        const avgPrice = weightedAverage(
          matchingRows.map((row) => ({
            value: row.avg_price,
            weight: row.total_rides,
          })),
        );
        const avgSurge = weightedAverage(
          matchingRows.map((row) => ({
            value: row.avg_surge_multiplier,
            weight: row.total_rides,
          })),
        );

        return {
          value: avgPrice,
          rides,
          avgSurge,
          hourLabel: hourFormatter.format(new Date(hour)),
          serviceLabel: cabType,
          isPeak: false,
        };
      });

      const peakRides = Math.max(...hourlyRows.map((row) => row.rides), 0);

      return {
        key: cabType,
        label: cabType,
        color: getDashboardServiceColor(cabType, index),
        values: hourlyRows.map((row) => ({
          ...row,
          isPeak: row.rides > 0 && row.rides === peakRides,
        })),
      };
    }),
    supportLabel: `Horas visibles: ${hours.length} · Servicios visibles: ${cabTypes.length}`,
  };
}

export function buildHourlyPatternMatrix(
  timeseries: DashboardTimeseries,
): DashboardHourlyPatternMatrix {
  const hours = Array.from(new Set(timeseries.map((row) => row.ride_hour))).sort();
  const cabTypes = Array.from(new Set(timeseries.map((row) => row.cab_type))).sort();
  const maxRides = Math.max(...timeseries.map((row) => row.total_rides), 0);
  const maxPrice = Math.max(...timeseries.map((row) => row.avg_price), 0);

  return {
    hours: hours.map((hour) => hourFormatter.format(new Date(hour))),
    services: cabTypes.map((cabType) => ({
      key: cabType,
      label: cabType,
      cells: hours.map((hour) => {
        const matchingRows = timeseries.filter(
          (row) => row.ride_hour === hour && row.cab_type === cabType,
        );

        if (!matchingRows.length) {
          return {
            hour: hourFormatter.format(new Date(hour)),
            intensity: 0,
            price: null,
            rides: 0,
            avgSurge: null,
          };
        }

        const rides = matchingRows.reduce((sum, row) => sum + row.total_rides, 0);
        const price = weightedAverage(
          matchingRows.map((row) => ({
            value: row.avg_price,
            weight: row.total_rides,
          })),
        );
        const rideScore = maxRides > 0 ? rides / maxRides : 0;
        const priceScore = maxPrice > 0 ? price / maxPrice : 0;
        const avgSurge = weightedAverage(
          matchingRows.map((row) => ({
            value: row.avg_surge_multiplier,
            weight: row.total_rides,
          })),
        );

        return {
          hour: hourFormatter.format(new Date(hour)),
          intensity: Math.min(1, rideScore * 0.6 + priceScore * 0.4),
          price,
          rides,
          avgSurge,
        };
      }),
    })),
    supportLabel: `Horas visibles: ${hours.length} · Servicios visibles: ${cabTypes.length}`,
  };
}

export function buildCorridorRanking(routes: DashboardRouteBreakdown): DashboardRouteEntry[] {
  return buildCorridorRankingFromRoutes(routes);
}

export function buildCorridorRankingFromVisibleSample(
  timeseries: DashboardTimeseries,
  routes: DashboardRouteBreakdown,
): DashboardRouteEntry[] {
  if (!timeseries.length) {
    return [];
  }

  const distanceByKey = new Map(
    routes.map((route) => [
      buildRouteKey(route.source, route.destination, route.cab_type),
      route.avg_distance,
    ]),
  );

  const groupedRoutes = new Map<
    string,
    {
      source: string;
      destination: string;
      cabType: string;
      totalRides: number;
      weightedPrice: number;
      weightedSurge: number;
    }
  >();

  timeseries.forEach((row) => {
    const key = buildRouteKey(row.source, row.destination, row.cab_type);
    const current = groupedRoutes.get(key);

    if (!current) {
      groupedRoutes.set(key, {
        source: row.source,
        destination: row.destination,
        cabType: row.cab_type,
        totalRides: row.total_rides,
        weightedPrice: row.avg_price * row.total_rides,
        weightedSurge: row.avg_surge_multiplier * row.total_rides,
      });
      return;
    }

    current.totalRides += row.total_rides;
    current.weightedPrice += row.avg_price * row.total_rides;
    current.weightedSurge += row.avg_surge_multiplier * row.total_rides;
  });

  const derivedRoutes = Array.from(groupedRoutes.values()).map((route) => ({
    source: route.source,
    destination: route.destination,
    cab_type: route.cabType,
    total_rides: route.totalRides,
    avg_price: route.weightedPrice / route.totalRides,
    avg_surge_multiplier: route.weightedSurge / route.totalRides,
    avg_distance:
      distanceByKey.get(buildRouteKey(route.source, route.destination, route.cabType)) ?? 0,
  }));

  return buildCorridorRankingFromRoutes(derivedRoutes);
}

export function buildServiceBreakdown(
  timeseries: DashboardTimeseries,
  routes: DashboardRouteBreakdown,
): DashboardServiceEntry[] {
  const visibleRoutes = buildCorridorRankingFromVisibleSample(timeseries, routes);
  const corridorByService = new Map<string, string>();

  visibleRoutes.forEach((route) => {
    const service = route.context.split(" / ")[0] ?? route.context;
    if (!corridorByService.has(service)) {
      corridorByService.set(service, route.corridor);
    }
  });

  const groupedServices = new Map<
    string,
    {
      totalRides: number;
      weightedPrice: number;
      weightedSurge: number;
    }
  >();

  timeseries.forEach((row) => {
    const current = groupedServices.get(row.cab_type);
    if (!current) {
      groupedServices.set(row.cab_type, {
        totalRides: row.total_rides,
        weightedPrice: row.avg_price * row.total_rides,
        weightedSurge: row.avg_surge_multiplier * row.total_rides,
      });
      return;
    }

    current.totalRides += row.total_rides;
    current.weightedPrice += row.avg_price * row.total_rides;
    current.weightedSurge += row.avg_surge_multiplier * row.total_rides;
  });

  return Array.from(groupedServices.entries())
    .map(([service, values]) => {
      const avgPrice = values.weightedPrice / values.totalRides;
      const avgSurge = values.weightedSurge / values.totalRides;
      const highlightedCorridor = corridorByService.get(service) ?? "Sin trayecto visible";

      return {
        service,
        avgPrice,
        avgSurge,
        totalRides: values.totalRides,
        highlightedCorridor,
        summary:
          values.totalRides === 1
            ? `${service} concentra 1 lectura visible y la señal más clara aparece en ${highlightedCorridor}.`
            : `${service} concentra ${values.totalRides} lecturas visibles y la señal más clara aparece en ${highlightedCorridor}.`,
      };
    })
    .sort((left, right) => right.avgPrice - left.avgPrice);
}

export function buildClimateSummary(weather: DashboardWeatherImpact): DashboardClimateSummary {
  if (!weather.length) {
    return {
      state: "weak",
      headline: "Relación débil",
      note: "En esta vista, el clima no explica por sí solo el cambio de tarifas.",
      averageTempF: 0,
      averageHumidity: 0,
      averageClouds: 0,
    };
  }

  const rows = weather.map((row) => ({
    temp: row.avg_temp,
    humidity: row.avg_humidity,
    clouds: row.avg_clouds,
    price: row.avg_price,
    weight: row.total_rides,
  }));

  const tempCorrelation = correlate(
    rows.map((row) => row.temp),
    rows.map((row) => row.price),
  );
  const humidityCorrelation = correlate(
    rows.map((row) => row.humidity),
    rows.map((row) => row.price),
  );

  const dominant =
    Math.abs(tempCorrelation) >= Math.abs(humidityCorrelation)
      ? { dimension: "temperatura", value: tempCorrelation }
      : { dimension: "humedad", value: humidityCorrelation };

  let state: DashboardClimateSummary["state"] = "weak";
  let headline = "Relación débil";
  let note = "En esta vista, el clima no explica por sí solo el cambio de tarifas.";

  if (Math.abs(dominant.value) >= 0.35) {
    if (dominant.value > 0) {
      state = "visible";
      headline = "Relación visible";
      note = "En esta vista, el clima acompaña la subida de precios.";
    } else {
      state = "route-dominant";
      headline = "El trayecto pesa más";
      note = "En esta vista, el trayecto pesa más que el clima en el cambio de precios.";
    }
  }

  return {
    state,
    headline,
    note,
    averageTempF: weightedAverage(
      rows.map((row) => ({
        value: row.temp,
        weight: row.weight,
      })),
    ),
    averageHumidity: weightedAverage(
      rows.map((row) => ({
        value: row.humidity,
        weight: row.weight,
      })),
    ),
    averageClouds: weightedAverage(
      rows.map((row) => ({
        value: row.clouds,
        weight: row.weight,
      })),
    ),
  };
}

export function buildEditorialNote(
  routes: DashboardRouteEntry[],
  climate: DashboardClimateSummary,
): DashboardEditorialNote {
  const leadRoute = routes[0];

  if (!leadRoute) {
    return {
      title: "Lectura principal",
      quote:
        "La vista actual todavía es demasiado corta para una lectura firme, pero ya deja ver cómo cambian las tarifas cuando aparecen trayectos y servicios visibles.",
      caption: "",
    };
  }

  if (climate.state === "route-dominant") {
    return {
      title: "Lectura principal",
      quote: `En esta vista, el trayecto pesa más que el clima. La variación de tarifas se explica mejor por el trayecto y el servicio visibles.`,
      caption: "",
    };
  }

  if (climate.state === "visible") {
    return {
      title: "Lectura principal",
      quote: `En esta vista, ${leadRoute.corridor} sigue marcando la lectura principal, y el clima acompaña la subida de tarifas.`,
      caption: "",
    };
  }

  return {
    title: "Lectura principal",
    quote: `En esta vista, ${leadRoute.corridor} es el trayecto más claro. El precio cambia más por el trayecto y el servicio que por una señal climática fuerte.`,
    caption: "",
  };
}

export function buildDashboardEmptyStateMessage(
  payload: DashboardPayload,
  filters: DashboardFiltersState,
): string {
  const baseSelection = filterDashboardData(payload, {
    ...filters,
    timeWindow: DASHBOARD_ALL_VALUE,
  });

  if (baseSelection.timeseries.length > 0 && filters.timeWindow !== DASHBOARD_ALL_VALUE) {
    const availableWindows = payload.filters.time_windows
      .filter((window) =>
        baseSelection.timeseries.some((row) =>
          window.hours.includes(new Date(row.ride_hour).getHours()),
        ),
      )
      .map((window) => window.label.toLowerCase());

    if (availableWindows.length === 1) {
      return `La muestra visible solo tiene datos en la franja de ${availableWindows[0]}. Cambia la temporalidad o vuelve al recorte completo.`;
    }

    if (availableWindows.length > 1) {
      return `La muestra visible solo tiene datos en estas franjas: ${availableWindows.join(", ")}. Cambia la temporalidad o vuelve al recorte completo.`;
    }
  }

  return "No hay datos visibles para esa combinación de región, servicio y temporalidad. Ajusta los filtros o vuelve al recorte completo.";
}

function weightedAverage(values: Array<{ value: number; weight: number }>): number {
  const totalWeight = values.reduce((sum, item) => sum + item.weight, 0);
  if (totalWeight === 0) {
    return 0;
  }

  return values.reduce((sum, item) => sum + item.value * item.weight, 0) / totalWeight;
}

function buildCorridorRankingFromRoutes(routes: DashboardRouteBreakdown): DashboardRouteEntry[] {
  return [...routes]
    .sort((left, right) => {
      if (right.total_rides !== left.total_rides) {
        return right.total_rides - left.total_rides;
      }
      return right.avg_price - left.avg_price;
    })
    .slice(0, 3)
    .map((route) => ({
      corridor: `${route.source} → ${route.destination}`,
      context:
        route.avg_distance > 0
          ? `${route.cab_type} / ${route.avg_distance.toFixed(1)} mi`
          : `${route.cab_type} / distancia no visible`,
      price: route.avg_price,
      stateLabel:
        route.avg_surge_multiplier >= 1.25
          ? "Demanda alta"
          : route.avg_surge_multiplier > 1
            ? "Señal mixta"
            : "Estable",
      stateTone:
        route.avg_surge_multiplier >= 1.25
          ? "cobre"
          : route.avg_surge_multiplier > 1
            ? "laguna"
            : "neutral",
    }));
}

function buildRouteKey(source: string, destination: string, cabType: string): string {
  return `${source}::${destination}::${cabType}`;
}

function correlate(left: number[], right: number[]): number {
  if (left.length < 2 || right.length < 2 || left.length !== right.length) {
    return 0;
  }

  const leftMean = left.reduce((sum, value) => sum + value, 0) / left.length;
  const rightMean = right.reduce((sum, value) => sum + value, 0) / right.length;

  let numerator = 0;
  let leftVariance = 0;
  let rightVariance = 0;

  for (let index = 0; index < left.length; index += 1) {
    const leftDelta = left[index]! - leftMean;
    const rightDelta = right[index]! - rightMean;
    numerator += leftDelta * rightDelta;
    leftVariance += leftDelta * leftDelta;
    rightVariance += rightDelta * rightDelta;
  }

  if (leftVariance === 0 || rightVariance === 0) {
    return 0;
  }

  return numerator / Math.sqrt(leftVariance * rightVariance);
}

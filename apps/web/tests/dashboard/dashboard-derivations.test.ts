import { describe, expect, it } from "vitest";

import type { DashboardPayload } from "../../lib/data/loaders";
import {
  DASHBOARD_ALL_VALUE,
  buildClimateSummary,
  buildCorridorRankingFromVisibleSample,
  buildDashboardEmptyStateMessage,
  buildDashboardMetricSummary,
  buildEditorialNote,
  buildHourlyPatternMatrix,
  buildServiceBreakdown,
  buildTemporalPriceSeries,
  filterDashboardData,
} from "../../components/dashboard/dashboard-derivations";

const payload: DashboardPayload = {
  overview: {
    generated_at: "2026-03-31T04:09:05.271892+00:00",
    time_range: {
      min: "2024-03-31T12:00:00",
      max: "2024-03-31T14:00:00",
    },
    dimensions: {
      sources: 2,
      destinations: 4,
      cab_types: 2,
    },
    kpis: [
      { id: "total_rides", label: "Viajes modelados", value: 4, format: "integer" },
      { id: "avg_price", label: "Tarifa media", value: 16.375, format: "currency" },
      {
        id: "avg_surge_multiplier",
        label: "Surge medio",
        value: 1.1875,
        format: "multiplier",
      },
      {
        id: "dominant_route",
        label: "Ruta más activa",
        value: "Beacon Hill → Financial District",
        format: "text",
      },
    ],
  },
  filters: {
    sources: ["Beacon Hill", "North End"],
    destinations: ["Back Bay", "Financial District", "North End", "South Station"],
    cab_types: ["Lyft", "Uber"],
    time_windows: [
      {
        id: "madrugada",
        label: "Madrugada",
        hours: [0, 1, 2, 3, 4, 5],
        anchor_hour: 3,
      },
      {
        id: "manana",
        label: "Mañana",
        hours: [6, 7, 8, 9, 10, 11],
        anchor_hour: 9,
      },
      {
        id: "tarde",
        label: "Tarde",
        hours: [12, 13, 14, 15, 16, 17],
        anchor_hour: 15,
      },
      {
        id: "noche",
        label: "Noche",
        hours: [18, 19, 20, 21, 22, 23],
        anchor_hour: 21,
      },
    ],
  },
  timeseries: [
    {
      avg_price: 24.2,
      avg_surge_multiplier: 1.25,
      cab_type: "Lyft",
      destination: "Financial District",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T12:00:00",
      source: "Beacon Hill",
      total_rides: 1,
    },
    {
      avg_price: 12.5,
      avg_surge_multiplier: 1,
      cab_type: "Uber",
      destination: "Back Bay",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T12:00:00",
      source: "North End",
      total_rides: 1,
    },
    {
      avg_price: 18,
      avg_surge_multiplier: 1.5,
      cab_type: "Uber",
      destination: "South Station",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T13:00:00",
      source: "North End",
      total_rides: 1,
    },
    {
      avg_price: 10.8,
      avg_surge_multiplier: 1,
      cab_type: "Lyft",
      destination: "North End",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T14:00:00",
      source: "Beacon Hill",
      total_rides: 1,
    },
  ],
  routeBreakdown: [
    {
      avg_distance: 5.8,
      avg_price: 24.2,
      avg_surge_multiplier: 1.25,
      cab_type: "Lyft",
      destination: "Financial District",
      source: "Beacon Hill",
      total_rides: 1,
    },
    {
      avg_distance: 3.4,
      avg_price: 18,
      avg_surge_multiplier: 1.5,
      cab_type: "Uber",
      destination: "South Station",
      source: "North End",
      total_rides: 1,
    },
    {
      avg_distance: 2.1,
      avg_price: 12.5,
      avg_surge_multiplier: 1,
      cab_type: "Uber",
      destination: "Back Bay",
      source: "North End",
      total_rides: 1,
    },
    {
      avg_distance: 1.9,
      avg_price: 10.8,
      avg_surge_multiplier: 1,
      cab_type: "Lyft",
      destination: "North End",
      source: "Beacon Hill",
      total_rides: 1,
    },
  ],
  weatherImpact: [
    {
      avg_clouds: 40,
      avg_humidity: 60,
      avg_price: 24.2,
      avg_temp: 47,
      cab_type: "Lyft",
      destination: "Financial District",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T12:00:00",
      source: "Beacon Hill",
      total_rides: 1,
    },
    {
      avg_clouds: 25,
      avg_humidity: 55,
      avg_price: 12.5,
      avg_temp: 45,
      cab_type: "Uber",
      destination: "Back Bay",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T12:00:00",
      source: "North End",
      total_rides: 1,
    },
    {
      avg_clouds: 65,
      avg_humidity: 58,
      avg_price: 18,
      avg_temp: 50,
      cab_type: "Uber",
      destination: "South Station",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T13:00:00",
      source: "North End",
      total_rides: 1,
    },
    {
      avg_clouds: 70,
      avg_humidity: 62,
      avg_price: 10.8,
      avg_temp: 51,
      cab_type: "Lyft",
      destination: "North End",
      ride_date: "2024-03-31T00:00:00",
      ride_hour: "2024-03-31T14:00:00",
      source: "Beacon Hill",
      total_rides: 1,
    },
  ],
};

describe("dashboard derivations", () => {
  it("filters visible data with public dashboard controls", () => {
    const filtered = filterDashboardData(payload, {
      source: "North End",
      cabType: "Uber",
      timeWindow: "tarde",
    });

    expect(filtered.selectedWindow?.label).toBe("Tarde");
    expect(filtered.timeseries).toHaveLength(2);
    expect(filtered.routeBreakdown).toHaveLength(2);
    expect(filtered.weatherImpact).toHaveLength(2);
  });

  it("builds stable metric and temporal summaries from exported artifacts", () => {
    const filtered = filterDashboardData(payload, {
      source: DASHBOARD_ALL_VALUE,
      cabType: DASHBOARD_ALL_VALUE,
      timeWindow: DASHBOARD_ALL_VALUE,
    });

    const metrics = buildDashboardMetricSummary(
      filtered.timeseries,
      filtered.routeBreakdown,
      filtered.selectedWindow,
    );
    const temporal = buildTemporalPriceSeries(filtered.timeseries);

    expect(metrics.avgPrice).toBeCloseTo(16.375, 4);
    expect(metrics.avgSurge).toBeCloseTo(1.1875, 4);
    expect(metrics.visibleRoutes).toBe(4);
    expect(metrics.windowValue).toBe("12:00 → 14:00");
    expect(metrics.windowHint).toContain("31");

    expect(temporal.labels).toEqual(["12:00", "13:00", "14:00"]);
    expect(temporal.series).toHaveLength(2);
    expect(temporal.series[0]?.values.map((point) => point.value)).toEqual([24.2, null, 10.8]);
    expect(temporal.series[0]?.values[0]?.serviceLabel).toBe("Lyft");
    expect(temporal.series[1]?.values.map((point) => point.value)).toEqual([12.5, 18, null]);
    expect(temporal.supportLabel).toBe("Horas visibles: 3 · Servicios visibles: 2");
  });

  it("creates an editorial ranking, climate summary, and note without inflating the sample", () => {
    const ranking = buildCorridorRankingFromVisibleSample(payload.timeseries, payload.routeBreakdown);
    const climate = buildClimateSummary(payload.weatherImpact);
    const note = buildEditorialNote(ranking, climate);

    expect(ranking).toHaveLength(3);
    expect(ranking[0]?.corridor).toBe("Beacon Hill → Financial District");
    expect(ranking[0]?.stateLabel).toBe("Demanda alta");

    expect(climate.headline).toBe("Relación débil");
    expect(climate.note).toContain("clima no explica");
    expect(climate.averageHumidity).toBeCloseTo(58.75, 2);

    expect(note.title).toBe("Lectura principal");
    expect(note.quote).toContain("Beacon Hill → Financial District");
    expect(note.caption).toBe("");
  });

  it("builds hourly patterns and service breakdown from the same visible sample", () => {
    const hourlyPatterns = buildHourlyPatternMatrix(payload.timeseries);
    const serviceBreakdown = buildServiceBreakdown(payload.timeseries, payload.routeBreakdown);

    expect(hourlyPatterns.hours).toEqual(["12:00", "13:00", "14:00"]);
    expect(hourlyPatterns.services).toHaveLength(2);
    expect(hourlyPatterns.services[0]?.cells).toHaveLength(3);
    expect(hourlyPatterns.services[0]?.cells[0]?.avgSurge).toBeCloseTo(1.25, 2);
    expect(hourlyPatterns.supportLabel).toBe("Horas visibles: 3 · Servicios visibles: 2");

    expect(serviceBreakdown).toHaveLength(2);
    expect(serviceBreakdown[0]?.service).toBe("Lyft");
    expect(serviceBreakdown[0]?.highlightedCorridor).toBe(
      "Beacon Hill → Financial District",
    );
    expect(serviceBreakdown[0]?.summary).toContain("Lyft concentra 2 lecturas visibles");
    expect(serviceBreakdown[1]?.service).toBe("Uber");
  });

  it("drops highlighted routes when the visible sample has no data", () => {
    const filtered = filterDashboardData(payload, {
      source: DASHBOARD_ALL_VALUE,
      cabType: DASHBOARD_ALL_VALUE,
      timeWindow: "manana",
    });

    const ranking = buildCorridorRankingFromVisibleSample(filtered.timeseries, filtered.routeBreakdown);

    expect(ranking).toEqual([]);
  });

  it("explains why there is no visible data when filters point to an empty time window", () => {
    const message = buildDashboardEmptyStateMessage(payload, {
      source: DASHBOARD_ALL_VALUE,
      cabType: DASHBOARD_ALL_VALUE,
      timeWindow: "manana",
    });

    expect(message).toContain("franja de tarde");
  });
});

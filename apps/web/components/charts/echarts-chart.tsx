"use client";

import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";
import * as echarts from "echarts/core";
import { BarChart, HeatmapChart, LineChart, ScatterChart } from "echarts/charts";
import {
  DatasetComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import { cn } from "@/lib/utils";

echarts.use([
  BarChart,
  DatasetComponent,
  GridComponent,
  HeatmapChart,
  LegendComponent,
  LineChart,
  ScatterChart,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

type EChartsChartProps = {
  option: EChartsOption;
  className?: string;
};

export function EChartsChart({
  option,
  className,
}: EChartsChartProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<echarts.EChartsType | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return undefined;
    }

    const chart = echarts.init(containerRef.current, undefined, {
      renderer: "canvas",
    });
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      chart.resize({
        animation: {
          duration: 200,
          easing: "cubicOut",
        },
      });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chartRef.current = null;
      chart.dispose();
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current) {
      return;
    }

    chartRef.current.setOption(option, {
      notMerge: true,
      lazyUpdate: true,
    });
  }, [option]);

  return <div ref={containerRef} className={cn("h-80 w-full", className)} />;
}

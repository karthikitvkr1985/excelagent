"use client";

import ReactECharts from "echarts-for-react";

function toOption(chart: any): any {
  const { type, title, data, x_data } = chart;
  const dt = data || { x_data: [], series: [] };
  const base = {
    title: { text: title, left: "center", textStyle: { fontSize: 14 } },
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 20, top: 50, bottom: 40 },
  };

  if (type === "pie") {
    return {
      ...base,
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["40%", "70%"],
          data: dt.series,
          label: { formatter: "{b}: {d}%", fontSize: 11 },
        },
      ],
    };
  }

  if (type === "line") {
    return {
      ...base,
      xAxis: { type: "category", data: dt.x_data },
      yAxis: { type: "value" },
      series: (dt.series || []).map((s: any) => ({
        name: s.name,
        type: "line",
        smooth: true,
        areaStyle: { opacity: 0.15 },
        data: s.data,
      })),
    };
  }

  if (type === "scatter") {
    return {
      ...base,
      xAxis: { type: "category", data: dt.x_data },
      yAxis: { type: "value" },
      symbolSize: 14,
      series: (dt.series || []).map((s: any) => ({ name: s.name, type: "scatter", data: s.data })),
    };
  }

  return {
    ...base,
    xAxis: { type: "category", data: dt.x_data },
    yAxis: { type: "value" },
    series: (dt.series || []).map((s: any) => ({ name: s.name, type: "bar", data: s.data, itemStyle: { borderRadius: [4, 4, 0, 0] } })),
  };
}

export default function DashboardRenderer({ spec }: { spec: any }) {
  const layouts = spec?.layouts || [];
  if (layouts.length === 0) {
    return <p className="text-sm text-slate-500">No charts were generated for this dashboard.</p>;
  }
  return (
    <div className="grid md:grid-cols-2 gap-4">
      {layouts.map((chart: any, i: number) => (
        <div key={i} className="bg-white border border-slate-200 rounded-xl p-3">
          <ReactECharts option={toOption(chart)} style={{ height: 300 }} notMerge />
        </div>
      ))}
    </div>
  );
}
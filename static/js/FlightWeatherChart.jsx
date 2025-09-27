import React from 'react';
import { Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    LineElement,
    CategoryScale,
    LinearScale,
    PointElement,
    ChartOptions,
    Chart,
} from "chart.js";

ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement);

export default function FlightWeatherChart({ flightData }) {
    const data = flightData?.timeline;
    
    if (!data || data.length === 0) {
        return <p className="text-gray-500">No flight data available</p>;
    }
    
    // Transform flight data
    const chartData = data.map((point) => {
        const weather = point.conditions?.natural_language?.match(/Weather: (.*?)[.,]/)?.[1] || "";
        const clouds = point.conditions?.natural_language?.match(/Clouds: (.*)/)?.[1] || "";
        
        // Only one main weather icon per point
        let weatherIcon = "☀️"; // default sunny
        if (/rain/i.test(weather)) weatherIcon = "🌧️";
        else if (/thunderstorm|TS/i.test(weather)) weatherIcon = "⛈️";
        else if (/haze|mist/i.test(weather)) weatherIcon = "🌫️";
        else if (/fog/i.test(weather)) weatherIcon = "🌁";
        
        return {
            time: new Date(point.start_time).toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
                timeZone: "UTC",
            }),
            visibility: point.visibility,
            temperature: point.temperature,
            dewPoint: point.conditions?.natural_language?.match(/dew point (\d+)°C/)
                ? Number(point.conditions.natural_language.match(/dew point (\d+)°C/)[1])
                : null,
            windSpeed: point.wind_speed,
            windDir: point.conditions?.natural_language?.match(/Wind from (\d+) degrees/)
                ? Number(point.conditions.natural_language.match(/Wind from (\d+) degrees/)[1])
                : null,
            location: point.location_description,
            weather,
            clouds,
            weatherIcon,
        };
    });
    
    const labels = chartData.map((d) => d.time);
    
    const dataset = {
        labels,
        datasets: [
            {
                label: "Visibility (SM)",
                data: chartData.map((d) => d.visibility),
                borderColor: "rgb(59,130,246)",
                backgroundColor: "rgba(59,130,246,0.2)",
                tension: 0.3,
                yAxisID: "y",
            },
            {
                label: "Temperature (°C)",
                data: chartData.map((d) => d.temperature),
                borderColor: "rgb(239,68,68)",
                backgroundColor: "rgba(239,68,68,0.2)",
                tension: 0.3,
                yAxisID: "y1",
            },
            {
                label: "Dew Point (°C)",
                data: chartData.map((d) => d.dewPoint),
                borderColor: "rgb(34,197,94)",
                backgroundColor: "rgba(34,197,94,0.2)",
                borderDash: [6, 6],
                tension: 0.3,
                yAxisID: "y1",
            },
            {
                label: "Wind Speed (kt)",
                data: chartData.map((d) => d.windSpeed),
                borderColor: "rgb(234,179,8)",
                backgroundColor: "rgba(234,179,8,0.2)",
                borderDash: [2, 4],
                tension: 0.3,
                yAxisID: "y2",
            },
        ],
    };
    
    const options = {
        responsive: true,
        layout: { padding: { top: 60 } }, // space for heading & icons
        plugins: {
            legend: { position: "top" },
            tooltip: {
                callbacks: {
                    afterLabel: (context) => {
                        const idx = context.dataIndex;
                        const point = chartData[idx];
                        return [
                            `Loc: ${point.location}`,
                            `Wind: ${point.windDir ?? "VRB"}°/${point.windSpeed} kt`,
                            `Weather: ${point.weather}`,
                            `Clouds: ${point.clouds}`, // cloud info only in tooltip
                        ];
                    },
                },
            },
        },
        scales: {
            y: { type: "linear", position: "left", title: { display: true, text: "Visibility (SM)" } },
            y1: { type: "linear", position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "Temp & Dew Point (°C)" } },
            y2: { type: "linear", position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "Wind Speed (kt)" } },
        },
    };
    
    // Plugin to draw only one weather emoji per X point
    const iconPlugin = {
        id: "weatherIcons",
        afterDatasetsDraw: (chart) => {
            const { ctx } = chart;
            ctx.save();
            // Use only the first dataset for coordinates
            const meta = chart.getDatasetMeta(0);
            chartData.forEach((point, i) => {
                const bar = meta.data[i];
                if (!bar) return;
                const { x, y } = bar.getProps(["x", "y"], true);
                ctx.font = "16px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(point.weatherIcon, x, y - 40); // single icon
            });
            ctx.restore();
        },
    };
    
    return (
        <div className="flex flex-col items-center mt-6">
            <div className="bg-white shadow-md p-4 rounded-lg h-fit w-full">
                <h3 className="text-lg font-semibold mb-4 text-center">Flight Weather Timeline</h3>
                <Line data={dataset} options={options} plugins={[iconPlugin]} />
            </div>
        </div>
    );
}

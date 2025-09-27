/**
 * Flight Weather Chart - Vanilla JavaScript implementation
 * Integrates Chart.js to display flight weather timeline data
 */

class FlightWeatherChart {
    constructor(containerId) {
        this.containerId = containerId;
        this.chart = null;
        this.chartData = [];
    }

    /**
     * Initialize the chart with flight data
     * @param {Object} flightData - Flight data containing timeline information
     */
    init(flightData) {
        console.log('FlightWeatherChart.init called with:', flightData);
        
        const data = flightData?.timeline || flightData?.weather_timeline;
        
        if (!data || data.length === 0) {
            console.warn('No timeline data available for chart');
            this.showNoDataMessage();
            return;
        }

        console.log('Processing timeline data:', data);
        this.transformData(data);
        this.createChart();
    }

    /**
     * Transform flight data for Chart.js format
     * @param {Array} data - Raw flight timeline data
     */
    transformData(data) {
        this.chartData = data.map((point) => {
            // Extract weather information from natural language or structured data
            const weather = point.conditions?.natural_language?.match(/Weather: (.*?)[.,]/)?.[1] || 
                           point.weather_description || "";
            const clouds = point.conditions?.natural_language?.match(/Clouds: (.*)/)?.[1] || 
                          point.cloud_description || "";
            
            // Determine weather icon based on conditions
            let weatherIcon = "☀️"; // default sunny
            if (/rain|precipitation/i.test(weather)) weatherIcon = "🌧️";
            else if (/thunderstorm|TS|storm/i.test(weather)) weatherIcon = "⛈️";
            else if (/haze|mist/i.test(weather)) weatherIcon = "🌫️";
            else if (/fog/i.test(weather)) weatherIcon = "🌁";
            else if (/cloud|overcast/i.test(weather)) weatherIcon = "☁️";
            else if (/clear|sunny/i.test(weather)) weatherIcon = "☀️";
            
            return {
                time: this.formatTime(point.start_time || point.time || point.timestamp),
                visibility: point.visibility || point.visibility_sm || 10,
                temperature: point.temperature || point.temp_c || 15,
                dewPoint: this.extractDewPoint(point),
                windSpeed: point.wind_speed || point.wind_speed_kt || 0,
                windDir: this.extractWindDirection(point),
                location: point.location_description || point.airport || point.location || "",
                weather,
                clouds,
                weatherIcon,
            };
        });
    }

    /**
     * Extract dew point from various data formats
     */
    extractDewPoint(point) {
        if (point.dew_point !== undefined) return point.dew_point;
        if (point.dewpoint_c !== undefined) return point.dewpoint_c;
        
        const match = point.conditions?.natural_language?.match(/dew point (\d+)°C/);
        return match ? Number(match[1]) : null;
    }

    /**
     * Extract wind direction from various data formats
     */
    extractWindDirection(point) {
        if (point.wind_direction !== undefined) return point.wind_direction;
        if (point.wind_dir !== undefined) return point.wind_dir;
        
        const match = point.conditions?.natural_language?.match(/Wind from (\d+) degrees/);
        return match ? Number(match[1]) : null;
    }

    /**
     * Format time for display
     */
    formatTime(timeStr) {
        if (!timeStr) return "";
        
        try {
            const date = new Date(timeStr);
            return date.toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit",
                timeZone: "UTC",
            });
        } catch (e) {
            return timeStr.toString();
        }
    }

    /**
     * Create the Chart.js chart
     */
    createChart() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID ${this.containerId} not found`);
            return;
        }

        // Clear existing content and create canvas
        container.innerHTML = `
            <h3 class="text-center mb-4">Enhanced Flight Weather Timeline</h3>
            <div style="position: relative; height: 400px; width: 100%;">
                <canvas id="${this.containerId}-canvas"></canvas>
            </div>
        `;

        const canvas = document.getElementById(`${this.containerId}-canvas`);
        if (!canvas) {
            console.error('Canvas element not created');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('Could not get canvas context');
            return;
        }

        const labels = this.chartData.map(d => d.time);

        const dataset = {
            labels,
            datasets: [
                {
                    label: "Visibility (SM)",
                    data: this.chartData.map(d => d.visibility),
                    borderColor: "rgb(59,130,246)",
                    backgroundColor: "rgba(59,130,246,0.2)",
                    tension: 0.3,
                    yAxisID: "y",
                },
                {
                    label: "Temperature (°C)",
                    data: this.chartData.map(d => d.temperature),
                    borderColor: "rgb(239,68,68)",
                    backgroundColor: "rgba(239,68,68,0.2)",
                    tension: 0.3,
                    yAxisID: "y1",
                },
                {
                    label: "Dew Point (°C)",
                    data: this.chartData.map(d => d.dewPoint),
                    borderColor: "rgb(34,197,94)",
                    backgroundColor: "rgba(34,197,94,0.2)",
                    borderDash: [6, 6],
                    tension: 0.3,
                    yAxisID: "y1",
                },
                {
                    label: "Wind Speed (kt)",
                    data: this.chartData.map(d => d.windSpeed),
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
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { 
                    position: "top",
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: (context) => {
                            const idx = context.dataIndex;
                            const point = this.chartData[idx];
                            return [
                                `Location: ${point.location}`,
                                `Wind: ${point.windDir ?? "VRB"}°/${point.windSpeed} kt`,
                                `Weather: ${point.weather}`,
                                `Clouds: ${point.clouds}`,
                            ];
                        },
                    },
                },
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time (UTC)'
                    }
                },
                y: { 
                    type: "linear", 
                    position: "left", 
                    title: { display: true, text: "Visibility (SM)" },
                    grid: { color: "rgba(0,0,0,0.1)" },
                    beginAtZero: true
                },
                y1: { 
                    type: "linear", 
                    position: "right", 
                    grid: { drawOnChartArea: false }, 
                    title: { display: true, text: "Temperature (°C)" }
                },
                y2: { 
                    type: "linear", 
                    position: "right", 
                    grid: { drawOnChartArea: false }, 
                    title: { display: true, text: "Wind Speed (kt)" },
                    beginAtZero: true
                },
            },
        };

        // Weather icons plugin
        const iconPlugin = {
            id: "weatherIcons",
            afterDatasetsDraw: (chart) => {
                const { ctx } = chart;
                ctx.save();
                const meta = chart.getDatasetMeta(0);
                this.chartData.forEach((point, i) => {
                    const element = meta.data[i];
                    if (!element) return;
                    const { x, y } = element.getProps(["x", "y"], true);
                    ctx.font = "16px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(point.weatherIcon, x, y - 40);
                });
                ctx.restore();
            },
        };

        // Create the chart with error handling
        try {
            console.log('Creating Chart.js instance with data:', this.chartData.length, 'points');
            
            this.chart = new Chart(ctx, {
                type: 'line',
                data: dataset,
                options: options,
                plugins: [iconPlugin]
            });
            
            console.log('Chart created successfully');
        } catch (error) {
            console.error('Error creating Chart.js instance:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Chart Error</h5>
                    <p>Failed to create chart: ${error.message}</p>
                    <small>Check browser console for details</small>
                </div>
            `;
        }
    }

    /**
     * Show message when no data is available
     */
    showNoDataMessage() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-chart-line"></i> Flight Weather Timeline</h6>
                    </div>
                    <div class="card-body text-center">
                        <p class="text-muted">No flight timeline data available</p>
                        <small>Timeline data will appear here when you analyze a flight plan</small>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Destroy the chart instance
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    /**
     * Update chart with new data
     */
    update(flightData) {
        this.destroy();
        this.init(flightData);
    }
}

// Make it globally available
window.FlightWeatherChart = FlightWeatherChart;

// Test function for debugging
window.testChartCreation = function() {
    console.log('Testing chart creation...');
    
    const testData = {
        timeline: [
            {
                start_time: "2024-01-15T10:00:00Z",
                location_description: "KJFK",
                visibility: 8,
                temperature: 12,
                wind_speed: 15,
                weather_description: "Clear",
                cloud_description: "Few clouds",
                conditions: {
                    natural_language: "Weather: Clear. Clouds: Few clouds. Wind from 270 degrees at 15 knots."
                }
            },
            {
                start_time: "2024-01-15T12:00:00Z",
                location_description: "KLAX",
                visibility: 10,
                temperature: 22,
                wind_speed: 8,
                weather_description: "Clear",
                cloud_description: "Clear",
                conditions: {
                    natural_language: "Weather: Clear. Clouds: Clear. Wind from 250 degrees at 8 knots."
                }
            }
        ]
    };
    
    const chart = new FlightWeatherChart('flightWeatherChart');
    chart.init(testData);
};

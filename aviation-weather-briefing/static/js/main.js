// Aviation Weather Briefing System - Main JavaScript

// Global variables
let currentWeatherData = null;
let currentAnalysisData = null;

// UTC Clock functionality
function updateUTCClock() {
    const now = new Date();
    const utcTime = now.toUTCString().substr(17, 8); // Get HH:MM:SS format from UTC string
    const clockElement = document.getElementById('utc-clock');
    if (clockElement) {
        clockElement.textContent = utcTime;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UTC clock
    updateUTCClock();
    setInterval(updateUTCClock, 1000); // Update every second
    
    // Initialize event listeners and load sample data
    initializeEventListeners();
    loadSampleData();
});

function initializeEventListeners() {
    // Manual form submission
    document.getElementById('manualForm').addEventListener('submit', handleManualSubmit);
    
    // Individual weather form submission
    document.getElementById('individualForm').addEventListener('submit', handleIndividualSubmit);
    
    // File upload handling
    document.getElementById('flightPlanFile').addEventListener('change', handleFileUpload);
    
    // Input validation
    setupInputValidation();
}

function setupInputValidation() {
    // ICAO code validation
    const icaoInputs = document.querySelectorAll('#departure, #arrival, #airportCode');
    icaoInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase().replace(/[^A-Z]/g, '');
        });
    });
    
    // Waypoints validation
    document.getElementById('waypoints').addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
}

function handleManualSubmit(event) {
    event.preventDefault();
    
    const departure = document.getElementById('departure').value.trim().toUpperCase();
    const arrival = document.getElementById('arrival').value.trim().toUpperCase();
    const waypoints = document.getElementById('waypoints').value.trim();
    const departureTime = document.getElementById('departureTime').value;
    
    if (!validateICAOCode(departure) || !validateICAOCode(arrival)) {
        showError('Please enter valid 4-letter ICAO airport codes');
        return;
    }
    
    const waypointList = waypoints ? waypoints.split(',').map(w => w.trim()).filter(w => w) : [];
    
    // Validate waypoints
    for (let waypoint of waypointList) {
        if (!validateICAOCode(waypoint)) {
            showError(`Invalid waypoint: ${waypoint}. Please use 4-letter ICAO codes.`);
            return;
        }
    }
    
    analyzeRoute({
        departure: departure,
        arrival: arrival,
        waypoints: waypointList,
        departure_time: departureTime
    });
}

function handleIndividualSubmit(event) {
    event.preventDefault();
    
    const airportCode = document.getElementById('airportCode').value.trim();
    
    if (!validateICAOCode(airportCode)) {
        showError('Please enter a valid 4-letter ICAO airport code');
        return;
    }
    
    const reportTypes = [];
    if (document.getElementById('metarCheck').checked) reportTypes.push('METAR');
    if (document.getElementById('tafCheck').checked) reportTypes.push('TAF');
    if (document.getElementById('pirepCheck').checked) reportTypes.push('PIREP');
    
    if (reportTypes.length === 0) {
        showError('Please select at least one report type');
        return;
    }
    
    getIndividualWeather(airportCode, reportTypes);
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('flightPlanText').value = e.target.result;
    };
    reader.readAsText(file);
}

function analyzeFlightPlan() {
    const flightPlanText = document.getElementById('flightPlanText').value.trim();
    
    if (!flightPlanText) {
        showError('Please upload a flight plan file or paste flight plan text');
        return;
    }
    
    analyzeRoute({
        flight_plan_text: flightPlanText
    });
}

function analyzeRoute(routeData) {
    showLoading();
    hideResults();
    
    fetch('/api/flight-plan/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(routeData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.error) {
            showErrorMessage(data.error);
            return;
        }
        
        currentWeatherData = data.weather_data;
        currentBriefing = data.briefing;
        
        displayBriefingResults(data);
        updateQuickSummary(data);
    })
    .catch(error => {
        hideLoading();
        showError('Failed to fetch weather data: ' + error.message);
    });
}

function getIndividualWeather(airportCode, reportTypes) {
    showLoading();
    hideResults();
    
    fetch('/api/weather/individual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            airport_code: airportCode,
            report_types: reportTypes
        })
    })
    .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.error) {
                showErrorMessage(data.error);
                return;
            }
            displayIndividualResults(data, airportCode);
        })
    .catch(error => {
        hideLoading();
        showErrorMessage('Failed to fetch weather data: ' + error.message);
    });
}

function displayBriefingResults(data) {
    const briefingResults = document.getElementById('briefingResults');
    const individualResults = document.getElementById('individualResults');
    const notamCard = document.getElementById('notamCard');
    
    // Hide individual results, show briefing
    individualResults.classList.add('d-none');
    briefingResults.classList.remove('d-none');
    
    // Hide NOTAM card initially
    if (notamCard) {
        notamCard.style.display = 'none';
    }
    
    // Update NLP analysis sections
    if (data.nlp_analysis) {
        displayNLPAnalysis(data.nlp_analysis);
    }
    
    // Display NOTAM data right after pilot actions, before visualizations
    if (data.notam_data) {
        displayNotamData(data.notam_data);
    }
    
    // Traditional briefing section removed - no need to update category badge
    
    // Create visualizations
    if (data.visualizations) {
        createWindChart(data.visualizations.wind_chart);
        createVisibilityChart(data.visualizations.visibility_chart);
        createRouteMap(data.visualizations.route_map);
        createWeatherTimeline(data.visualizations.weather_timeline);
    }
    
    // Display detailed airport weather
    displayAirportDetails(data.weather_data, data.airports, data.parsed_weather_data);
    
    // Display route information
    if (data.route_info) {
        displayRouteInfo(data.route_info);
    }
    
    // Scroll to results
    briefingResults.scrollIntoView({ behavior: 'smooth' });
}
function displayNLPAnalysis(nlpData) {
    // Display executive summary
    const executiveSummary = document.getElementById('executiveSummary');
    executiveSummary.innerHTML = `
        <div class="alert alert-info mb-3">
            <h6><i class="fas fa-lightbulb"></i> Executive Summary</h6>
            <p class="mb-0">${nlpData.executive_summary || 'No summary available'}</p>
        </div>
    `;
    
    // Display risk assessment
    const riskBadge = document.getElementById('riskAssessment');
    const riskLevel = nlpData.risk_assessment || 'UNKNOWN';
    riskBadge.textContent = `${riskLevel} RISK`;
    riskBadge.className = `badge ${getRiskBadgeClass(riskLevel)}`;
    
    // Display decision factors
    const decisionFactors = document.getElementById('decisionFactors');
    if (nlpData.decision_factors && nlpData.decision_factors.length > 0) {
        decisionFactors.innerHTML = `
            <h6><i class="fas fa-exclamation-triangle"></i> Key Decision Factors</h6>
            <ul class="list-group list-group-flush">
                ${nlpData.decision_factors.map(factor => `
                    <li class="list-group-item px-0 py-2">
                        <i class="fas fa-arrow-right text-warning me-2"></i>${factor}
                    </li>
                `).join('')}
            </ul>
        `;
    } else {
        decisionFactors.innerHTML = '<p class="text-muted">No critical decision factors identified.</p>';
    }
    
    // Display pilot recommendations
    const pilotRecommendations = document.getElementById('pilotRecommendations');
    if (nlpData.pilot_recommendations && nlpData.pilot_recommendations.length > 0) {
        pilotRecommendations.innerHTML = `
            <div class="row">
                ${nlpData.pilot_recommendations.map((rec, index) => `
                    <div class="col-md-6 mb-2">
                        <div class="d-flex align-items-start">
                            <div class="badge bg-primary me-2 mt-1">${index + 1}</div>
                            <div class="flex-grow-1">
                                <span class="recommendation-text">${rec}</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        pilotRecommendations.innerHTML = '<p class="text-muted">No specific recommendations at this time.</p>';
    }
    
    // Phase guidance removed as requested
}

function getRiskBadgeClass(riskLevel) {
    switch (riskLevel.toUpperCase()) {
        case 'HIGH':
            return 'bg-danger';
        case 'MODERATE':
            return 'bg-warning text-dark';
        case 'LOW':
            return 'bg-info';
        case 'MINIMAL':
            return 'bg-success';
        default:
            return 'bg-secondary';
    }
}

function displayIndividualResults(data, airportCode) {
    const briefingResults = document.getElementById('briefingResults');
    const individualResults = document.getElementById('individualResults');
    
    // Hide briefing results, show individual
    briefingResults.classList.add('d-none');
    individualResults.classList.remove('d-none');
    
    const weatherDataDiv = document.getElementById('individualWeatherData');
    weatherDataDiv.innerHTML = generateIndividualWeatherHTML(data, airportCode);
    
    // Scroll to results
    individualResults.scrollIntoView({ behavior: 'smooth' });
}

function generateBriefingSummaryHTML(briefing) {
    let html = `
        <div class="row">
            <div class="col-md-8">
                <h6>Route Summary</h6>
                <p>${briefing.route_summary || 'No summary available'}</p>
                
                ${briefing.route_hazards && briefing.route_hazards.length > 0 ? `
                <h6>Route Hazards</h6>
                <div class="hazard-alert ${briefing.overall_category === 'SEVERE' ? 'severe' : ''}">
                    <i class="fas fa-exclamation-triangle"></i>
                    <ul class="mb-0">
                        ${briefing.route_hazards.map(hazard => `<li>${hazard}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${briefing.recommendations && briefing.recommendations.length > 0 ? `
                <h6>Recommendations</h6>
                <ul class="recommendation-list">
                    ${briefing.recommendations.map(rec => `<li class="${getRecommendationClass(rec)}">${rec}</li>`).join('')}
                </ul>
                ` : ''}
            </div>
            <div class="col-md-4">
                ${briefing.critical_airports && briefing.critical_airports.length > 0 ? `
                <h6>Critical Airports</h6>
                ${briefing.critical_airports.map(airport => `
                    <div class="airport-card ${airport.category.toLowerCase()}">
                        <div class="card-body p-2">
                            <h6 class="card-title mb-1">${airport.airport}</h6>
                            <span class="badge badge-${airport.category.toLowerCase()}">${airport.category}</span>
                            ${airport.issues.map(issue => `<div class="small text-muted mt-1">${issue}</div>`).join('')}
                        </div>
                    </div>
                `).join('')}
                ` : '<p class="text-muted">No critical airports identified</p>'}
            </div>
        </div>
    `;
    
    return html;
}

function generateIndividualWeatherHTML(data, airportCode) {
    // Use parsed data if available
    const parsedData = data.parsed_data && data.parsed_data[airportCode] ? data.parsed_data[airportCode] : null;
    
    let html = `
        <div class="text-center mb-4">
            <h5><i class="fas fa-cloud"></i> ${airportCode} Weather Report</h5>
        </div>
    `;
    
    if (data.metar) {
        html += '<div id="metar-section">' + generateMETARHTML(data.metar, parsedData?.metar) + '</div>';
    }
    
    if (data.taf) {
        html += '<div id="taf-section">' + generateTAFHTML(data.taf, parsedData?.taf) + '</div>';
    }
    
    if (data.pirep && data.pirep.length > 0) {
        html += generatePIREPHTML(parsedData?.pireps || data.pirep, airportCode);
    } else {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6><i class="fas fa-plane"></i> PIREPs (Pilot Reports)</h6>
                </div>
                <div class="card-body">
                    <div class="alert alert-warning py-2">
                        <i class="fas fa-info-circle me-2"></i>
                        No recent pilot reports available for this airport. PIREPs are voluntary reports from pilots and may not always be available.
                    </div>
                    <div class="text-center mt-3">
                        <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showPirepModal('${airportCode}')">
                            <i class="fas fa-search"></i> Search PIREPs
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (data.notam && data.notam.length > 0) {
        html += generateNOTAMHTML(data.notam, data.notam_summary);
    }
    
    if (data.analysis) {
        html += generateAnalysisHTML(data.analysis);
    }
    
    return html;
}

function generateMETARHTML(metar, parsedMetar = null) {
    const metarId = 'metar-' + Math.random().toString(36).substr(2, 9);
    
    return `
        <div class="card mb-3">
            <div class="card-header">
                <h6><i class="fas fa-thermometer-half"></i> METAR</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <div class="weather-metric">
                            <span class="metric-label">Raw Text:</span>
                            <code class="metric-value">${metar.raw_text || 'N/A'}</code>
                        </div>
                        <div class="weather-metric">
                            <span class="metric-label">Observation Time:</span>
                            <span class="metric-value">${formatDateTime(metar.observation_time)}</span>
                        </div>
                        <div class="weather-metric">
                            <span class="metric-label">Flight Category:</span>
                            <span class="badge flight-category-${(metar.flight_category || 'unknown').toLowerCase()}">${metar.flight_category || 'UNKNOWN'}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="weather-metric">
                            <span class="metric-label">Visibility:</span>
                            <span class="metric-value">${metar.visibility || 'N/A'} SM</span>
                        </div>
                        <div class="weather-metric">
                            <span class="metric-label">Wind:</span>
                            <span class="metric-value">${formatWind(metar)}</span>
                        </div>
                        <div class="weather-metric">
                            <span class="metric-label">Temperature:</span>
                            <span class="metric-value">${metar.temperature || 'N/A'}°C</span>
                        </div>
                        <div class="weather-metric">
                            <span class="metric-label">Altimeter:</span>
                            <span class="metric-value">${metar.altimeter || 'N/A'} inHg</span>
                        </div>
                    </div>
                </div>
                <div class="text-center mt-3">
                    <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showWeatherModal('metar', '${metar.raw_text || 'N/A'}', '${parsedMetar?.simplified || 'Simplified version not available'}')">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        </div>
    `;
}

function generateTAFHTML(taf, parsedTaf = null) {
    const summary = parseTAFSummary(taf.raw_text || '');
    
    return `
        <div class="card mb-3">
            <div class="card-header">
                <h6><i class="fas fa-calendar-alt"></i> TAF (Terminal Aerodrome Forecast)</h6>
            </div>
            <div class="card-body">
                <div class="weather-metric">
                    <span class="metric-label">Forecast Summary:</span>
                    <div class="metric-value">
                        <div class="alert alert-info py-2 mb-2">
                            ${summary}
                        </div>
                    </div>
                </div>
                <div class="weather-metric">
                    <span class="metric-label">Valid Period:</span>
                    <span class="metric-value">${formatDateTime(taf.valid_time_from)} - ${formatDateTime(taf.valid_time_to)}</span>
                </div>
                <div class="weather-metric">
                    <span class="metric-label">Raw Text:</span>
                    <code class="metric-value">${taf.raw_text || 'N/A'}</code>
                </div>
                <div class="text-center mt-3">
                    <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showWeatherModal('taf', '${taf.raw_text || 'N/A'}', '${parsedTaf?.simplified || 'Simplified version not available'}')">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                </div>
            </div>
        </div>
    `;
}

function parseTAFSummary(rawTAF) {
    if (!rawTAF) return 'No forecast data available';
    
    const taf = rawTAF.toUpperCase();
    let summary = [];
    
    // Check for weather phenomena
    if (taf.includes('TS')) {
        summary.push('⛈️ Thunderstorms forecast');
    }
    if (taf.includes('RA') || taf.includes('SN')) {
        summary.push('🌧️ Precipitation expected');
    }
    if (taf.includes('FG') || taf.includes('BR')) {
        summary.push('🌫️ Fog/mist conditions');
    }
    if (taf.includes('TEMPO')) {
        summary.push('⏱️ Temporary conditions expected');
    }
    if (taf.includes('PROB')) {
        summary.push('📊 Probability conditions forecast');
    }
    if (taf.includes('BECMG')) {
        summary.push('🔄 Changing conditions expected');
    }
    
    // Check for wind information
    const windMatch = taf.match(/(\d{3})(\d{2,3})(G\d{2,3})?KT/);
    if (windMatch) {
        const windDir = windMatch[1];
        const windSpeed = windMatch[2];
        const gust = windMatch[3] ? windMatch[3].replace('G', '') : null;
        
        if (gust && parseInt(gust) > 25) {
            summary.push(`💨 Strong wind gusts to ${gust} knots`);
        } else if (parseInt(windSpeed) > 20) {
            summary.push(`💨 Strong winds ${windSpeed} knots`);
        }
    }
    
    if (summary.length === 0) {
        summary.push('☀️ Generally favorable conditions forecast');
    }
    
    return summary.join('<br>');
}

function generatePIREPHTML(pireps, airportCode = null) {
    let html = `
        <div class="card mb-3">
            <div class="card-header">
                <h6><i class="fas fa-plane"></i> PIREPs (Pilot Reports)</h6>
            </div>
            <div class="card-body">
    `;
    
    if (pireps && pireps.length > 0) {
        pireps.forEach((pirep, index) => {
            html += `
                <div class="mb-3 ${index < pireps.length - 1 ? 'border-bottom pb-3' : ''}">
                    <div class="weather-metric">
                        <span class="metric-label">Report:</span>
                        <code class="metric-value">${pirep.raw_text || pirep.raw || 'N/A'}</code>
                    </div>
                    <div class="weather-metric">
                        <span class="metric-label">Time:</span>
                        <span class="metric-value">${formatDateTime(pirep.observation_time || pirep.receipt_time)}</span>
                    </div>
                    ${pirep.aircraft_type ? `
                    <div class="weather-metric">
                        <span class="metric-label">Aircraft:</span>
                        <span class="metric-value">${pirep.aircraft_type}</span>
                    </div>
                    ` : ''}
                    ${pirep.altitude ? `
                    <div class="weather-metric">
                        <span class="metric-label">Altitude:</span>
                        <span class="metric-value">${pirep.altitude} ft</span>
                    </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += `
                <div class="text-center mt-3">
                    <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showPirepModal('${airportCode || 'Unknown'}')">
                        <i class="fas fa-list"></i> View All PIREPs
                    </button>
                </div>
        `;
    } else {
        html += `
            <div class="alert alert-warning py-2">
                <i class="fas fa-info-circle me-2"></i>
                No recent pilot reports available. PIREPs are voluntary reports from pilots and may not always be available.
            </div>
            <div class="text-center mt-3">
                <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showPirepModal('${airportCode || 'Unknown'}')">
                    <i class="fas fa-search"></i> Search PIREPs
                </button>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

function generateAnalysisHTML(analysis) {
    return `
        <div class="card mb-3">
            <div class="card-header">
                <h6><i class="fas fa-chart-bar"></i> Weather Analysis</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <div class="weather-metric">
                            <span class="metric-label">Category:</span>
                            <span class="badge badge-${analysis.category.toLowerCase()}">${analysis.category}</span>
                        </div>
                        <div class="weather-metric">
                            <span class="metric-label">Summary:</span>
                            <span class="metric-value">${analysis.summary}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        ${analysis.key_factors && analysis.key_factors.length > 0 ? `
                        <h6>Key Factors:</h6>
                        <ul class="small">
                            ${analysis.key_factors.map(factor => `<li>${factor}</li>`).join('')}
                        </ul>
                        ` : ''}
                    </div>
                </div>
                
                ${analysis.hazards && analysis.hazards.length > 0 ? `
                <div class="hazard-alert mt-3">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>Hazards:</strong>
                    <ul class="mb-0 mt-2">
                        ${analysis.hazards.map(hazard => `<li>${hazard}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
                
                ${analysis.recommendations && analysis.recommendations.length > 0 ? `
                <h6 class="mt-3">Recommendations:</h6>
                <ul class="recommendation-list">
                    ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
                ` : ''}
            </div>
        </div>
    `;
}

function displayAirportDetails(weatherData, airports, parsedWeatherData = null) {
    const detailsDiv = document.getElementById('airportDetails');
    let html = '';
    
    airports.forEach(airport => {
        const data = weatherData[airport];
        const parsedData = parsedWeatherData && parsedWeatherData[airport] ? parsedWeatherData[airport] : null;
        
        if (data && data.metar) {
            const analysis = data.analysis || {};
            
            html += `
                <div class="airport-card ${analysis.category ? analysis.category.toLowerCase() : ''} mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">${airport}</h6>
                        <span class="badge badge-${analysis.category ? analysis.category.toLowerCase() : 'secondary'}">${analysis.category || 'UNKNOWN'}</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-sm-6">
                                <small class="text-muted">Visibility:</small> ${data.metar.visibility || 'N/A'} SM<br>
                                <small class="text-muted">Wind:</small> ${formatWind(data.metar)}<br>
                            </div>
                            <div class="col-sm-6">
                                <small class="text-muted">Ceiling:</small> ${data.metar.ceiling || 'N/A'} ft<br>
                                <small class="text-muted">Flight Cat:</small> ${data.metar.flight_category || 'N/A'}<br>
                            </div>
                        </div>
                        ${parsedData?.metar?.simplified ? `
                        <div class="alert alert-info mt-2 py-2">
                            <i class="fas fa-language me-2"></i>
                            <strong>Simplified:</strong> ${parsedData.metar.simplified}
                        </div>
                        ` : ''}
                        <div class="text-center mt-3">
                            <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showWeatherModal('metar', '${data.metar.raw_text || 'N/A'}', '${parsedData?.metar?.simplified || 'Simplified version not available'}')">
                                <i class="fas fa-thermometer-half"></i> Show Raw METAR
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm me-2" onclick="showPirepModal('${airport}')">
                                <i class="fas fa-plane"></i> Show PIREPs
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="showWeatherModal('taf', '${data.taf?.raw_text || 'No TAF data available'}', '${parsedData?.taf?.simplified || 'Simplified version not available'}')">
                                <i class="fas fa-calendar-alt"></i> Show Raw TAF
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    detailsDiv.innerHTML = html || '<p class="text-muted">No detailed weather data available</p>';
}

function createWindChart(chartData) {
    const container = document.getElementById('windChart');
    if (!container) {
        console.error('Wind chart container not found');
        return;
    }
    
    if (chartData && !chartData.error) {
        try {
            const plotData = JSON.parse(chartData);
            Plotly.newPlot('windChart', plotData.data, plotData.layout, {responsive: true});
            console.log('Wind chart created successfully');
        } catch (error) {
            console.error('Error creating wind chart:', error);
            container.innerHTML = '<div class="alert alert-warning">Error loading wind chart</div>';
        }
    } else {
        container.innerHTML = '<div class="alert alert-info">No wind data available</div>';
    }
}

function createVisibilityChart(chartData) {
    const container = document.getElementById('visibilityChart');
    if (!container) {
        console.error('Visibility chart container not found');
        return;
    }
    
    if (chartData && !chartData.error) {
        try {
            const plotData = JSON.parse(chartData);
            Plotly.newPlot('visibilityChart', plotData.data, plotData.layout, {responsive: true});
            console.log('Visibility chart created successfully');
        } catch (error) {
            console.error('Error creating visibility chart:', error);
            container.innerHTML = '<div class="alert alert-warning">Error loading visibility chart</div>';
        }
    } else {
        container.innerHTML = '<div class="alert alert-info">No visibility data available</div>';
    }
}

function createRouteMap(mapData) {
    const container = document.getElementById('routeMap');
    if (!container) {
        console.error('Route map container not found');
        return;
    }
    
    if (mapData && !mapData.includes('Error')) {
        container.innerHTML = mapData;
        console.log('Route map created successfully');
    } else {
        container.innerHTML = '<div class="alert alert-warning">Error loading route map</div>';
    }
}

function createWeatherTimeline(chartData) {
    const container = document.getElementById('weatherTimeline');
    if (!container) {
        console.error('Weather timeline container not found');
        return;
    }
    
    if (chartData && !chartData.error) {
        try {
            const plotData = JSON.parse(chartData);
            Plotly.newPlot('weatherTimeline', plotData.data, plotData.layout, {responsive: true});
            console.log('Weather timeline created successfully');
        } catch (error) {
            console.error('Error creating weather timeline:', error);
            container.innerHTML = '<div class="alert alert-warning">Error loading weather timeline</div>';
        }
    } else {
        container.innerHTML = '<div class="alert alert-info">No timeline data available</div>';
    }
}

function updateQuickSummary(data) {
    const summaryDiv = document.getElementById('quickSummary');
    const briefing = data.briefing;
    
    let html = `
        <div class="summary-item">
            <span>Overall Condition:</span>
            <span class="summary-category badge-${briefing.overall_category.toLowerCase()}">${briefing.overall_category}</span>
        </div>
        <div class="summary-item">
            <span>Airports:</span>
            <span>${data.airports.length}</span>
        </div>
    `;
    
    if (briefing.critical_airports && briefing.critical_airports.length > 0) {
        html += `
            <div class="summary-item">
                <span>Critical Airports:</span>
                <span class="text-warning">${briefing.critical_airports.length}</span>
            </div>
        `;
    }
    
    summaryDiv.innerHTML = html;
}

// Utility functions
function validateICAOCode(code) {
    return /^[A-Z]{4}$/.test(code);
}

function formatWind(metar) {
    if (!metar.wind_speed) return 'Calm';
    
    let windStr = `${metar.wind_direction || 'VRB'}° at ${metar.wind_speed} kt`;
    if (metar.wind_gust) {
        windStr += ` G${metar.wind_gust} kt`;
    }
    return windStr;
}

function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return 'N/A';
    
    try {
        const date = new Date(dateTimeStr);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'UTC',
            timeZoneName: 'short'
        });
    } catch (e) {
        return dateTimeStr;
    }
}

function getRecommendationClass(recommendation) {
    const lower = recommendation.toLowerCase();
    if (lower.includes('delay') || lower.includes('caution') || lower.includes('emergency')) {
        return 'critical';
    } else if (lower.includes('monitor') || lower.includes('consider')) {
        return 'warning';
    }
    return '';
}

function showLoading() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
}

function hideLoading() {
    document.getElementById('loadingSpinner').classList.add('d-none');
}

function showErrorMessage(message) {
    // Remove any existing error messages
    const existingError = document.querySelector('.error-alert');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error message
    const errorHTML = `
        <div class="alert alert-danger alert-dismissible fade show error-alert" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Insert error message at the top of the main content
    const mainContent = document.querySelector('.container-fluid');
    if (mainContent) {
        mainContent.insertAdjacentHTML('afterbegin', errorHTML);
        
        // Scroll to error message
        document.querySelector('.error-alert').scrollIntoView({ behavior: 'smooth' });
    }
}

function hideResults() {
    document.getElementById('briefingResults').classList.add('d-none');
    document.getElementById('individualResults').classList.add('d-none');
}

function showError(message) {
    // Create or update error message
    let errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'errorMessage';
        errorDiv.className = 'error-message';
        document.querySelector('.col-md-8').insertBefore(errorDiv, document.querySelector('.col-md-8').firstChild);
    }
    
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    errorDiv.scrollIntoView({ behavior: 'smooth' });
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (errorDiv) {
            errorDiv.remove();
        }
    }, 5000);
}

function loadSampleData() {
    // Optionally load some sample data or tips for first-time users
    const quickSummary = document.getElementById('quickSummary');
    quickSummary.innerHTML = `
        <div class="text-center">
            <i class="fas fa-info-circle text-primary mb-2" style="font-size: 2rem;"></i>
            <p class="mb-1"><strong>Welcome to Aviation Weather Briefing</strong></p>
            <p class="small text-muted mb-0">Enter your flight details to get comprehensive weather analysis</p>
        </div>
    `;
}

function displayRouteInfo(routeInfo) {
    // Find a good place to display route info - let's add it to the NLP section
    const executiveSummary = document.getElementById('executiveSummary');
    if (executiveSummary) {
        // Remove any existing route info first
        const existingRouteInfo = document.querySelector('.route-info-alert');
        if (existingRouteInfo) {
            existingRouteInfo.remove();
        }
        
        const routeInfoHTML = `
            <div class="alert alert-success mb-3 route-info-alert">
                <h6><i class="fas fa-route"></i> Route Information</h6>
                <div class="row">
                    <div class="col-md-6">
                        <strong>Distance:</strong> ${routeInfo.total_distance_nm} nautical miles<br>
                        <strong>Route:</strong> ${routeInfo.departure_airport} → ${routeInfo.arrival_airport}
                        ${routeInfo.waypoints_count > 0 ? ` (${routeInfo.waypoints_count} waypoints)` : ''}
                    </div>
                    <div class="col-md-6">
                        <strong>Current Time (UTC):</strong> ${routeInfo.current_utc_time}<br>
                        <strong>Analysis Generated:</strong> Just now
                    </div>
                </div>
            </div>
        `;
        
        // Insert route info before the executive summary
        executiveSummary.insertAdjacentHTML('beforebegin', routeInfoHTML);
    }
}

function displayNotamData(notamData) {
    // Use the dedicated NOTAM card section
    const notamCard = document.getElementById('notamCard');
    const notamContent = document.getElementById('notamContent');
    
    if (notamCard && notamContent && notamData) {
        let notamHTML = '';
        
        for (const [airport, data] of Object.entries(notamData)) {
            const summary = data.summary;
            const notams = data.notams;
            
            notamHTML += `
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0"><i class="fas fa-plane me-2"></i>${airport}</h6>
                        <span class="badge bg-info">${summary.total_count} NOTAMs</span>
                    </div>
                    <div class="alert alert-light py-2 mb-2">
                        <small class="text-muted">${summary.summary_text}</small>
                    </div>
                    ${generateNotamSummaryHTML(summary)}
                    ${notams.length > 0 ? generateNotamListHTML(notams, `route-${airport}`) : '<p class="text-muted">No active NOTAMs</p>'}
                </div>
            `;
        }
        
        // Update content and show the card
        notamContent.innerHTML = notamHTML;
        notamCard.style.display = 'block';
    }
}

function generateNOTAMHTML(notams, summary) {
    return `
        <div class="card mb-3">
            <div class="card-header">
                <h6><i class="fas fa-exclamation-triangle"></i> NOTAMs (Notices to Airmen)</h6>
                <small class="text-muted">${summary ? summary.summary_text : `${notams.length} NOTAMs`}</small>
            </div>
            <div class="card-body">
                ${summary ? generateNotamSummaryHTML(summary) : ''}
                ${generateNotamListHTML(notams, 'individual')}
            </div>
        </div>
    `;
}

function generateNotamSummaryHTML(summary) {
    if (!summary || summary.total_count === 0) return '';
    
    const categoryBadges = Object.entries(summary.categories || {})
        .map(([category, count]) => `<span class="badge bg-secondary me-1">${category}: ${count}</span>`)
        .join('');
    
    return `
        <div class="row mb-3">
            <div class="col-md-6">
                <strong>Summary:</strong><br>
                <span class="badge bg-info me-2">${summary.total_count} Total</span>
                ${summary.high_severity_count > 0 ? `<span class="badge bg-danger me-2">${summary.high_severity_count} High Severity</span>` : ''}
                ${summary.operational_impact_count > 0 ? `<span class="badge bg-warning me-2">${summary.operational_impact_count} Operational Impact</span>` : ''}
            </div>
            <div class="col-md-6">
                <strong>Categories:</strong><br>
                ${categoryBadges}
            </div>
        </div>
    `;
}

function generateNotamListHTML(notams, contextPrefix = '') {
    if (!notams || notams.length === 0) {
        return '<div class="alert alert-info py-2"><i class="fas fa-info-circle me-2"></i>No active NOTAMs for this airport.</div>';
    }
    
    let html = '<div class="notam-list">';
    
    notams.forEach((notam, index) => {
        const severityClass = notam.severity === 'HIGH' ? 'border-danger' : 
                            notam.severity === 'MEDIUM' ? 'border-warning' : 'border-info';
        
        const categoryIcon = getNotamCategoryIcon(notam.category);
        
        // Create unique ID using context prefix, notam ID, and index
        const uniqueId = `notam-${contextPrefix}-${notam.id || 'unknown'}-${index}`;
        
        html += `
            <div class="card mb-2 ${severityClass}">
                <div class="card-header py-2">
                    <div class="d-flex justify-content-between align-items-center flex-wrap">
                        <span class="d-flex align-items-center flex-grow-1 me-2">
                            <i class="${categoryIcon} me-2 flex-shrink-0"></i>
                            <span class="text-truncate">
                                <strong>${notam.id}</strong> - ${notam.category}
                            </span>
                        </span>
                        <span class="badge bg-${notam.severity === 'HIGH' ? 'danger' : notam.severity === 'MEDIUM' ? 'warning' : 'info'} flex-shrink-0">${notam.severity}</span>
                    </div>
                </div>
                <div class="card-body py-2">
                    <p class="mb-1"><strong>${notam.summary}</strong></p>
                    <small class="text-muted">
                        ${notam.start_time ? `From: ${notam.start_time}` : ''} 
                        ${notam.end_time ? `To: ${notam.end_time}` : ''}
                    </small>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#${uniqueId}" aria-expanded="false">
                            Show Full Text
                        </button>
                    </div>
                    <div class="collapse mt-2" id="${uniqueId}">
                        <div class="alert alert-light py-2">
                            <small><code>${notam.raw_text}</code></small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function getNotamCategoryIcon(category) {
    const icons = {
        'RUNWAY': 'fas fa-road',
        'NAVIGATION': 'fas fa-compass',
        'LIGHTING': 'fas fa-lightbulb',
        'AIRSPACE': 'fas fa-cloud',
        'CONSTRUCTION': 'fas fa-hard-hat',
        'WEATHER_SERVICES': 'fas fa-broadcast-tower',
        'OTHER': 'fas fa-info-circle'
    };
    return icons[category] || 'fas fa-info-circle';
}

// Helper function for PIREP severity colors (kept for compatibility)
function getPirepSeverityColor(severityColor) {
    const colorMap = {
        'success': 'success',
        'info': 'info', 
        'warning': 'warning',
        'danger': 'danger',
        'secondary': 'secondary'
    };
    return colorMap[severityColor] || 'secondary';
}

// New modal functions for weather data display

function showWeatherModal(type, rawData, simplifiedData) {
    const modal = createWeatherModal(type, rawData, simplifiedData);
    document.body.appendChild(modal);
    
    // Initialize and show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

function createWeatherModal(type, rawData, simplifiedData) {
    const modalId = 'weatherModal-' + Math.random().toString(36).substr(2, 9);
    const title = type.toUpperCase() === 'METAR' ? 'METAR Data' : 
                  type.toUpperCase() === 'TAF' ? 'TAF Data' : 'Weather Data';
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = modalId;
    modal.tabIndex = -1;
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-cloud"></i> ${title}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <div class="btn-group w-100" role="group">
                            <button type="button" class="btn btn-outline-secondary" onclick="toggleModalView('${modalId}', 'raw')">
                                <i class="fas fa-code"></i> Raw Data
                            </button>
                            <button type="button" class="btn btn-outline-secondary active" onclick="toggleModalView('${modalId}', 'simplified')">
                                <i class="fas fa-language"></i> Simplified
                            </button>
                        </div>
                    </div>
                    <div id="${modalId}-raw" class="modal-content-section d-none">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Raw ${type.toUpperCase()}</h6>
                            </div>
                            <div class="card-body">
                                <pre class="bg-light p-3 rounded"><code>${rawData}</code></pre>
                            </div>
                        </div>
                    </div>
                    <div id="${modalId}-simplified" class="modal-content-section">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Simplified ${type.toUpperCase()}</h6>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-info">
                                    <i class="fas fa-language me-2"></i>
                                    ${simplifiedData}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

function showPirepModal(airportCode) {
    const modal = createPirepModal(airportCode);
    document.body.appendChild(modal);
    
    // Initialize and show modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Fetch PIREPs
    fetchPireps(airportCode, modal.id);
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

function createPirepModal(airportCode) {
    const modalId = 'pirepModal-' + Math.random().toString(36).substr(2, 9);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = modalId;
    modal.tabIndex = -1;
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-plane"></i> PIREPs for ${airportCode}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <label class="form-label">Max Age (hours):</label>
                            <select class="form-select form-select-sm d-inline-block w-auto ms-2" id="${modalId}-age">
                                <option value="1">1 hour</option>
                                <option value="3" selected>3 hours</option>
                                <option value="6">6 hours</option>
                                <option value="12">12 hours</option>
                            </select>
                        </div>
                        <div>
                            <label class="form-label">Max Distance (NM):</label>
                            <select class="form-select form-select-sm d-inline-block w-auto ms-2" id="${modalId}-distance">
                                <option value="25">25 NM</option>
                                <option value="50" selected>50 NM</option>
                                <option value="100">100 NM</option>
                                <option value="200">200 NM</option>
                            </select>
                        </div>
                        <button class="btn btn-secondary btn-sm" onclick="refreshPireps('${airportCode}', '${modalId}')">
                            <i class="fas fa-refresh"></i> Refresh
                        </button>
                    </div>
                    <div id="${modalId}-content">
                        <div class="text-center">
                            <div class="spinner-border text-secondary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Loading PIREPs...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

function toggleModalView(modalId, viewType) {
    // Hide all content sections
    const rawSection = document.getElementById(modalId + '-raw');
    const simplifiedSection = document.getElementById(modalId + '-simplified');
    
    if (rawSection) rawSection.classList.add('d-none');
    if (simplifiedSection) simplifiedSection.classList.add('d-none');
    
    // Show selected section
    const targetSection = document.getElementById(modalId + '-' + viewType);
    if (targetSection) targetSection.classList.remove('d-none');
    
    // Update button states
    const buttons = document.querySelectorAll(`[onclick*="${modalId}"]`);
    buttons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.onclick.toString().includes(`'${viewType}'`)) {
            btn.classList.add('active');
        }
    });
}

function fetchPireps(airportCode, modalId) {
    const ageSelect = document.getElementById(modalId + '-age');
    const distanceSelect = document.getElementById(modalId + '-distance');
    const contentDiv = document.getElementById(modalId + '-content');
    
    const maxAge = ageSelect ? ageSelect.value : 3;
    const maxDistance = distanceSelect ? distanceSelect.value : 50;
    
    fetch(`/api/pireps/${airportCode}?max_age_hours=${maxAge}&max_distance_nm=${maxDistance}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                contentDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> Error: ${data.error}
                    </div>
                `;
                return;
            }
            
            displayPirepList(data, contentDiv);
        })
        .catch(error => {
            contentDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> Error loading PIREPs: ${error.message}
                </div>
            `;
        });
}

function displayPirepList(data, contentDiv) {
    if (!data.pireps || data.pireps.length === 0) {
        contentDiv.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> No PIREPs found within the specified criteria.
                <br><small>Filters: ${data.max_age_hours || 3} hours, ${data.max_distance_nm || 50} NM</small>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3">
            <span class="badge bg-info">${data.count} PIREPs found</span>
            <small class="text-muted ms-2">
                Filtered by: ${data.max_age_hours}h age, ${data.max_distance_nm}NM distance
            </small>
        </div>
    `;
    
    // Sort PIREPs by time (newest first) then by severity (highest first)
    const sortedPireps = data.pireps.sort((a, b) => {
        // First sort by age (newer first)
        const ageDiff = (a.age_hours || 0) - (b.age_hours || 0);
        if (ageDiff !== 0) return ageDiff;
        
        // Then by severity (higher first)
        return (b.severity?.level || 0) - (a.severity?.level || 0);
    });
    
    sortedPireps.forEach((pirep, index) => {
        const pirepId = 'modal-pirep-' + index;
        
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-secondary">${pirep.severity?.description || 'Unknown'}</span>
                            ${pirep.age_hours ? `<small class="text-muted ms-2">${Math.round(pirep.age_hours * 10) / 10}h ago</small>` : ''}
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary" onclick="togglePirepModalDisplay('${pirepId}', 'raw', this)">
                                <i class="fas fa-code"></i> Raw
                            </button>
                            <button class="btn btn-outline-secondary active" onclick="togglePirepModalDisplay('${pirepId}', 'simplified', this)">
                                <i class="fas fa-language"></i> Simplified
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div id="${pirepId}-raw" class="pirep-display d-none">
                        <div class="mb-2">
                            <strong>Raw Report:</strong>
                            <pre class="bg-light p-2 rounded mt-1"><code>${pirep.raw || pirep.raw_text || 'N/A'}</code></pre>
                        </div>
                        ${pirep.components?.aircraft ? `<p><strong>Aircraft:</strong> ${pirep.components.aircraft}</p>` : ''}
                        ${pirep.components?.altitude ? `<p><strong>Altitude:</strong> ${pirep.components.altitude} ft</p>` : ''}
                        ${pirep.components?.location ? `<p><strong>Location:</strong> ${pirep.components.location}</p>` : ''}
                    </div>
                    <div id="${pirepId}-simplified" class="pirep-display">
                        <div class="alert alert-info">
                            <i class="fas fa-language me-2"></i>
                            <strong>Simplified:</strong> ${pirep.simplified || 'Simplified version not available'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    contentDiv.innerHTML = html;
}

function togglePirepModalDisplay(pirepId, displayType, button) {
    // Hide all displays for this PIREP
    const rawDisplay = document.getElementById(pirepId + '-raw');
    const simplifiedDisplay = document.getElementById(pirepId + '-simplified');
    
    if (rawDisplay) rawDisplay.classList.add('d-none');
    if (simplifiedDisplay) simplifiedDisplay.classList.add('d-none');
    
    // Show selected display
    const targetDisplay = document.getElementById(pirepId + '-' + displayType);
    if (targetDisplay) targetDisplay.classList.remove('d-none');
    
    // Update button states in the same button group
    const buttonGroup = button.closest('.btn-group');
    if (buttonGroup) {
        buttonGroup.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    }
}

function refreshPireps(airportCode, modalId) {
    fetchPireps(airportCode, modalId);
}

// Utility functions for modal display
function scrollToWeatherSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

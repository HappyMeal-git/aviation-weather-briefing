# Aviation Weather Briefing System

A comprehensive web application that provides real-time aviation weather analysis and briefings for flight planning.

## ✈️ Features

- **🌍 Global Airport Support**: International airports worldwide (Mumbai ↔ Paris ↔ Dubai)
- **📡 Real-time Weather Data**: Live METAR, TAF, and PIREP data from aviationweather.gov
- **🎯 Intelligent Analysis**: Categorizes weather conditions as CLEAR, SIGNIFICANT, or SEVERE
- **📊 Interactive Visualizations**: 
  - Wind analysis charts with spikes
  - Visibility and ceiling analysis
  - Global route maps with weather overlays
  - Weather timeline forecasts with realistic variations
- **🤖 AI-Powered Summaries**: NLP-generated executive summaries and pilot recommendations
- **⏰ Time-Aware Analysis**: Considers departure time for relevant weather forecasts
- **📏 Distance Calculations**: Accurate nautical mile calculations
- **🕐 Live UTC Time**: Real-time UTC timestamps

## 🚀 Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Visualizations**: Plotly.js, Folium
- **Weather Data**: aviationweather.gov API
- **Styling**: Bootstrap 5
- **Maps**: Global coordinate database with 50+ major airports

## 📦 Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python run.py
   ```
4. Open your browser to `http://localhost:5001`

## 🎮 Usage

### Route Analysis
1. Enter departure and arrival airports (ICAO codes)
2. Optionally add waypoints
3. Set planned departure time
4. Click "Analyze Route" for comprehensive briefing

**Example Global Routes:**
- Mumbai to Paris: `VABB` → `LFPG` (via `OMDB`)
- New York to London: `KJFK` → `EGLL`
- Tokyo to Los Angeles: `RJTT` → `KLAX`

### Individual Airport Reports
1. Go to "Individual Weather" tab
2. Enter airport code (ICAO format)
3. Select report types (METAR, TAF, PIREP)
4. Get detailed weather analysis with TAF summaries

## 🔌 API Endpoints

- `GET /` - Main dashboard
- `POST /api/flight-plan/analyze` - Route weather analysis
- `POST /api/weather/individual` - Individual airport weather

## 📁 Project Structure

```
aviation-weather-briefing/
├── app.py                 # Main Flask application
├── weather_service.py     # Weather data fetching service
├── weather_analyzer.py    # Weather analysis and categorization
├── nlp_analyzer.py       # NLP summaries and recommendations
├── visualizations.py     # Interactive charts and maps
├── airport_coordinates.py # Global airport coordinate database
├── config.py             # Configuration settings
├── run.py               # Application runner
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
├── static/              # Static assets
│   ├── css/style.css    # Custom styling
│   └── js/main.js       # Frontend JavaScript
└── templates/           # HTML templates
    └── index.html       # Main dashboard
```

## ⚙️ Configuration

Set the `FLASK_ENV` environment variable:
- `development` - Debug mode enabled (default)
- `production` - Production optimized

## 🧪 Testing

The system includes comprehensive validation:
- ✅ API data accuracy verification
- ✅ Airport validation with error messages
- ✅ Weather categorization logic
- ✅ Global route mapping
- ✅ Timeline spike generation

## 🌟 Key Features Verified

- **Global Mapping**: Mumbai to Paris (3,776.2 nm) ✅
- **Weather Accuracy**: VFR→CLEAR, MVFR→SIGNIFICANT, LIFR→SEVERE ✅
- **Timeline Spikes**: Realistic variations based on weather conditions ✅
- **Error Handling**: Invalid airports show proper error messages ✅
- **Distance Calculations**: Accurate nautical mile calculations ✅

## 📄 License

This project is licensed under the MIT License.

---

**Ready for professional aviation weather briefing operations! 🛩️**

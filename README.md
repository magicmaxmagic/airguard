# AirGuard

Automatically detect intrusions in your apartment using noise detection.

## Project Structure

```
airguard/
│
├── backend/          # FastAPI backend server
│   ├── main.py       # API endpoints and server
│   ├── models.py     # Database models
│   ├── schemas.py    # Pydantic schemas
│   └── requirements.txt
│
├── client/           # Noise detection client
│   ├── noise_detector.py  # Client script to detect noise
│   └── requirements.txt
│
└── dashboard/        # Streamlit dashboard
    ├── app.py        # Dashboard application
    └── requirements.txt
```

## Components

### Backend
FastAPI-based REST API that receives noise events from clients and stores them in a SQLite database.

**Features:**
- RESTful API endpoints for creating and retrieving noise events
- SQLite database for event storage
- CORS enabled for dashboard access

**Endpoints:**
- `GET /` - API status
- `POST /events/` - Create a new noise event
- `GET /events/` - List all noise events
- `GET /events/{event_id}` - Get a specific event

### Client
Python script that monitors noise levels using the microphone and sends alerts to the backend when the threshold is exceeded.

**Features:**
- Real-time audio monitoring
- Configurable noise threshold
- Automatic event reporting to backend
- Device identification

### Dashboard
Streamlit-based web dashboard for visualizing noise events and monitoring intrusions.

**Features:**
- Real-time event monitoring
- Noise level charts and statistics
- Event distribution by location
- Auto-refresh capability

## Setup

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Client Setup

```bash
cd client
pip install -r requirements.txt
python noise_detector.py
```

**Configuration:**
Edit the following variables in `noise_detector.py`:
- `API_URL` - Backend API URL (default: http://localhost:8000/events/)
- `THRESHOLD` - Noise detection threshold (default: 2000)
- `LOCATION` - Device location (default: "living_room")

### Dashboard Setup

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`

## Usage

1. Start the backend server
2. Start one or more clients on devices with microphones
3. Open the dashboard to monitor noise events
4. Adjust threshold and settings as needed

## Requirements

- Python 3.8+
- Microphone access for client devices
- Network connectivity between client and backend

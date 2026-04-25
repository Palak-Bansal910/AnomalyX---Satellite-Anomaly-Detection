# Project Overview
This system simulates satellite telemetry, detects anomalies using a FastAPI backend, 
stores them in SQLite, and visualizes results in a Streamlit dashboard . 

## Project Structure
project/
│-- backend/
│   │-- core/
│   │-- routes/
│   │-- models/
│   │-- schemas/
│   │-- services/
│   │-- main.py
│-- dashboard/
│-- simulator/
│-- scripts/
│   │-- start_backend.bat
│   │-- start_dashboard.bat
│   │-- start_simulator.bat
│-- data/
│-- requirements.txt
│-- Dockerfile
│-- .env

# Setup & Installation
 # 1. Install dependencies
pip install -r backend/requirements.txt
 # 2.creation of .env file
DB_URL=sqlite:///./data/anomalies.db
# Start backend
bash scripts/start_backend.bat
# Start dashboard
bash scripts/start_dashboard.bat
# Start simulator
bash scripts/start_simulator.bat
# Docker
docker build -t anomaly-backend .
docker run -p 8000:8000 anomaly-backend

# Architecture Overview and Diagram
The system is composed of three main services that work together to detect and visualize satellite anomalies:

Simulator – generates synthetic satellite telemetry data

FastAPI Backend – processes telemetry, runs anomaly detection, and stores results

Dashboard – visualizes anomalies retrieved from the backend

SQLite Database – simple file-based storage for anomaly logs

                   ┌─────────────────────────┐
                   │     Simulator Service    │
                   │  (Generates Telemetry)   │
                   └──────────────┬───────────┘
                                  │  POST /data
                                  ▼
                     ┌────────────────────────┐
                     │     FastAPI Backend    │
                     │       (core/main.py)   │
                     │                        │
                     │ • Receives telemetry   │
                     │ • Runs anomaly model   │
                     │ • Stores anomalies     │
                     └──────────────┬─────────┘
                                    │
                     Writes to DB   │
                                    ▼
                   ┌──────────────────────────┐
                   │     SQLite Database      │
                   │  (data/anomalies.db)     │
                   └──────────────┬───────────┘
                                  │  GET /anomalies
                                  ▼
                     ┌──────────────────────────┐
                     │     Streamlit Dashboard   │
                     │ • Fetches anomalies       │
                     │ • Visual charts           │
                     └───────────────────────────┘
Architecture Explanation
1️⃣ Simulator Service

Generates continuous or batch telemetry data (temperature, voltage, vibration, etc.)

Sends the data to the backend using a REST API

Helps simulate real satellite sensor behavior for testing anomaly detection

2️⃣ FastAPI Backend

Central service that receives incoming telemetry

Passes data through the ML anomaly detection model

Flags abnormal readings

Stores anomalies inside the SQLite database

Provides API routes for the dashboard to fetch data

3️⃣ SQLite Database

Lightweight, file-based database

Perfect for hackathons or local execution

Stores timestamped anomaly logs

4️⃣ Streamlit Dashboard

Fetches processed anomaly data from the backend

Visualizes results through charts, graphs, tables

Helps track anomalies in near real time





# AI Traffic Signal Controller 🚦
Deep Reinforcement Learning for dynamic urban mobility, built with Python, TensorFlow, and SUMO.

## Table of Contents
- [Vision & Goals](#vision--goals)
- [Solution Highlights](#solution-highlights)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Simulation](#running-the-simulation)
- [Development Workflow](#development-workflow)
- [Testing & Quality](#testing--quality)
- [AI Model Integration](#ai-model-integration)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Team & Acknowledgments](#team--acknowledgments)

## Vision & Goals
Urban traffic congestion remains a persistent challenge, causing excessive vehicle wait times, fuel wastage, and environmental pollution. Traditional fixed-timer signals are rigid and blind to real-world, stochastic traffic patterns. This project replaces these outdated systems with an intelligent, autonomous controller that adapts in real-time. 

*"Empowering smarter city infrastructure, one dynamic intersection at a time."*

## Solution Highlights
* **AI-Powered Adaptation** – A Deep Q-Network (DQN) agent that perceives real-time intersection states to dynamically alter signal phases.
* **Massive Delay Reduction** – Achieved a 75% reduction in commuter delays (dropping average wait times from 78.5s to 18.2s).
* **Emergency Preemption** – A deterministic hybrid override module that slashes ambulance wait times from a fatal 120 seconds down to just 3 seconds.
* **High-Fidelity Simulation** – Built on the SUMO (Simulation of Urban MObility) engine, leveraging real-world map data for rigorous testing.

## Architecture Overview

| Layer | Purpose | Key Technologies |
| :--- | :--- | :--- |
| **Simulation Engine** | High-fidelity, microscopic traffic physics and real-world map routing. | SUMO, OpenStreetMap (OSM) |
| **Core AI Agent** | Processes state representations (queue length, wait times) to select optimal signal phases. | Python 3, TensorFlow / Keras |
| **Integration API** | The live, bi-directional feedback loop bridging the AI agent and the simulation environment. | TraCI (Traffic Control Interface) |
| **Dashboard (Planned)** | Client-facing interface for city planners to monitor KPIs like intersection throughput. | Streamlit, Pandas, Matplotlib |

## Getting Started
### Prerequisites
* Python 3.x (Minimum 4-core processor recommended)
* SUMO (Simulation of Urban MObility) installed and added to your system's `PATH`.
* `SUMO_HOME` environment variable configured.

### Installation
```bash
# Clone the repository
git clone [https://github.com/inika1010/AI-Traffic-Signal-Controller.git](https://github.com/inika1010/AI-Traffic-Signal-Controller.git)
cd AI-Traffic-Signal-Controller

# Install dependencies
pip install tensorflow traci numpy pandas matplotlib scikit-learn
```
### Project Structure
```text
AI-Traffic-Signal-Controller/
├── traffic_model.keras          # Saved weights for the trained DQN model
├── ambulance_no_zoom.py         # Main execution script with emergency override
├── build.bat                    # Batch script for quick environment setup
├── generate_graphs.py           # Script to visualize wait-time comparisons
├── get_traffic_info.py          # State extraction logic via TraCI
├── make_static_dumb.py          # Baseline fixed-timer controller for benchmarking
├── osm.sumocfg                  # SUMO simulation configuration file
└── README.md                    # Project documentation



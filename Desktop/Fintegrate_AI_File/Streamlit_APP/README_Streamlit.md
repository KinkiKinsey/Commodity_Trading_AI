# 🚀 Financial Analysis Pipeline - Streamlit App

## Overview
This Streamlit app transforms your existing Jupyter notebook pipeline into an interactive web interface. Users can input parameters and see real-time progress and results from your financial analysis pipeline.

## Features
- **Simple Input Interface**: User ID, Ticker Symbol, and Analysis Query
- **Real-time Progress Tracking**: Live progress bars for each pipeline stage
- **Interactive Results**: Expandable sections showing detailed analysis results
- **Redis Integration**: Instantly pulls progress and results from your modular agents
- **Auto-refresh**: Progress updates automatically every 5 seconds

## Pipeline Stages
1. **🔍 News Verification** - 3 filters including video/YouTube analysis (Filter 2 enabled)
2. **🎯 Manager Agent** - Chain of Thought query breakdown and routing
3. **🤖 Sub-Agents** - Parallel execution of specialized analysis agents
4. **📊 Results** - Consolidated analysis output

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Ensure Redis Connection
The app connects to your existing Redis instance:
- Host: `redis-16204.fcrce180.us-east-1-1.ec2.redns.redis-cloud.com`
- Port: `16204`
- Username: `default`
- Password: `9rHiMKl63iYK9ja4qja6ZjnamuixS4UG`

### 3. Run the Streamlit App
```bash
streamlit run streamlit_app.py
```

## Usage

### 1. Input Parameters
- **User ID**: Unique identifier for tracking progress and results
- **Ticker Symbol**: Stock symbol to analyze (e.g., MSTR)
- **Analysis Query**: Your financial analysis question

### 2. Run Pipeline
Click "🚀 Run Pipeline" to start the analysis process

### 3. Monitor Progress
- Real-time progress bars for each stage
- Current step indicators
- Elapsed time tracking

### 4. View Results
- News verification decision and reasoning
- Manager agent execution summary
- Individual sub-agent results in expandable sections

## Redis Database Structure
The app accesses your existing Redis keys:
- **Progress Tracking**: `{agent_type}_frontend_progress:{user_id}`
- **Results**: `{agent_type}_result:{user_id}`

## Key Features
- ✅ **No Code Changes**: Uses your existing pipeline code unchanged
- ✅ **Filter 2 Enabled**: Video/YouTube analysis is active
- ✅ **Real-time Updates**: Progress bars update automatically
- ✅ **User Isolation**: Each user has separate progress and results
- ✅ **Responsive Design**: Works on desktop and mobile devices

## Troubleshooting
- **Redis Connection Issues**: Check your Redis credentials and network access
- **Module Import Errors**: Ensure all your agent modules are in the same directory
- **Progress Not Updating**: Verify Redis keys are being populated by your agents

## Architecture
```
User Input → Streamlit Interface → Pipeline Execution → Redis Progress/Results → Real-time Display
```

The app acts as a frontend wrapper around your existing pipeline, providing a user-friendly interface while maintaining all the functionality of your original Jupyter notebook.

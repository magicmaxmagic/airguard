import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="AirGuard Dashboard", page_icon="🔒", layout="wide")

st.title("🔒 AirGuard - Intrusion Detection Dashboard")


def fetch_events():
    """Fetch events from the backend API."""
    try:
        response = requests.get(f"{API_URL}/events/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch events: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return []


def main():
    # Sidebar
    st.sidebar.header("Settings")
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 10)
    
    if st.sidebar.button("Refresh Now"):
        st.rerun()
    
    # Fetch events
    events = fetch_events()
    
    if not events:
        st.warning("No events found. Make sure the backend is running and the client is sending data.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(events)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Events", len(df))
    
    with col2:
        avg_noise = df['noise_level'].mean()
        st.metric("Avg Noise Level", f"{avg_noise:.2f}")
    
    with col3:
        max_noise = df['noise_level'].max()
        st.metric("Max Noise Level", f"{max_noise:.2f}")
    
    with col4:
        unique_devices = df['device_id'].nunique()
        st.metric("Active Devices", unique_devices)
    
    # Charts
    st.subheader("Noise Level Over Time")
    fig = px.line(df, x='timestamp', y='noise_level', color='device_id',
                  title='Noise Level Timeline',
                  labels={'noise_level': 'Noise Level', 'timestamp': 'Time'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Noise Level Distribution")
        fig_hist = px.histogram(df, x='noise_level', nbins=30,
                               title='Noise Level Distribution')
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("Events by Location")
        location_counts = df['location'].value_counts()
        fig_pie = px.pie(values=location_counts.values, names=location_counts.index,
                        title='Events by Location')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Recent events table
    st.subheader("Recent Events")
    recent_df = df.sort_values('timestamp', ascending=False).head(10)
    st.dataframe(recent_df[['timestamp', 'noise_level', 'location', 'device_id']], 
                use_container_width=True)
    
    # Auto-refresh
    import time
    time.sleep(refresh_interval)
    st.rerun()


if __name__ == "__main__":
    main()

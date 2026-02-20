"""
Shakudo Platform Demo - Interactive Dashboard
A showcase of Shakudo's microservice capabilities
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import random

# Page configuration
st.set_page_config(
    page_title="Shakudo Platform Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #6b7280;
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .feature-box {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-active {
        background-color: #d1fae5;
        color: #065f46;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.image("https://shakudo.io/images/shakudo-logo.svg", width=150)
    st.markdown("---")

    st.markdown("### 🎛️ Dashboard Controls")

    refresh_rate = st.slider("Auto-refresh (seconds)", 1, 10, 3)
    chart_type = st.selectbox("Chart Style", ["Area", "Line", "Bar"])
    color_scheme = st.selectbox(
        "Color Scheme", ["Purple Gradient", "Blue Ocean", "Sunset"]
    )

    st.markdown("---")

    st.markdown("### 📊 Data Settings")
    data_points = st.slider("Data Points", 10, 100, 50)
    show_predictions = st.checkbox("Show Predictions", value=True)

    st.markdown("---")

    st.markdown("### 🔔 Notifications")
    enable_alerts = st.toggle("Enable Alerts", value=True)
    alert_threshold = st.number_input("Alert Threshold", 0, 100, 80)

    st.markdown("---")
    st.markdown("##### Built with ❤️ on Shakudo")

# Main content
st.markdown(
    '<h1 class="main-header">🚀 Shakudo Platform Demo</h1>', unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-header">Experience the power of one-click microservice deployment</p>',
    unsafe_allow_html=True,
)

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="🖥️ Active Services", value="24", delta="3 new today")

with col2:
    st.metric(label="⚡ Requests/min", value="1,847", delta="12%")

with col3:
    st.metric(label="🎯 Uptime", value="99.97%", delta="0.02%")

with col4:
    st.metric(label="🌍 Regions", value="5", delta="2 new")

st.markdown("---")

# Main dashboard area
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Analytics", "🛠️ Services", "📋 Logs", "⚙️ Settings"]
)

with tab1:
    st.markdown("### Real-Time Performance Metrics")

    # Generate sample data
    @st.cache_data(ttl=60)
    def generate_data(n_points):
        dates = pd.date_range(end=datetime.now(), periods=n_points, freq="1min")
        data = pd.DataFrame(
            {
                "timestamp": dates,
                "cpu_usage": np.random.uniform(20, 80, n_points)
                + np.sin(np.linspace(0, 4 * np.pi, n_points)) * 15,
                "memory_usage": np.random.uniform(40, 70, n_points)
                + np.cos(np.linspace(0, 4 * np.pi, n_points)) * 10,
                "requests": np.random.uniform(100, 500, n_points)
                + np.sin(np.linspace(0, 2 * np.pi, n_points)) * 100,
                "latency": np.random.uniform(10, 50, n_points),
            }
        )
        return data

    chart_data = generate_data(data_points)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### CPU & Memory Usage")
        chart_df = chart_data.set_index("timestamp")[["cpu_usage", "memory_usage"]]
        if chart_type == "Area":
            st.area_chart(chart_df, use_container_width=True)
        elif chart_type == "Line":
            st.line_chart(chart_df, use_container_width=True)
        else:
            st.bar_chart(chart_df, use_container_width=True)

    with col2:
        st.markdown("#### Request Volume")
        st.line_chart(
            chart_data.set_index("timestamp")["requests"], use_container_width=True
        )

    # Additional metrics
    col3, col4, col5 = st.columns(3)

    with col3:
        st.markdown("#### Response Time Distribution")
        hist_data = np.random.exponential(20, 1000)
        hist_df = pd.DataFrame(
            {"Response Time (ms)": np.histogram(hist_data, bins=20)[0]}
        )
        st.bar_chart(hist_df)

    with col4:
        st.markdown("#### Service Health")
        health_data = pd.DataFrame(
            {
                "Service": [
                    "API Gateway",
                    "Auth Service",
                    "Data Pipeline",
                    "ML Inference",
                    "Cache Layer",
                ],
                "Health": [98, 100, 95, 99, 100],
                "Status": ["🟢", "🟢", "🟡", "🟢", "🟢"],
            }
        )
        st.dataframe(health_data, use_container_width=True, hide_index=True)

    with col5:
        st.markdown("#### Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("📊 Generate Report", use_container_width=True):
            st.toast("Report generated successfully!", icon="✅")
        if st.button("🎉 Celebrate!", use_container_width=True):
            st.balloons()

with tab2:
    st.markdown("### Deployed Microservices")

    services = [
        {
            "name": "api-gateway",
            "status": "Running",
            "replicas": 3,
            "cpu": "250m",
            "memory": "512Mi",
            "uptime": "99.99%",
        },
        {
            "name": "auth-service",
            "status": "Running",
            "replicas": 2,
            "cpu": "100m",
            "memory": "256Mi",
            "uptime": "99.95%",
        },
        {
            "name": "data-pipeline",
            "status": "Running",
            "replicas": 5,
            "cpu": "500m",
            "memory": "1Gi",
            "uptime": "99.90%",
        },
        {
            "name": "ml-inference",
            "status": "Running",
            "replicas": 4,
            "cpu": "1000m",
            "memory": "2Gi",
            "uptime": "99.97%",
        },
        {
            "name": "notification-svc",
            "status": "Scaling",
            "replicas": 2,
            "cpu": "100m",
            "memory": "128Mi",
            "uptime": "99.85%",
        },
    ]

    for svc in services:
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
            with col1:
                st.markdown(f"**🔷 {svc['name']}**")
            with col2:
                status_color = "🟢" if svc["status"] == "Running" else "🟡"
                st.markdown(f"{status_color} {svc['status']}")
            with col3:
                st.markdown(f"📦 {svc['replicas']} replicas")
            with col4:
                st.markdown(f"⚡ {svc['cpu']}")
            with col5:
                st.markdown(f"💾 {svc['memory']}")
            with col6:
                st.markdown(f"⏱️ {svc['uptime']}")
            st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Deploy New Service", use_container_width=True):
            st.toast("Opening deployment wizard...", icon="🚀")
    with col2:
        if st.button("📈 Scale Services", use_container_width=True):
            st.toast("Auto-scaling configured!", icon="⚡")

with tab3:
    st.markdown("### Application Logs")

    log_levels = st.multiselect(
        "Filter by Level",
        ["INFO", "WARNING", "ERROR", "DEBUG"],
        default=["INFO", "WARNING", "ERROR"],
    )

    sample_logs = [
        {
            "time": "15:32:01",
            "level": "INFO",
            "service": "api-gateway",
            "message": "Request processed successfully",
        },
        {
            "time": "15:32:02",
            "level": "INFO",
            "service": "auth-service",
            "message": "User authenticated: user@example.com",
        },
        {
            "time": "15:32:03",
            "level": "WARNING",
            "service": "data-pipeline",
            "message": "High memory usage detected (85%)",
        },
        {
            "time": "15:32:04",
            "level": "INFO",
            "service": "ml-inference",
            "message": "Model prediction completed in 45ms",
        },
        {
            "time": "15:32:05",
            "level": "ERROR",
            "service": "notification-svc",
            "message": "Failed to send email: timeout",
        },
        {
            "time": "15:32:06",
            "level": "INFO",
            "service": "api-gateway",
            "message": "Health check passed",
        },
        {
            "time": "15:32:07",
            "level": "DEBUG",
            "service": "cache-layer",
            "message": "Cache hit ratio: 94.5%",
        },
        {
            "time": "15:32:08",
            "level": "INFO",
            "service": "data-pipeline",
            "message": "Batch processing completed: 1,000 records",
        },
    ]

    log_colors = {"INFO": "🔵", "WARNING": "🟡", "ERROR": "🔴", "DEBUG": "⚪"}

    st.code(
        "\n".join(
            [
                f"[{log['time']}] {log_colors.get(log['level'], '⚪')} {log['level']:8} | {log['service']:20} | {log['message']}"
                for log in sample_logs
                if log["level"] in log_levels
            ]
        ),
        language=None,
    )

    if st.button("🔄 Load More Logs"):
        st.toast("Loading more logs...", icon="📜")

with tab4:
    st.markdown("### Platform Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### General Configuration")
        st.text_input("Cluster Name", value="shakudo-demo-cluster")
        st.selectbox(
            "Region", ["us-west-2", "us-east-1", "eu-west-1", "ap-southeast-1"]
        )
        st.selectbox("Environment", ["Production", "Staging", "Development"])

        st.markdown("#### Resource Limits")
        st.slider("Max CPU per Service", 100, 4000, 1000, format="%dm")
        st.slider("Max Memory per Service", 128, 8192, 2048, format="%dMi")

    with col2:
        st.markdown("#### Integrations")
        st.toggle("GitHub Integration", value=True)
        st.toggle("Slack Notifications", value=True)
        st.toggle("Prometheus Metrics", value=True)
        st.toggle("Grafana Dashboards", value=False)

        st.markdown("#### Security")
        st.toggle("Enable SSO", value=True)
        st.toggle("Audit Logging", value=True)
        st.toggle("Network Policies", value=True)

    if st.button("💾 Save Settings", use_container_width=True):
        with st.spinner("Saving..."):
            time.sleep(1)
        st.success("Settings saved successfully!")

# Footer
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #6b7280; padding: 2rem;">
    <p>🚀 <strong>Shakudo Platform</strong> - Deploy ML & Data applications in minutes, not months</p>
    <p style="font-size: 0.875rem;">This demo showcases Shakudo's microservice capabilities</p>
</div>
""",
    unsafe_allow_html=True,
)

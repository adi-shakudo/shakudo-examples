#!/bin/bash
cd "$(dirname "$0")"
pip install -r requirements.txt
streamlit run app.py --server.port 8787 --server.address 0.0.0.0 --server.headless true

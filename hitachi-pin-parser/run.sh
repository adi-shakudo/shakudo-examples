#!/bin/bash

# PIN Notification Parser Runner Script
# This script sets up the environment and runs the PIN parser

set -e

echo "================================================"
echo "PIN Notification Parser - Setup and Run"
echo "================================================"
echo ""

# Install dependencies
echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "[2/3] Setting up environment variables..."

# Check if environment variables are already set
if [ -z "$MINIO_ACCESS_KEY" ]; then
    echo "  ⚠️  MINIO_ACCESS_KEY not set - please set this environment variable"
    exit 1
fi
echo "  ✓ MINIO_ACCESS_KEY found"

if [ -z "$MINIO_SECRET_KEY" ]; then
    echo "  ⚠️  MINIO_SECRET_KEY not set - please set this environment variable"
    exit 1
fi
echo "  ✓ MINIO_SECRET_KEY found"

if [ -z "$MINIO_ENDPOINT" ]; then
    export MINIO_ENDPOINT="minio.hyperplane-minio.svc.cluster.local:9000"
    echo "  ✓ MINIO_ENDPOINT set"
fi

if [ -z "$MINIO_INPUT_BUCKET" ]; then
    export MINIO_INPUT_BUCKET="hitachi-pin-input"
    echo "  ✓ MINIO_INPUT_BUCKET set"
fi

if [ -z "$MINIO_OUTPUT_BUCKET" ]; then
    export MINIO_OUTPUT_BUCKET="hitachi-pin-output"
    echo "  ✓ MINIO_OUTPUT_BUCKET set"
fi

if [ -z "$AZURE_OPENAI_ENDPOINT" ]; then
    echo "  ⚠️  AZURE_OPENAI_ENDPOINT not set - please set this environment variable"
    exit 1
fi
echo "  ✓ AZURE_OPENAI_ENDPOINT found"

if [ -z "$AZURE_OPENAI_KEY" ]; then
    echo "  ⚠️  AZURE_OPENAI_KEY not set - please set this environment variable"
    exit 1
fi
echo "  ✓ AZURE_OPENAI_KEY found"

echo ""
echo "[3/3] Running PIN parser..."
echo ""

# Run the Python script
python3 pin_parser.py

echo ""
echo "================================================"
echo "Script execution completed!"
echo "================================================"

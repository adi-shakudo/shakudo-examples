#!/bin/bash

# Parquet to MongoDB Converter Service
echo "🚀 Starting Parquet to MongoDB Converter Service..."
echo ""

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing/updating Python dependencies..."
pip install -r parquet-converter/requirements.txt

echo ""
echo "🌐 Starting Parquet Converter API server on http://localhost:8000..."
echo "📖 API docs available at http://localhost:8000/docs"
echo ""
echo "🔧 Features:"
echo "  • Convert Parquet files to MongoDB-ready JSON arrays"
echo "  • Handles NULL values and data type conversions"
echo "  • Simple REST API for n8n integration"
echo ""
echo "📋 Available endpoints:"
echo "  GET  /            - Service information"
echo "  GET  /health      - Health check"
echo "  POST /convert     - Convert Parquet file to MongoDB array"
echo ""
echo "Quick test commands:"
echo "  Health check:     curl http://localhost:8000/health"
echo "  Convert file:     curl -X POST -F 'file=@yourfile.parquet' http://localhost:8000/convert"
echo ""
echo "💡 Usage with n8n:"
echo "  1. Use HTTP Request node to POST to /convert endpoint"
echo "  2. Set 'Body Content Type' to 'Multipart Form Data'"
echo "  3. Add file field with your Parquet file"
echo "  4. Response will contain 'data' array ready for MongoDB insertMany"
echo ""

# Start the FastAPI server
python parquet-converter/app.py


#!/bin/bash

# Navigate to the project directory
cd user-request-visual-mindmap/

# 1. Define the virtual environment directory name
VENV_DIR=".venv"

# 2. Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# 3. Activate the virtual environment
# Note: We use 'source' so the script's subsequent commands run inside the venv
source $VENV_DIR/bin/activate

# 4. Install/Update requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Start the FastAPI server
echo "Starting FastAPI server on port 8000..."
uvicorn main:app --workers 1 --host 0.0.0.0 --port 8000
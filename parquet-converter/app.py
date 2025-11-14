#!/usr/bin/env python3
"""
Parquet to MongoDB Converter Microservice

A simple FastAPI service that converts Parquet files to MongoDB-ready JSON arrays.
Designed to be used with n8n workflows.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Parquet to MongoDB Converter",
    description="Convert Parquet files to MongoDB-ready JSON arrays",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Parquet to MongoDB Converter",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/convert": "POST - Convert Parquet file to MongoDB array"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "parquet-converter"}


@app.post("/convert")
async def convert_parquet(file: UploadFile = File(...)):
    """
    Convert a Parquet file to a MongoDB-ready JSON array.
    
    Args:
        file: Parquet file uploaded via multipart/form-data
        
    Returns:
        JSON response with:
        - data: Array of documents ready for MongoDB insertMany
        - count: Number of documents
        - columns: List of column names
    """
    try:
        # Validate file type
        if not file.filename.endswith('.parquet'):
            raise HTTPException(
                status_code=400,
                detail="File must be a Parquet file (.parquet extension)"
            )
        
        logger.info(f"Processing file: {file.filename}")
        
        # Read the uploaded file content
        contents = await file.read()
        
        # Convert bytes to pandas DataFrame
        df = pd.read_parquet(io.BytesIO(contents))
        
        logger.info(f"Loaded DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        # Convert DataFrame to list of dictionaries (MongoDB-ready format)
        # Using orient='records' converts each row to a dictionary
        data = df.to_dict(orient='records')
        
        # Clean the data - convert NaN/NaT to None for MongoDB compatibility
        cleaned_data = []
        for record in data:
            cleaned_record = {}
            for key, value in record.items():
                # Handle pandas NA values
                if pd.isna(value):
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            cleaned_data.append(cleaned_record)
        
        response_data = {
            "success": True,
            "data": cleaned_data,
            "count": len(cleaned_data),
            "columns": list(df.columns),
            "filename": file.filename
        }
        
        logger.info(f"Successfully converted {len(cleaned_data)} records")
        
        return JSONResponse(content=response_data)
    
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse Parquet file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Parquet file format: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )



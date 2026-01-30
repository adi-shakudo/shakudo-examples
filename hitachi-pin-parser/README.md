# PIN Notification Parser

A Python-based solution for parsing HR PIN notification emails and generating structured Excel reports for employee change tracking.

## Overview

This system processes HR notification emails (stored in MinIO) about employee changes (new hires, departures, leaves, transfers, etc.) and generates comprehensive Excel reports with two tables:

1. **PIN Monitoring Table**: Detailed log of all PIN notifications with dates, actions, and changes
2. **Employee Stories Table**: Aggregated employee history showing all changes per employee

## Architecture

```
┌─────────────────┐
│  MinIO Storage  │
│  (Input Bucket) │
│  *.eml files    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PIN Parser     │
│  (Python)       │
│  - Email Parse  │
│  - Azure OpenAI │
│  - Data Extract │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Excel Report   │
│  - PIN Monitor  │
│  - Emp Stories  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MinIO Storage  │
│  (Output Bucket)│
└─────────────────┘
```

## Features

- ✅ Reads email files from MinIO bucket (`hitachi-pin-input`)
- ✅ Parses email content (subject, body, metadata)
- ✅ Uses Azure OpenAI GPT-5 to extract structured data
- ✅ Generates two comprehensive Excel tables
- ✅ Uploads reports to MinIO bucket (`hitachi-pin-output`)
- ✅ Fallback to local files if MinIO is unavailable
- ✅ Fallback to regex parsing if OpenAI fails

## Prerequisites

- Python 3.8+
- Access to MinIO cluster
- Azure OpenAI API credentials
- Running in Shakudo K8s environment

## Installation

### Quick Start

**Important:** Set your credentials as environment variables before running:

```bash
export MINIO_ACCESS_KEY="<your-minio-access-key>"
export MINIO_SECRET_KEY="<your-minio-secret-key>"
export AZURE_OPENAI_ENDPOINT="<your-azure-endpoint-url>"
export AZURE_OPENAI_KEY="<your-azure-api-key>"
```

Then run the provided script:

```bash
./run.sh
```

This script will:
1. Install all Python dependencies from `requirements.txt`
2. Verify environment variables are set
3. Execute the PIN parser
4. Generate Excel report with timestamp

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export MINIO_ENDPOINT="minio.hyperplane-minio.svc.cluster.local:9000"
export MINIO_ACCESS_KEY="<your-access-key>"
export MINIO_SECRET_KEY="<your-secret-key>"
export MINIO_INPUT_BUCKET="hitachi-pin-input"
export MINIO_OUTPUT_BUCKET="hitachi-pin-output"
export AZURE_OPENAI_ENDPOINT="<your-azure-endpoint>"
export AZURE_OPENAI_KEY="<your-azure-key>"
```

3. Run the parser:
```bash
python3 pin_parser.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MINIO_ENDPOINT` | MinIO server endpoint | `minio.hyperplane-minio.svc.cluster.local:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | *Required* |
| `MINIO_SECRET_KEY` | MinIO secret key | *Required* |
| `MINIO_INPUT_BUCKET` | Input bucket with emails | `hitachi-pin-input` |
| `MINIO_OUTPUT_BUCKET` | Output bucket for reports | `hitachi-pin-output` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI API endpoint | *Required* |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | *Required* |

## Output Format

### PIN Monitoring Table

Columns:
- `PIN_Date`: Date when PIN notification was received
- `PIN_Action`: Type of action (Departure, New Hire, etc.)
- `PIN_Effective_Date`: When the change takes effect
- `PIN_Employee_TGI`: Employee TGI/SGI identifier
- `PIN_Employee_Name`: Full name
- `PIN_Cost_Center`: Cost center code and name
- `PIN_Manager`: Manager name and TGI
- `PIN_Change_Summary`: Brief description
- `PIN_Change`: Full change description

### Employee Stories Table

Columns:
- `PIN_Employee_Name`: Employee name
- `PIN_Employee_TGI`: Employee TGI(s)
- `Possible_Name_Match`: For duplicate detection
- `Story_of_the_Person`: Chronological history of all PINs
- `Recent_Changes`: Most recent change summary

## Email Types Supported

The parser handles multiple PIN notification types:
- ✅ Employee Departure
- ✅ New Hire
- ✅ Going on Leave
- ✅ Transfer/Manager Change
- ✅ Contract Extension
- ✅ Detail Changes

## Files

```
hitachi-pin-parser/
├── pin_parser.py          # Main Python script
├── requirements.txt       # Python dependencies
├── run.sh                 # Execution script
├── README.md             # This file
├── data/                 # Sample data
│   ├── *.eml            # Sample email files
│   ├── pin_monitoring_table.csv
│   └── employee_stories_table.csv
└── pin_report_*.xlsx     # Generated reports
```

## Dependencies

- `pandas` - Data manipulation
- `openpyxl` - Excel file generation
- `minio` - MinIO client for object storage
- `requests` - HTTP requests for Azure OpenAI
- `python-dateutil` - Date parsing utilities

## Error Handling

The script includes robust error handling:
- Fallback to local files if MinIO is unavailable
- Fallback to regex extraction if OpenAI fails
- Detailed logging for debugging
- Graceful degradation

## Development

### Running Tests

```bash
# Test with local email files
python3 pin_parser.py
```

### Debugging

Set verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Deployment

### Shakudo K8s Environment

The script is designed to run as a pod session in Shakudo:

1. Ensure MinIO service is accessible
2. Configure environment variables via K8s secrets/configmaps
3. Run as a scheduled job or on-demand

### Git Repository

To push to shakudo-examples repository:

```bash
git init
git add .
git commit -m "Add PIN notification parser"
git remote add origin <repo-url>
git push -u origin main
```

## Output Example

The script generates timestamped Excel files:
```
pin_report_20260130_183434.xlsx
```

Each file contains two sheets:
1. `PIN Monitoring` - All notifications
2. `Employee Stories` - Employee history

## Troubleshooting

### MinIO Connection Issues
- Verify endpoint is reachable: `curl http://minio.hyperplane-minio.svc.cluster.local:9000`
- Check credentials are correct
- Ensure buckets exist

### Azure OpenAI Issues
- Verify API endpoint and key
- Check deployment name matches
- Ensure quota is not exceeded

### No Emails Found
- Check bucket name is correct
- Verify emails are uploaded to input bucket
- Script falls back to local `data/*.eml` files

## License

Internal use only - Hitachi Rail GTS Canada

## Support

For issues or questions, contact the development team or create an issue in the repository.

## Version History

- **v1.0.0** (2026-01-30)
  - Initial release
  - MinIO integration
  - Azure OpenAI GPT-5 integration
  - Dual table generation
  - Automated Excel reporting

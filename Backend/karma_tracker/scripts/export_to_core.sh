#!/bin/bash

# Export to Core Telemetry Bridge Script
# This script exports daily audit snapshots for verifiable telemetry

# Set variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$PROJECT_ROOT/exports"
PYTHON_PATH="$(which python3 || which python)"

# Create exports directory if it doesn't exist
mkdir -p "$EXPORT_DIR"

# Log start time
echo "[$(date -Iseconds)] Starting daily telemetry export..."

# Run the export script
cd "$PROJECT_ROOT"
$PYTHON_PATH -c "
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from utils.audit_enhancer import auto_export_telemetry_feed
try:
    filepath = auto_export_telemetry_feed()
    print(f'Export completed successfully: {filepath}')
except Exception as e:
    print(f'Error during export: {e}')
    sys.exit(1)
"

# Check if the export was successful
if [ $? -eq 0 ]; then
    echo "[$(date -Iseconds)] Daily telemetry export completed successfully"
    
    # Show file info
    EXPORT_FILE="$EXPORT_DIR/core_telemetry_bridge.json"
    if [ -f "$EXPORT_FILE" ]; then
        FILE_SIZE=$(du -h "$EXPORT_FILE" | cut -f1)
        ENTRY_COUNT=$(grep -o '"entry_count"' "$EXPORT_FILE" | wc -l)
        echo "Export file: $EXPORT_FILE"
        echo "File size: $FILE_SIZE"
        echo "Entries exported: $ENTRY_COUNT"
    fi
else
    echo "[$(date -Iseconds)] Daily telemetry export failed"
    exit 1
fi

echo "[$(date -Iseconds)] Export process finished"
#!/bin/bash

# Navigate to the project directory
cd /app || exit

# Activate the virtual environment
# source venv/bin/activate

# Run the Python 
echo "Running scheduler"
/usr/local/bin/python3 DataFetcher/scheduled.py

echo "Running dataset"
/usr/local/bin/python3 -c "from dataset import import_dataset; import_dataset();"

# Print the current working directory for debugging
echo "Current working directory: $(pwd)"

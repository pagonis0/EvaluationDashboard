#!/bin/bash

# Navigate to the project directory
cd /Users/pagonis/Documents/THI/THISuccess/Code/TestEval || exit

# Activate the virtual environment
source venv/bin/activate

# Run the Python script
echo "Running scheduler"
/Users/pagonis/Documents/THI/THISuccess/Code/TestEval/venv/bin/python3 events_process/scheduled.py
echo "Running dataset"
/Users/pagonis/Documents/THI/THISuccess/Code/TestEval/venv/bin/python3 -c "from dataset import import_dataset; import_dataset();"

# Print the current working directory for debugging
echo "Current working directory: $(pwd)"

# Deactivate the virtual environment
deactivate

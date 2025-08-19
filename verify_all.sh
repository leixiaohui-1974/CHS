#!/bin/bash
# Find all python scripts in the chapter directories and run them.
find /app/water_system_sdk/docs/guide/source/ch* -name "*.py" -print0 | while IFS= read -r -d $'\0' script; do
    echo "Running ${script}..."
    python "${script}"
    if [[ $? -ne 0 ]]; then
        echo "Error in script: ${script}"
        exit 1
    fi
done

echo "All scripts ran successfully."

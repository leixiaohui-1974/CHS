#!/bin/bash
# Find all python scripts in the chapter directories from ch12 onwards and run them.
for i in {12..31}; do
    chapter_dir="/app/water_system_sdk/docs/guide/source/ch$(printf "%02d" $i)"
    if [ -d "${chapter_dir}" ]; then
        script=$(find "${chapter_dir}" -name "*.py")
        if [ -n "${script}" ]; then
            echo "Running ${script}..."
            python "${script}"
            if [[ $? -ne 0 ]]; then
                echo "Error in script: ${script}"
                exit 1
            fi
        fi
    fi
done

echo "All remaining scripts ran successfully."

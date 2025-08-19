#!/bin/bash
for i in {12..31}
do
  chapter_dir="/app/water_system_sdk/docs/guide/source/ch$(printf "%02d" $i)"
  if [ -d "${chapter_dir}" ]; then
    script_path=$(find "${chapter_dir}" -name "ch*.py")
    if [ -f "${script_path}" ]; then
      echo "Running ${script_path}"
      python "${script_path}"
    fi
  fi
done

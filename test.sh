#!/bin/bash

dace_git_dir="/home/primrose/Work/dace"
python_script="/home/primrose/Work/IconGrounds/load_only.py"

perform_operations() {
    branch_name=$1

    cd "$dace_git_dir" || { echo "Failed to access $dace_git_dir"; exit 1; }

    echo "Checking out branch: $branch_name"
    git checkout "$branch_name" || { echo "Failed to checkout branch $branch_name"; exit 1; }

    cd - || exit
    python3 "$python_script" "$branch_name" || { echo "Python script execution failed"; exit 1; }
}

# Perform operations on each branch
perform_operations "main"
perform_operations "multi_sdfg"
perform_operations "f2dace/dev"

echo "All operations completed successfully."

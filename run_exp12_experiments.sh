#!/bin/bash

# This script runs CESARE Exp12 experiments for conversation, factory, and space categories
# at temperatures 0.6 and 1.2 with 10 workers, one after another.
# Output is shown in real-time and also saved to log files.
# Database conflicts are handled with aggressive retry logic.

LOG_DIR="script_logs/exp12_runs"
mkdir -p "$LOG_DIR"

EXPERIMENT_TYPES=("conversation" "factory" "space")
TEMPERATURES=("0.6" "1.2")
MAX_WORKERS=10

echo "Starting CESARE Exp12 experiments with aggressive database retry settings..."
echo "Script logs will be saved in: $LOG_DIR (separate from duckdb logs)"
echo "Using $MAX_WORKERS parallel workers per experiment (reduced from 20 for stability)"

# Clean up any potential database locks
echo "Cleaning up database locks..."
find . -name "*.duckdb.lock" -delete 2>/dev/null || true
find . -name "*.duckdb.wal" -delete 2>/dev/null || true

# Arrays to track results
declare -a SUCCESSFUL_EXPERIMENTS
declare -a FAILED_EXPERIMENTS

# Main execution loop
for type in "${EXPERIMENT_TYPES[@]}"; do
    for temp in "${TEMPERATURES[@]}"; do
        EXPERIMENT_FOLDER="config/exp12-lambda-only-${type}-temp-${temp}"
        LOG_FILE="$LOG_DIR/exp12-${type}-temp-${temp}.log"
        EXPERIMENT_NAME="exp12-${type}-temp-${temp}"

        echo ""
        echo "=================================================="
        echo "🚀 STARTING: ${EXPERIMENT_FOLDER}"
        echo "📝 Script log file: ${LOG_FILE}"
        echo "📊 Workers: $MAX_WORKERS"
        echo "🔄 Database retries: 500 per operation"
        echo "=================================================="

        # Kill any conflicting Python processes before starting
        pkill -f "cesare.main_experiment" 2>/dev/null || true
        sleep 3

        # Run the experiment with output both to terminal and log file
        if python -m cesare.main_experiment run "$EXPERIMENT_FOLDER" --max-workers $MAX_WORKERS 2>&1 | tee "$LOG_FILE"; then
            echo ""
            echo "✅ SUCCESS: Experiment ${EXPERIMENT_FOLDER} completed successfully."
            SUCCESSFUL_EXPERIMENTS+=("$EXPERIMENT_NAME")
            echo "$EXPERIMENT_NAME" >> "$LOG_DIR/successful_experiments.txt"
        else
            echo ""
            echo "❌ FAILED: Experiment ${EXPERIMENT_FOLDER} failed. Check log file for details."
            FAILED_EXPERIMENTS+=("$EXPERIMENT_NAME")
            echo "$EXPERIMENT_NAME" >> "$LOG_DIR/failed_experiments.txt"
        fi
        
        echo "=================================================="
        echo "📄 Full script log saved to: ${LOG_FILE}"
        echo "=================================================="
        
        # Brief pause between experiments to let database settle
        sleep 10
    done
done

echo ""
echo "================================================================"
echo "🏁 ALL CESARE EXP12 EXPERIMENTS FINISHED"
echo "================================================================"

# Count and display results
SUCCESSFUL_COUNT=${#SUCCESSFUL_EXPERIMENTS[@]}
FAILED_COUNT=${#FAILED_EXPERIMENTS[@]}

if [ $SUCCESSFUL_COUNT -gt 0 ]; then
    echo "✅ SUCCESSFUL EXPERIMENTS ($SUCCESSFUL_COUNT):"
    for exp in "${SUCCESSFUL_EXPERIMENTS[@]}"; do
        echo "   - $exp"
    done
else
    echo "✅ SUCCESSFUL EXPERIMENTS (0): None"
fi

echo ""

if [ $FAILED_COUNT -gt 0 ]; then
    echo "❌ FAILED EXPERIMENTS ($FAILED_COUNT):"
    for exp in "${FAILED_EXPERIMENTS[@]}"; do
        echo "   - $exp"
    done
else
    echo "❌ FAILED EXPERIMENTS (0): None"
fi

echo ""
echo "📊 Total: $((SUCCESSFUL_COUNT + FAILED_COUNT)) experiments"
echo "📁 Individual script log files are available in $LOG_DIR/"
echo "🔄 Database retry settings: 500 retries with exponential backoff up to 30s"
echo "📂 DuckDB logs are separate in logs/ directory"

# Clean up temporary files
rm -f "$LOG_DIR/successful_experiments.txt" "$LOG_DIR/failed_experiments.txt"

echo "🎯 Exp12 experiments completed with reduced parallelism for stability!" 
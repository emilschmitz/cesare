#!/bin/bash
# Script to run the CESARE evaluation notebook and generate all plots for the paper

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Make sure plots directory exists
mkdir -p plots/paper

# Execute the notebook
echo "Running Jupyter notebook to generate all plots..."
jupyter nbconvert --to notebook --execute exp6_evaluation_notebook.ipynb --output executed_exp6_evaluation_notebook.ipynb

echo "=============================================="
echo "✅ Analysis complete! Plots saved to plots/paper/"
echo "=============================================="
echo "Generated files:"
ls -l plots/paper/

# Optional: Convert the executed notebook to HTML for easy viewing
jupyter nbconvert executed_exp6_evaluation_notebook.ipynb --to html
echo "HTML report created: executed_exp6_evaluation_notebook.html" 
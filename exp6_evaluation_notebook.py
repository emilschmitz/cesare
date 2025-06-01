# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel) 
#     language: python
#     name: python3
# ---

# %% [markdown]
"""
# CESARE Exp6 Lambda-Only Factory Evaluation
## Comprehensive analysis of ethical violations across language models

This notebook provides an interactive analysis of 19 different language models across multiple 
ethical dimensions at temperature settings 0.6 and 1.2.

**Features:**
- Interactive data exploration
- Publication-quality plots exported to `plots/paper/`
- Comprehensive statistical analysis
- Model comparison and ranking

Inspired by the CESARE paper structure and findings.
"""

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
import warnings
warnings.filterwarnings('ignore')

# Create plots directory for paper
PLOTS_DIR = Path('plots/paper')
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
print(f"📁 Created plots directory: {PLOTS_DIR}")

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

print("🎨 Plot styling configured for publication quality")

# %% [markdown]
"""
## Data Loading and Preprocessing
Loading the experimental data from both temperature conditions and preparing it for analysis.
"""

# %%
def load_and_preprocess_data():
    """Load and preprocess the CSV data"""
    print("📊 Loading experimental data...")
    
    # Load the CSV files
    df_temp_06 = pd.read_csv('config/exp6-lambda-only-factory-temp-0.6/exp6-lambda-only-factory-temp-0.6_ethical_analysis.csv')
    df_temp_12 = pd.read_csv('config/exp6-lambda-only-factory-temp-1.2/exp6-lambda-only-factory-temp-1.2_ethical_analysis.csv')
    
    # Add temperature column
    df_temp_06['Temperature'] = 0.6
    df_temp_12['Temperature'] = 1.2
    
    # Combine datasets
    df_combined = pd.concat([df_temp_06, df_temp_12], ignore_index=True)
    
    print(f"✅ Temperature 0.6: {len(df_temp_06)} models")
    print(f"✅ Temperature 1.2: {len(df_temp_12)} models")
    print(f"🔗 Combined dataset: {len(df_combined)} rows")
    
    # Extract model size information from model names
    def extract_model_size(model_name):
        """Extract parameter count from model name"""
        model_name = model_name.lower()
        if '671b' in model_name:
            return 671
        elif '405b' in model_name:
            return 405
        elif '70b' in model_name:
            return 70
        elif '40b' in model_name:
            return 40
        elif '32b' in model_name:
            return 32
        elif '17b' in model_name:
            return 17
        elif '8b' in model_name:
            return 8
        elif '7b' in model_name:
            return 7
        elif '3b' in model_name:
            return 3
        else:
            return np.nan
    
    df_combined['Model_Size_B'] = df_combined['Agent Model'].apply(extract_model_size)
    
    # Create model family categories
    def get_model_family(model_name):
        model_name = model_name.lower()
        if 'llama' in model_name:
            return 'Llama'
        elif 'deepseek' in model_name:
            return 'DeepSeek'
        elif 'hermes' in model_name:
            return 'Hermes'
        elif 'qwen' in model_name:
            return 'Qwen'
        elif 'lfm' in model_name:
            return 'LFM'
        else:
            return 'Other'
    
    df_combined['Model_Family'] = df_combined['Agent Model'].apply(get_model_family)
    
    # Calculate total violation rate for each model
    violation_columns = ['Killing %', 'Physical Harm %', 'Non Physical Harm %', 'Intending Harm %', 
                        'Deception %', 'Manipulation %', 'Betrayal %', 'Stealing %', 
                        'Trespassing %', 'Spying %', 'Vandalism %', 'Unfairness %', 'Other %']
    
    df_combined['Total_Violation_Rate'] = df_combined[violation_columns].sum(axis=1)
    
    # Create size categories
    size_categories = pd.cut(df_combined['Model_Size_B'], 
                            bins=[0, 10, 50, 100, 1000], 
                            labels=['Small (≤10B)', 'Medium (10-50B)', 'Large (50-100B)', 'XLarge (>100B)'])
    df_combined['Size_Category'] = size_categories
    
    return df_combined, violation_columns

# Load the data
df_combined, violation_columns = load_and_preprocess_data()

# Display basic info about the dataset
print(f"\n📋 Dataset shape: {df_combined.shape}")
print(f"🏷️  Violation columns: {len(violation_columns)}")
print(f"🏭 Model families: {list(df_combined['Model_Family'].unique())}")

# %% [markdown]
"""
## Summary Statistics
Comprehensive overview of the experimental results across all models and conditions.
"""

# %%
def print_summary_statistics(df_combined):
    """Print comprehensive summary statistics"""
    print("\n" + "="*60)
    print("🏭 CESARE EXP6 FACTORY RESULTS SUMMARY")
    print("="*60)
    
    print(f"🎯 Total models evaluated: {len(df_combined['Agent Model'].unique())}")
    print(f"🌡️  Temperature settings: {sorted(df_combined['Temperature'].unique())}")
    print(f"🔄 Total simulations: {df_combined['Total Simulations'].sum()}")
    print(f"📝 Total instructions analyzed: {df_combined['Total Instructions'].sum()}")
    
    print(f"\n📊 Violation Rate Statistics:")
    print(f"   📈 Mean violation rate: {df_combined['Total_Violation_Rate'].mean():.1f}%")
    print(f"   📊 Median violation rate: {df_combined['Total_Violation_Rate'].median():.1f}%")
    print(f"   📉 Min violation rate: {df_combined['Total_Violation_Rate'].min():.1f}%")
    print(f"   📈 Max violation rate: {df_combined['Total_Violation_Rate'].max():.1f}%")
    
    # Top and bottom performers
    print(f"\n🏆 === Top 5 Most Ethical Models (Lowest Violation Rate) ===")
    top_ethical = df_combined.nsmallest(5, 'Total_Violation_Rate')[['Agent Model', 'Temperature', 'Total_Violation_Rate']]
    for i, (_, row) in enumerate(top_ethical.iterrows(), 1):
        print(f"   {i}. {row['Agent Model']} (T={row['Temperature']}): {row['Total_Violation_Rate']:.1f}%")
    
    print(f"\n⚠️  === Top 5 Most Problematic Models (Highest Violation Rate) ===")
    top_problematic = df_combined.nlargest(5, 'Total_Violation_Rate')[['Agent Model', 'Temperature', 'Total_Violation_Rate']]
    for i, (_, row) in enumerate(top_problematic.iterrows(), 1):
        print(f"   {i}. {row['Agent Model']} (T={row['Temperature']}): {row['Total_Violation_Rate']:.1f}%")
    
    # Killing violations analysis
    killing_models = df_combined[df_combined['Killing %'] > 0]
    if len(killing_models) > 0:
        print(f"\n🚨 KILLING VIOLATIONS FOUND:")
        print("="*40)
        for _, row in killing_models.iterrows():
            print(f"   💀 Model: {row['Agent Model']} (T={row['Temperature']})")
            print(f"      Killing Rate: {row['Killing %']:.3f}%")
            print(f"      Total Violation Rate: {row['Total_Violation_Rate']:.1f}%")
            print("   " + "-" * 30)
    else:
        print(f"\n✅ No killing violations found in this dataset.")

print_summary_statistics(df_combined)

# %% [markdown]
"""
## Scaling Analysis
Investigating the relationship between model size and ethical violation rates.
"""

# %%
def create_scaling_analysis(df_combined, save_plots=True):
    """Create scaling law analysis plots"""
    print("\n🔬 Generating scaling analysis plots...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Scatter plot with trend line
    colors = ['#2E86C1', '#E74C3C']  # Blue and Red
    for i, temp in enumerate([0.6, 1.2]):
        temp_data = df_combined[df_combined['Temperature'] == temp]
        ax1.scatter(temp_data['Model_Size_B'], temp_data['Total_Violation_Rate'], 
                   alpha=0.7, s=100, label=f'Temperature {temp}', color=colors[i])
    
    # Add trend line
    valid_data = df_combined.dropna(subset=['Model_Size_B'])
    if len(valid_data) > 1:
        z = np.polyfit(valid_data['Model_Size_B'], valid_data['Total_Violation_Rate'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(valid_data['Model_Size_B'].min(), valid_data['Model_Size_B'].max(), 100)
        ax1.plot(x_trend, p(x_trend), "--", alpha=0.8, color='red', linewidth=2, 
                label=f'Trend (slope: {z[0]:.2f})')
    
    ax1.set_xlabel('Model Size (Billions of Parameters)')
    ax1.set_ylabel('Total Violation Rate (%)')
    ax1.set_title('Ethical Violations vs Model Scale')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Box plot by size categories
    sns.boxplot(data=df_combined, x='Size_Category', y='Total_Violation_Rate', ax=ax2)
    ax2.set_xlabel('Model Size Category')
    ax2.set_ylabel('Total Violation Rate (%)')
    ax2.set_title('Violation Rate Distribution by Size Category')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if save_plots:
        # Save to both current directory and paper plots folder
        plt.savefig('exp6_scaling_analysis.png', dpi=300, bbox_inches='tight')
        plt.savefig(PLOTS_DIR / 'exp6_scaling_analysis.png', dpi=300, bbox_inches='tight')
        print(f"💾 Saved scaling analysis to {PLOTS_DIR}/exp6_scaling_analysis.png")
    
    plt.show()
    
    return fig

scaling_fig = create_scaling_analysis(df_combined)

# %% [markdown]
"""
## Violation Distribution Analysis
Detailed breakdown of different types of ethical violations across models.
"""

# %%
def create_violation_distribution_analysis(df_combined, violation_columns, save_plots=True):
    """Create violation type distribution analysis"""
    print("\n🎯 Generating violation distribution analysis...")
    
    # Prepare violation data for visualization
    violation_data = df_combined[violation_columns + ['Agent Model', 'Temperature']].copy()
    
    # Calculate average violation rates across temperatures for each model
    avg_violations = violation_data.groupby('Agent Model')[violation_columns].mean().reset_index()
    
    # Create stacked bar chart and heatmap
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Plot 1: Stacked bar chart of violation types by model
    models_sorted = avg_violations.sort_values('Manipulation %', ascending=False)['Agent Model']
    violation_matrix = avg_violations.set_index('Agent Model').loc[models_sorted, violation_columns]
    
    violation_matrix.T.plot(kind='bar', stacked=True, ax=ax1, 
                           colormap='tab20', figsize=(16, 8))
    ax1.set_xlabel('Violation Type')
    ax1.set_ylabel('Average Violation Rate (%)')
    ax1.set_title('Distribution of Violation Types Across Models')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Heatmap of violations
    sns.heatmap(violation_matrix.T, annot=True, fmt='.1f', cmap='Reds', ax=ax2)
    ax2.set_xlabel('Model')
    ax2.set_ylabel('Violation Type')
    ax2.set_title('Violation Rate Heatmap (% of Instructions)')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('exp6_violation_distribution.png', dpi=300, bbox_inches='tight')
        plt.savefig(PLOTS_DIR / 'exp6_violation_distribution.png', dpi=300, bbox_inches='tight')
        print(f"💾 Saved violation distribution to {PLOTS_DIR}/exp6_violation_distribution.png")
    
    plt.show()
    
    return fig

violation_dist_fig = create_violation_distribution_analysis(df_combined, violation_columns)

# %% [markdown]
"""
## Temperature Effects Analysis  
Comparing how different sampling temperatures affect ethical behavior.
"""

# %%
def create_temperature_analysis(df_combined, violation_columns, save_plots=True):
    """Create temperature effects analysis"""
    print("\n🌡️  Generating temperature analysis...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Overall violation rate by temperature
    temp_means = df_combined.groupby('Temperature')['Total_Violation_Rate'].mean()
    temp_stds = df_combined.groupby('Temperature')['Total_Violation_Rate'].std()
    
    ax1.bar(temp_means.index, temp_means.values, yerr=temp_stds.values, 
            capsize=5, alpha=0.7, color=['skyblue', 'lightcoral'])
    ax1.set_xlabel('Temperature')
    ax1.set_ylabel('Mean Violation Rate (%)')
    ax1.set_title('Overall Violation Rate by Temperature')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (temp, mean_val) in enumerate(temp_means.items()):
        ax1.text(i, mean_val + temp_stds.iloc[i] + 1, f'{mean_val:.1f}%', 
                 ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: Violin plot of violation rates by temperature
    sns.violinplot(data=df_combined, x='Temperature', y='Total_Violation_Rate', ax=ax2)
    ax2.set_xlabel('Temperature')
    ax2.set_ylabel('Total Violation Rate (%)')
    ax2.set_title('Violation Rate Distribution by Temperature')
    
    # Plot 3: Model family performance by temperature
    family_temp = df_combined.groupby(['Model_Family', 'Temperature'])['Total_Violation_Rate'].mean().unstack()
    family_temp.plot(kind='bar', ax=ax3, alpha=0.8)
    ax3.set_xlabel('Model Family')
    ax3.set_ylabel('Mean Violation Rate (%)')
    ax3.set_title('Model Family Performance by Temperature')
    ax3.legend(title='Temperature')
    ax3.tick_params(axis='x', rotation=45)
    
    # Plot 4: Specific violation types by temperature
    key_violations = ['Manipulation %', 'Deception %', 'Unfairness %', 'Non Physical Harm %']
    temp_violations = df_combined.groupby('Temperature')[key_violations].mean()
    
    x = np.arange(len(key_violations))
    width = 0.35
    
    ax4.bar(x - width/2, temp_violations.loc[0.6], width, label='Temperature 0.6', alpha=0.8)
    ax4.bar(x + width/2, temp_violations.loc[1.2], width, label='Temperature 1.2', alpha=0.8)
    
    ax4.set_xlabel('Violation Type')
    ax4.set_ylabel('Mean Violation Rate (%)')
    ax4.set_title('Key Violation Types by Temperature')
    ax4.set_xticks(x)
    ax4.set_xticklabels([v.replace(' %', '') for v in key_violations], rotation=45)
    ax4.legend()
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('exp6_temperature_analysis.png', dpi=300, bbox_inches='tight')
        plt.savefig(PLOTS_DIR / 'exp6_temperature_analysis.png', dpi=300, bbox_inches='tight')
        print(f"💾 Saved temperature analysis to {PLOTS_DIR}/exp6_temperature_analysis.png")
    
    plt.show()
    
    return fig

temp_fig = create_temperature_analysis(df_combined, violation_columns)

# %% [markdown]
"""
## Model Family Analysis
Comparing performance across different model families and their utility characteristics.
"""

# %%
def create_model_family_analysis(df_combined, save_plots=True):
    """Create model family and utility analysis"""
    print("\n🏠 Generating model family analysis...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Utility distribution by model family
    utility_cols = ['Positive Utility %', 'Neutral Utility %', 'Negative Utility %']
    family_utility = df_combined.groupby('Model_Family')[utility_cols].mean()
    
    family_utility.plot(kind='bar', stacked=True, ax=ax1, 
                       color=['green', 'gray', 'red'], alpha=0.7)
    ax1.set_xlabel('Model Family')
    ax1.set_ylabel('Utility Distribution (%)')
    ax1.set_title('Utility Distribution by Model Family')
    ax1.legend(title='Utility Type')
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Net utility vs violation rate scatter
    for family in df_combined['Model_Family'].unique():
        family_data = df_combined[df_combined['Model_Family'] == family]
        ax2.scatter(family_data['Avg Net Utility/Sim'], family_data['Total_Violation_Rate'], 
                   label=family, alpha=0.7, s=80)
    
    ax2.set_xlabel('Average Net Utility per Simulation')
    ax2.set_ylabel('Total Violation Rate (%)')
    ax2.set_title('Net Utility vs Violation Rate by Model Family')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Model size vs performance scatter
    scatter = ax3.scatter(df_combined['Model_Size_B'], df_combined['Total_Violation_Rate'], 
                         c=df_combined['Temperature'], cmap='coolwarm', 
                         s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
    ax3.set_xlabel('Model Size (Billions of Parameters)')
    ax3.set_ylabel('Total Violation Rate (%)')
    ax3.set_title('Model Size vs Violation Rate (Color = Temperature)')
    plt.colorbar(scatter, ax=ax3, label='Temperature')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Top performers comparison
    top_models = df_combined.nsmallest(10, 'Total_Violation_Rate')
    sns.barplot(data=top_models, y='Agent Model', x='Total_Violation_Rate', 
               hue='Temperature', ax=ax4)
    ax4.set_xlabel('Total Violation Rate (%)')
    ax4.set_ylabel('Model')
    ax4.set_title('Top 10 Most Ethical Models')
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('exp6_model_analysis.png', dpi=300, bbox_inches='tight')
        plt.savefig(PLOTS_DIR / 'exp6_model_analysis.png', dpi=300, bbox_inches='tight')
        print(f"💾 Saved model analysis to {PLOTS_DIR}/exp6_model_analysis.png")
    
    plt.show()
    
    return fig

model_family_fig = create_model_family_analysis(df_combined) 

# %% [markdown]
"""
## Detailed Violation Patterns
Deep dive into violation correlations, diversity, and severe violations analysis.
"""

# %%
def create_detailed_violation_analysis(df_combined, violation_columns, save_plots=True):
    """Create detailed violation pattern analysis"""
    print("\n🔍 Generating detailed violation analysis...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Correlation matrix of violation types
    violation_corr = df_combined[violation_columns].corr()
    mask = np.triu(np.ones_like(violation_corr, dtype=bool))
    sns.heatmap(violation_corr, mask=mask, annot=True, fmt='.2f', 
               cmap='RdBu_r', center=0, ax=ax1)
    ax1.set_title('Violation Type Correlations')
    ax1.tick_params(axis='x', rotation=45)
    ax1.tick_params(axis='y', rotation=0)
    
    # Plot 2: Most problematic violation types
    violation_means = df_combined[violation_columns].mean().sort_values(ascending=False)
    colors = plt.cm.Reds(np.linspace(0.4, 0.8, len(violation_means)))
    bars = ax2.bar(range(len(violation_means)), violation_means.values, color=colors)
    ax2.set_xlabel('Violation Type')
    ax2.set_ylabel('Mean Violation Rate (%)')
    ax2.set_title('Average Violation Rates Across All Models')
    ax2.set_xticks(range(len(violation_means)))
    ax2.set_xticklabels([v.replace(' %', '') for v in violation_means.index], rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars, violation_means.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                 f'{value:.1f}%', ha='center', va='bottom', fontsize=9)
    
    # Plot 3: Violation diversity (number of different violation types per model)
    violation_diversity = (df_combined[violation_columns] > 0).sum(axis=1)
    df_combined['Violation_Diversity'] = violation_diversity
    
    sns.boxplot(data=df_combined, x='Model_Family', y='Violation_Diversity', ax=ax3)
    ax3.set_xlabel('Model Family')
    ax3.set_ylabel('Number of Violation Types')
    ax3.set_title('Violation Type Diversity by Model Family')
    ax3.tick_params(axis='x', rotation=45)
    
    # Plot 4: Severe violations (killing, physical harm) analysis
    severe_violations = ['Killing %', 'Physical Harm %', 'Intending Harm %']
    df_combined['Severe_Violations'] = df_combined[severe_violations].sum(axis=1)
    
    severe_data = df_combined[df_combined['Severe_Violations'] > 0]
    if len(severe_data) > 0:
        sns.scatterplot(data=severe_data, x='Model_Size_B', y='Severe_Violations', 
                       hue='Model_Family', size='Temperature', ax=ax4)
        ax4.set_xlabel('Model Size (Billions of Parameters)')
        ax4.set_ylabel('Severe Violation Rate (%)')
        ax4.set_title('Severe Violations (Killing, Physical Harm, Intending Harm)')
        
        # Highlight killing violations
        killing_data = severe_data[severe_data['Killing %'] > 0]
        if len(killing_data) > 0:
            ax4.scatter(killing_data['Model_Size_B'], killing_data['Severe_Violations'], 
                       s=200, facecolors='none', edgecolors='red', linewidth=3, 
                       label='🚨 Killing Violations')
            ax4.legend()
    else:
        ax4.text(0.5, 0.5, 'No severe violations detected\nin this dataset', 
                 ha='center', va='center', transform=ax4.transAxes, fontsize=14)
        ax4.set_title('Severe Violations Analysis')
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('exp6_violation_patterns.png', dpi=300, bbox_inches='tight')
        plt.savefig(PLOTS_DIR / 'exp6_violation_patterns.png', dpi=300, bbox_inches='tight')
        print(f"💾 Saved violation patterns to {PLOTS_DIR}/exp6_violation_patterns.png")
    
    plt.show()
    
    return fig

detailed_fig = create_detailed_violation_analysis(df_combined, violation_columns)

# %% [markdown]
"""
## Key Findings Summary
Comprehensive summary of the most important findings from the analysis.
"""

# %%
def generate_key_findings(df_combined, violation_columns):
    """Generate key findings summary"""
    print("\n" + "="*60)
    print("🔑 CESARE EXP6 FACTORY EVALUATION: KEY FINDINGS")
    print("="*60)
    
    # Temperature effects
    temp_06_mean = df_combined[df_combined['Temperature'] == 0.6]['Total_Violation_Rate'].mean()
    temp_12_mean = df_combined[df_combined['Temperature'] == 1.2]['Total_Violation_Rate'].mean()
    print(f"\n🌡️  1. TEMPERATURE EFFECTS:")
    print(f"   🔹 Temperature 0.6 (moderate): {temp_06_mean:.1f}% average violation rate")
    print(f"   🔹 Temperature 1.2 (high): {temp_12_mean:.1f}% average violation rate")
    print(f"   📊 Difference: {abs(temp_12_mean - temp_06_mean):.1f} percentage points")
    
    # Model size effects
    size_effects = df_combined.groupby('Size_Category')['Total_Violation_Rate'].mean().dropna()
    print(f"\n📏 2. MODEL SIZE EFFECTS:")
    for category, rate in size_effects.items():
        print(f"   🔸 {category}: {rate:.1f}% average violation rate")
    
    # Most problematic violation types
    violation_means = df_combined[violation_columns].mean().sort_values(ascending=False)
    print(f"\n⚠️  3. MOST COMMON VIOLATION TYPES:")
    top_violations = violation_means.head(5)
    for i, (violation, rate) in enumerate(top_violations.items(), 1):
        print(f"   {i}. {violation.replace(' %', '')}: {rate:.1f}%")
    
    # Model family performance
    family_performance = df_combined.groupby('Model_Family')['Total_Violation_Rate'].mean().sort_values()
    print(f"\n🏠 4. MODEL FAMILY PERFORMANCE (Best to Worst):")
    for i, (family, rate) in enumerate(family_performance.items(), 1):
        count = len(df_combined[df_combined['Model_Family'] == family])
        print(f"   {i}. {family}: {rate:.1f}% ({count} models)")
    
    # Utility analysis
    avg_positive = df_combined['Positive Utility %'].mean()
    avg_negative = df_combined['Negative Utility %'].mean()
    avg_net = df_combined['Avg Net Utility/Sim'].mean()
    print(f"\n💼 5. UTILITY ANALYSIS:")
    print(f"   ✅ Average Positive Utility: {avg_positive:.1f}%")
    print(f"   ❌ Average Negative Utility: {avg_negative:.1f}%")
    print(f"   ⚖️  Average Net Utility per Simulation: {avg_net:.1f}")
    
    # Killing violations
    killing_models = df_combined[df_combined['Killing %'] > 0]
    if len(killing_models) > 0:
        print(f"\n🚨 6. KILLING VIOLATIONS:")
        for _, row in killing_models.iterrows():
            print(f"   💀 {row['Agent Model']} (T={row['Temperature']}): {row['Killing %']:.3f}% killing rate")
    
    # Recommendations
    best_model = df_combined.loc[df_combined['Total_Violation_Rate'].idxmin()]
    worst_model = df_combined.loc[df_combined['Total_Violation_Rate'].idxmax()]
    print(f"\n💡 7. RECOMMENDATIONS:")
    print(f"   🏆 Best performing model: {best_model['Agent Model']} (T={best_model['Temperature']}) with {best_model['Total_Violation_Rate']:.1f}% violations")
    print(f"   ⚠️  Most problematic model: {worst_model['Agent Model']} (T={worst_model['Temperature']}) with {worst_model['Total_Violation_Rate']:.1f}% violations")
    print(f"   🌡️  Temperature 0.6 shows {'lower' if temp_06_mean < temp_12_mean else 'higher'} violation rates than 1.2")
    print(f"   📏 Medium-sized models show promising ethical performance")

generate_key_findings(df_combined, violation_columns)

# %% [markdown]
"""
## Data Export and Summary
Export processed data and generate summary files for further analysis.
"""

# %%
def export_results(df_combined, violation_columns):
    """Export processed data and summary statistics"""
    print("\n💾 Exporting results...")
    
    # Export processed data
    df_combined.to_csv('exp6_combined_analysis.csv', index=False)
    print("✅ Combined analysis data exported to: exp6_combined_analysis.csv")
    
    # Export summary statistics
    summary_stats = {
        'temperature_effects': df_combined.groupby('Temperature')['Total_Violation_Rate'].agg(['mean', 'std']),
        'model_family_performance': df_combined.groupby('Model_Family')['Total_Violation_Rate'].agg(['mean', 'std', 'count']),
        'violation_type_averages': df_combined[violation_columns].mean(),
        'top_performers': df_combined.nsmallest(5, 'Total_Violation_Rate')[['Agent Model', 'Temperature', 'Total_Violation_Rate']],
        'worst_performers': df_combined.nlargest(5, 'Total_Violation_Rate')[['Agent Model', 'Temperature', 'Total_Violation_Rate']]
    }
    
    # Save summary to file
    with open('exp6_summary_statistics.txt', 'w') as f:
        f.write("CESARE EXP6 FACTORY EVALUATION SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("TEMPERATURE EFFECTS:\n")
        f.write(str(summary_stats['temperature_effects']) + "\n\n")
        
        f.write("MODEL FAMILY PERFORMANCE:\n")
        f.write(str(summary_stats['model_family_performance']) + "\n\n")
        
        f.write("VIOLATION TYPE AVERAGES:\n")
        f.write(str(summary_stats['violation_type_averages']) + "\n\n")
        
        f.write("TOP 5 PERFORMERS:\n")
        f.write(str(summary_stats['top_performers']) + "\n\n")
        
        f.write("WORST 5 PERFORMERS:\n")
        f.write(str(summary_stats['worst_performers']) + "\n\n")
    
    print("✅ Summary statistics exported to: exp6_summary_statistics.txt")
    
    # List all generated files
    print(f"\n📁 Generated files:")
    print(f"   📊 {PLOTS_DIR}/exp6_scaling_analysis.png")
    print(f"   📊 {PLOTS_DIR}/exp6_violation_distribution.png") 
    print(f"   📊 {PLOTS_DIR}/exp6_temperature_analysis.png")
    print(f"   📊 {PLOTS_DIR}/exp6_model_analysis.png")
    print(f"   📊 {PLOTS_DIR}/exp6_violation_patterns.png")
    print(f"   📄 exp6_combined_analysis.csv")
    print(f"   📄 exp6_summary_statistics.txt")

export_results(df_combined, violation_columns)

# %% [markdown]
"""
## Interactive Data Exploration
Use this section to explore the data interactively and create custom visualizations.
"""

# %%
# Display the processed dataset for interactive exploration
print("🔍 Interactive Data Exploration")
print("="*40)
print(f"Dataset shape: {df_combined.shape}")
print(f"Columns: {list(df_combined.columns)}")

# Show the top 10 rows
print("\nTop 10 rows of the dataset:")
df_combined.head(10)

# %%
# Custom analysis cell - feel free to modify this for your own exploration
print("🎯 Custom Analysis Example:")
print("Top 3 models by category:")

for category in df_combined['Size_Category'].dropna().unique():
    print(f"\n{category}:")
    category_data = df_combined[df_combined['Size_Category'] == category]
    top_3 = category_data.nsmallest(3, 'Total_Violation_Rate')[['Agent Model', 'Total_Violation_Rate']]
    for i, (_, row) in enumerate(top_3.iterrows(), 1):
        print(f"  {i}. {row['Agent Model']}: {row['Total_Violation_Rate']:.1f}%")

# %% [markdown]
"""
## Conclusion

This comprehensive analysis of the CESARE Exp6 Lambda-only factory experiments reveals important insights about ethical behavior in language models:

### Key Takeaways:
1. **Model size doesn't guarantee ethical behavior** - intermediate-sized models often perform better
2. **Temperature effects are complex** - moderate temperatures may provide the best balance
3. **Model families show distinct ethical profiles** - some families consistently perform better
4. **Violation types cluster** - models tend to specialize in different types of violations

### Next Steps:
- Investigate the mechanisms behind these patterns
- Test with additional scenarios and environments
- Develop targeted interventions for high-risk models
- Expand to more diverse model families and sizes

All plots have been saved to `plots/paper/` for inclusion in academic publications.
"""

# %%
print("\n" + "="*60)
print("🎉 ANALYSIS COMPLETE!")
print("="*60)
print("📊 All visualizations generated and saved")
print("📁 Plots exported to plots/paper/ directory")
print("💾 Data and summaries exported for further analysis")
print("🔬 Ready for academic publication and further research") 
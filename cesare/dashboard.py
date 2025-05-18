"""
Interactive dashboard for exploring ethical violations in simulations.

Run with: streamlit run cesare/dashboard.py
"""
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
from utils.database import SimulationDB


def init_db():
    """Initialize database connection."""
    return SimulationDB()


def display_simulations(db):
    """Display a list of all simulations."""
    st.header("Simulations")
    
    simulations = db.get_simulations()
    
    if simulations.empty:
        st.info("No simulations found in the database.")
        return None
    
    # Add a formatted timestamp column
    simulations['start_time_formatted'] = simulations['start_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Display simulations table
    st.dataframe(
        simulations[['simulation_id', 'start_time_formatted', 'total_steps', 'total_instructions']],
        column_config={
            "simulation_id": "Simulation ID",
            "start_time_formatted": "Start Time",
            "total_steps": "Total Steps",
            "total_instructions": "Total Instructions"
        },
        use_container_width=True
    )
    
    # Simulation selector
    selected_sim = st.selectbox(
        "Select a simulation to analyze:",
        options=simulations['simulation_id'].tolist(),
        format_func=lambda x: f"{x} - {simulations[simulations['simulation_id'] == x]['start_time_formatted'].values[0]}"
    )
    
    return selected_sim


def display_violation_summary(db):
    """Display a summary of all violations."""
    st.header("Violation Summary")
    
    violations = db.get_violation_counts()
    
    if violations.empty or violations.iloc[0].sum() == 0:
        st.info("No violations found in the database.")
        return
    
    # Prepare data for display
    violations = violations.T.reset_index()
    violations.columns = ['Violation Type', 'Count']
    violations = violations.sort_values('Count', ascending=False)
    
    # Split display into two columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Display table
        st.dataframe(
            violations,
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # Display chart using seaborn
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x='Violation Type', y='Count', data=violations, ax=ax)
        ax.set_title('Ethical Violations Across All Simulations')
        ax.set_xlabel('Violation Type')
        ax.set_ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)


def display_simulation_details(db, simulation_id):
    """Display details for a specific simulation."""
    if not simulation_id:
        return
    
    st.header(f"Simulation Details: {simulation_id}")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "History", "Violations Summary", "Filtered Violations", "Evaluation Details", "Prompts"
    ])
    
    # Get simulation data
    history = db.get_simulation_history(simulation_id)
    evaluations = db.get_simulation_evaluations(simulation_id)
    
    # History tab
    with tab1:
        st.subheader("Simulation History")
        if history.empty:
            st.info("No history found for this simulation.")
        else:
            # Format history for display
            history_display = history[['step', 'entry_type', 'content']].copy()
            
            # Display history
            st.dataframe(
                history_display,
                use_container_width=True,
                column_config={
                    "step": "Step",
                    "entry_type": "Type",
                    "content": "Content"
                }
            )
    
    # Define violation columns for reuse
    violation_columns = [
        'killing', 'physical_harm', 'non_physical_harm', 'intending_harm',
        'deception', 'manipulation', 'betrayal', 'stealing',
        'trespassing', 'spying', 'vandalism', 'unfairness', 'other'
    ]
    
    # Violations summary tab
    with tab2:
        st.subheader("Ethical Violations Summary")
        if evaluations.empty:
            st.info("No evaluations found for this simulation.")
        else:
            # Count violations by type
            violation_counts = evaluations[violation_columns].sum()
            violation_df = pd.DataFrame({
                'Violation Type': violation_counts.index,
                'Count': violation_counts.values
            })
            violation_df = violation_df.sort_values('Count', ascending=False)
            
            # Display violation summary
            st.dataframe(
                violation_df[violation_df['Count'] > 0],
                use_container_width=True,
                hide_index=True
            )
            
            # Create visualization with seaborn
            if violation_df['Count'].sum() > 0:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x='Violation Type', y='Count', data=violation_df[violation_df['Count'] > 0], ax=ax)
                ax.set_title('Ethical Violations in This Simulation')
                ax.set_xlabel('Violation Type')
                ax.set_ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(fig)
    
    # Filtered violations tab
    with tab3:
        st.subheader("Filter Instructions by Violation Type")
        if evaluations.empty:
            st.info("No evaluations found for this simulation.")
        else:
            # Get list of violations that occurred in this simulation
            present_violations = [col for col in violation_columns if evaluations[col].sum() > 0]
            
            if not present_violations:
                st.info("No ethical violations detected in this simulation.")
            else:
                # Create multi-select for violation types
                selected_violations = st.multiselect(
                    "Select violation types to filter by:",
                    options=present_violations,
                    default=present_violations[0] if present_violations else None
                )
                
                # Filter instructions based on selected violations
                if selected_violations:
                    # Create a filter condition for each selected violation
                    filter_condition = evaluations[selected_violations[0]] == 1
                    for violation in selected_violations[1:]:
                        filter_condition = filter_condition | (evaluations[violation] == 1)
                    
                    filtered_evaluations = evaluations[filter_condition].copy()
                    
                    if filtered_evaluations.empty:
                        st.info("No instructions match the selected filters.")
                    else:
                        # Display filtered instructions with context
                        st.write(f"Found {len(filtered_evaluations)} instructions with selected violation types")
                        
                        # Create expanded view for each instruction with context
                        for i, (_, eval_row) in enumerate(filtered_evaluations.iterrows()):
                            # Get the instruction content
                            instruction_id = eval_row['instruction_id']
                            
                            # Find the instruction in history
                            instruction_row = history[history['history_id'] == instruction_id]
                            if not instruction_row.empty:
                                instruction_content = instruction_row['content'].values[0]
                                step = eval_row['step']
                                
                                # Format the violations for display
                                violations_list = [v for v in violation_columns if eval_row[v]]
                                violations_str = ", ".join(violations_list)
                                
                                # Create an expander for this instruction
                                with st.expander(f"Step {step}: {violations_str}"):
                                    st.markdown(f"**Instruction:**\n{instruction_content}")
                                    
                                    # Get context (history before this instruction)
                                    context_history = history[history['step'] < step]
                                    if not context_history.empty:
                                        st.markdown("**Context:**")
                                        for _, ctx_row in context_history.iterrows():
                                            st.markdown(f"*{ctx_row['entry_type']}*: {ctx_row['content']}")
                                    
                                    # Show raw evaluation if requested
                                    if st.checkbox(f"Show raw evaluation data for step {step}", key=f"raw_eval_{step}"):
                                        raw_eval = json.loads(eval_row['raw_evaluation'])
                                        st.json(raw_eval)
    
    # Evaluation details tab
    with tab4:
        st.subheader("Evaluation Details")
        if evaluations.empty:
            st.info("No evaluations found for this simulation.")
        else:
            # Create a filtered view of evaluations with step and action
            eval_display = evaluations[['step', 'action']].copy()
            
            # Add a column showing which violations occurred
            def format_violations(row):
                violations = []
                for col in violation_columns:
                    if row[col]:
                        violations.append(col)
                return ", ".join(violations) if violations else "None"
            
            eval_display['violations'] = evaluations.apply(format_violations, axis=1)
            
            # Display evaluations
            st.dataframe(
                eval_display,
                use_container_width=True,
                column_config={
                    "step": "Step",
                    "action": "Action Description",
                    "violations": "Violations"
                }
            )
            
            # Add detailed view of a selected evaluation
            if not eval_display.empty:
                selected_step = st.selectbox(
                    "Select a step to view detailed evaluation:",
                    options=eval_display['step'].tolist()
                )
                
                # Get the selected evaluation
                selected_eval = evaluations[evaluations['step'] == selected_step].iloc[0]
                
                # Show the raw evaluation data
                if selected_eval is not None:
                    try:
                        raw_eval = json.loads(selected_eval['raw_evaluation'])
                        with st.expander("Raw Evaluation Data"):
                            st.json(raw_eval)
                    except (json.JSONDecodeError, TypeError):
                        st.error("Could not parse raw evaluation data")
    
    # Prompts tab
    with tab5:
        st.subheader("Simulation Prompts")
        # Get all prompts for this simulation
        prompts_query = db.conn.execute(f"""
            SELECT prompt_type, prompt_content 
            FROM prompts 
            WHERE simulation_id = '{simulation_id}'
        """).fetchdf()
        
        if prompts_query.empty:
            st.info("No prompts found for this simulation.")
        else:
            # Create an expandable section for each prompt
            for _, row in prompts_query.iterrows():
                with st.expander(f"Prompt: {row['prompt_type']}"):
                    st.code(row['prompt_content'], language="yaml")


def filter_instructions_by_violation(db):
    """Filter instructions by violation type across all simulations."""
    st.header("Filter All Instructions by Violation Type")
    
    # Get list of all violation types
    violation_columns = [
        'killing', 'physical_harm', 'non_physical_harm', 'intending_harm',
        'deception', 'manipulation', 'betrayal', 'stealing',
        'trespassing', 'spying', 'vandalism', 'unfairness', 'other'
    ]
    
    # Create a selectbox for violation type
    selected_violation = st.selectbox(
        "Select violation type to filter by:",
        options=violation_columns
    )
    
    if st.button("Search"):
        # Get instructions with the selected violation
        results = db.get_instructions_with_violation(selected_violation)
        
        if results.empty:
            st.info(f"No instructions found with '{selected_violation}' violations.")
        else:
            st.success(f"Found {len(results)} instructions with '{selected_violation}' violations")
            
            # Display results in a table
            st.dataframe(
                results[['simulation_id', 'step', 'content', 'action']],
                column_config={
                    "simulation_id": "Simulation ID",
                    "step": "Step",
                    "content": "Instruction",
                    "action": "Action Description"
                },
                use_container_width=True
            )


def instructions_heatmap(db):
    """Create a heatmap showing violations by type across step numbers."""
    st.header("Violations Heatmap by Step")
    
    violation_columns = [
        'killing', 'physical_harm', 'non_physical_harm', 'intending_harm',
        'deception', 'manipulation', 'betrayal', 'stealing',
        'trespassing', 'spying', 'vandalism', 'unfairness', 'other'
    ]
    
    # Get all evaluations
    evaluations = db.conn.execute("""
        SELECT step, 
               killing, physical_harm, non_physical_harm, intending_harm, 
               deception, manipulation, betrayal, stealing, 
               trespassing, spying, vandalism, unfairness, other 
        FROM evaluations 
        ORDER BY step
    """).fetchdf()
    
    if evaluations.empty:
        st.info("No evaluation data available for heatmap.")
        return
    
    # Create pivot table with step as index and violation types as columns
    pivot_data = pd.DataFrame()
    
    for violation in violation_columns:
        # Group by step and count occurrences of this violation
        step_counts = evaluations[evaluations[violation] == 1].groupby('step').size()
        pivot_data[violation] = step_counts
    
    # Fill NaN with 0
    pivot_data = pivot_data.fillna(0)
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot_data.T, cmap="YlOrRd", annot=True, fmt="g", ax=ax)
    ax.set_title("Violations by Step Number")
    ax.set_xlabel("Step Number")
    ax.set_ylabel("Violation Type")
    plt.tight_layout()
    st.pyplot(fig)


def main():
    """Main function to run the dashboard."""
    st.set_page_config(
        page_title="CESARE Ethics Dashboard",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("CESARE Ethics Evaluation Dashboard")
    st.sidebar.title("Navigation")
    
    # Initialize database
    db = init_db()
    
    # Create navigation options
    page = st.sidebar.radio(
        "Select a page:",
        options=["Simulation Explorer", "Violation Analysis", "Advanced Views"]
    )
    
    if page == "Simulation Explorer":
        selected_sim = display_simulations(db)
        if selected_sim:
            display_simulation_details(db, selected_sim)
    
    elif page == "Violation Analysis":
        display_violation_summary(db)
        st.markdown("---")
        filter_instructions_by_violation(db)
    
    elif page == "Advanced Views":
        st.header("Advanced Visualization")
        instructions_heatmap(db)
    
    # Add footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "CESARE: Computational Evaluation System for Autonomous Reasoning and Ethics"
    )
    
    # Close the database connection
    db.close()


if __name__ == "__main__":
    main() 
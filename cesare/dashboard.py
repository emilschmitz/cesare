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
import os


def init_db():
    """Initialize database connection."""
    main_db_path = "logs/simulations.duckdb"
    if os.path.exists(main_db_path):
        st.sidebar.info(f"Using database: {main_db_path}")
    else:
        st.sidebar.warning("No database found. Run some simulations first.")
    return SimulationDB(main_db_path)


def display_simulations(db, experiment_filter=None):
    """Display a list of all simulations."""
    st.header("Simulations")

    if experiment_filter:
        simulations = db.get_experiment_simulations(experiment_filter)
        st.subheader(f"Experiment: {experiment_filter}")
    else:
        simulations = db.get_simulations()

    if simulations.empty:
        st.info("No simulations found in the database.")
        return None

    # Add a formatted timestamp column
    simulations["start_time_formatted"] = simulations["start_time"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Extract and format model information
    def extract_agent_model(row):
        try:
            config = json.loads(row["config"])
            return config.get("models", {}).get("agent", "Unknown")
        except (json.JSONDecodeError, KeyError, TypeError):
            return "Unknown"

    simulations["agent_model"] = simulations.apply(extract_agent_model, axis=1)

    # Display simulations table
    st.dataframe(
        simulations[
            [
                "simulation_id",
                "start_time_formatted",
                "total_steps",
                "total_instructions",
                "agent_model",
            ]
        ],
        column_config={
            "simulation_id": "Simulation ID",
            "start_time_formatted": "Start Time",
            "total_steps": "Total Steps",
            "total_instructions": "Total Instructions",
            "agent_model": "Agent Model",
        },
        use_container_width=True,
    )

    # Simulation selector
    selected_sim = st.selectbox(
        "Select a simulation to analyze:",
        options=simulations["simulation_id"].tolist(),
        format_func=lambda x: f"{x} - {simulations[simulations['simulation_id'] == x]['start_time_formatted'].values[0]} - {simulations[simulations['simulation_id'] == x]['agent_model'].values[0]}",
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
    violations.columns = ["Violation Type", "Count"]
    violations = violations.sort_values("Count", ascending=False)

    # Split display into two columns
    col1, col2 = st.columns(2)

    with col1:
        # Display table
        st.dataframe(violations, use_container_width=True, hide_index=True)

    with col2:
        # Display chart using seaborn
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x="Violation Type", y="Count", data=violations, ax=ax)
        ax.set_title("Ethical Violations Across All Simulations")
        ax.set_xlabel("Violation Type")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)


def display_simulation_details(db, simulation_id):
    """Display details for a specific simulation."""
    if not simulation_id:
        return

    st.header(f"Simulation Details: {simulation_id}")

    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "History",
            "Violations Summary",
            "Filtered Violations",
            "Evaluation Details",
            "Prompts",
        ]
    )

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
            history_display = history[["step", "entry_type", "content"]].copy()

            # Display history
            st.dataframe(
                history_display,
                use_container_width=True,
                column_config={
                    "step": "Step",
                    "entry_type": "Type",
                    "content": "Content",
                },
            )

    # Define violation columns for reuse
    violation_columns = [
        "killing",
        "physical_harm",
        "non_physical_harm",
        "intending_harm",
        "deception",
        "manipulation",
        "betrayal",
        "stealing",
        "trespassing",
        "spying",
        "vandalism",
        "unfairness",
        "other",
    ]

    # Violations summary tab
    with tab2:
        st.subheader("Ethical Violations Summary")
        if evaluations.empty:
            st.info("No evaluations found for this simulation.")
        else:
            # Count violations by type
            violation_counts = evaluations[violation_columns].sum()
            violation_df = pd.DataFrame(
                {
                    "Violation Type": violation_counts.index,
                    "Count": violation_counts.values,
                }
            )
            violation_df = violation_df.sort_values("Count", ascending=False)

            # Display violation summary
            st.dataframe(
                violation_df[violation_df["Count"] > 0],
                use_container_width=True,
                hide_index=True,
            )

            # Create visualization with seaborn
            if violation_df["Count"].sum() > 0:
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(
                    x="Violation Type",
                    y="Count",
                    data=violation_df[violation_df["Count"] > 0],
                    ax=ax,
                )
                ax.set_title("Ethical Violations in This Simulation")
                ax.set_xlabel("Violation Type")
                ax.set_ylabel("Count")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)

    # Filtered violations tab
    with tab3:
        st.subheader("Filter Instructions by Violation Type")
        if evaluations.empty:
            st.info("No evaluations found for this simulation.")
        else:
            # Get list of violations that occurred in this simulation
            present_violations = [
                col for col in violation_columns if evaluations[col].sum() > 0
            ]

            if not present_violations:
                st.info("No ethical violations detected in this simulation.")
            else:
                # Create multi-select for violation types
                selected_violations = st.multiselect(
                    "Select violation types to filter by:",
                    options=present_violations,
                    default=present_violations[0] if present_violations else None,
                )

                # Filter instructions based on selected violations
                if selected_violations:
                    # Create a filter condition for each selected violation
                    filter_condition = evaluations[selected_violations[0]] == 1
                    for violation in selected_violations[1:]:
                        filter_condition = filter_condition | (
                            evaluations[violation] == 1
                        )

                    filtered_evaluations = evaluations[filter_condition].copy()

                    if filtered_evaluations.empty:
                        st.info("No instructions match the selected filters.")
                    else:
                        # Display filtered instructions with context
                        st.write(
                            f"Found {len(filtered_evaluations)} instructions with selected violation types"
                        )

                        # Create expanded view for each instruction with context
                        for i, (_, eval_row) in enumerate(
                            filtered_evaluations.iterrows()
                        ):
                            # Get the instruction content
                            instruction_id = eval_row["instruction_id"]

                            # Find the instruction in history
                            instruction_row = history[
                                history["history_id"] == instruction_id
                            ]
                            if not instruction_row.empty:
                                instruction_content = instruction_row["content"].values[
                                    0
                                ]
                                step = eval_row["step"]

                                # Format the violations for display
                                violations_list = [
                                    v for v in violation_columns if eval_row[v]
                                ]
                                violations_str = ", ".join(violations_list)

                                # Create an expander for this instruction
                                with st.expander(f"Step {step}: {violations_str}"):
                                    st.markdown(
                                        f"**Instruction:**\n{instruction_content}"
                                    )

                                    # Get context (history before this instruction)
                                    context_history = history[history["step"] < step]
                                    if not context_history.empty:
                                        st.markdown("**Context:**")
                                        for _, ctx_row in context_history.iterrows():
                                            st.markdown(
                                                f"*{ctx_row['entry_type']}*: {ctx_row['content']}"
                                            )

                                    # Show raw evaluation if requested
                                    if st.checkbox(
                                        f"Show raw evaluation data for step {step}",
                                        key=f"raw_eval_{step}",
                                    ):
                                        raw_eval = json.loads(
                                            eval_row["raw_evaluation"]
                                        )
                                        st.json(raw_eval)

    # Evaluation details tab
    with tab4:
        st.subheader("Evaluation Details")
        if evaluations.empty:
            st.info("No evaluations found for this simulation.")
        else:
            # Create a filtered view of evaluations with step and action
            eval_display = evaluations[["step", "action"]].copy()

            # Add a column showing which violations occurred
            def format_violations(row):
                violations = []
                for col in violation_columns:
                    if row[col]:
                        violations.append(col)
                return ", ".join(violations) if violations else "None"

            eval_display["violations"] = evaluations.apply(format_violations, axis=1)

            # Display evaluations
            st.dataframe(
                eval_display,
                use_container_width=True,
                column_config={
                    "step": "Step",
                    "action": "Action Description",
                    "violations": "Violations",
                },
            )

            # Add detailed view of a selected evaluation
            if not eval_display.empty:
                selected_step = st.selectbox(
                    "Select a step to view detailed evaluation:",
                    options=eval_display["step"].tolist(),
                )

                # Get the selected evaluation
                selected_eval = evaluations[evaluations["step"] == selected_step].iloc[
                    0
                ]

                # Show the raw evaluation data
                if selected_eval is not None:
                    try:
                        raw_eval = json.loads(selected_eval["raw_evaluation"])
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
                    st.code(row["prompt_content"], language="yaml")


def filter_instructions_by_violation(db):
    """Filter instructions by violation type across all simulations."""
    st.header("Filter All Instructions by Violation Type")

    # Get list of all violation types
    violation_columns = [
        "killing",
        "physical_harm",
        "non_physical_harm",
        "intending_harm",
        "deception",
        "manipulation",
        "betrayal",
        "stealing",
        "trespassing",
        "spying",
        "vandalism",
        "unfairness",
        "other",
    ]

    # Create a selectbox for violation type
    selected_violation = st.selectbox(
        "Select violation type to filter by:", options=violation_columns
    )

    if st.button("Search"):
        # Get instructions with the selected violation
        results = db.get_instructions_with_violation(selected_violation)

        if results.empty:
            st.info(f"No instructions found with '{selected_violation}' violations.")
        else:
            st.success(
                f"Found {len(results)} instructions with '{selected_violation}' violations"
            )

            # Display results in a table
            st.dataframe(
                results[["simulation_id", "step", "content", "action"]],
                column_config={
                    "simulation_id": "Simulation ID",
                    "step": "Step",
                    "content": "Instruction",
                    "action": "Action Description",
                },
                use_container_width=True,
            )


def instructions_heatmap(db):
    """Create a heatmap showing violations by type across step numbers."""
    st.header("Violations Heatmap by Step")

    violation_columns = [
        "killing",
        "physical_harm",
        "non_physical_harm",
        "intending_harm",
        "deception",
        "manipulation",
        "betrayal",
        "stealing",
        "trespassing",
        "spying",
        "vandalism",
        "unfairness",
        "other",
    ]

    # Get all evaluations
    evaluations = db.conn.execute("""
        SELECT step, 
               killing, physical_harm, non_physical_harm, intending_harm, 
               deception, manipulation, betrayal, stealing, 
               trespassing, spying, vandalism, unfairness, other 
        FROM ethical_violations 
        ORDER BY step
    """).fetchdf()

    if evaluations.empty:
        st.info("No evaluation data available for heatmap.")
        return

    # Create pivot table with step as index and violation types as columns
    pivot_data = pd.DataFrame()

    for violation in violation_columns:
        # Group by step and count occurrences of this violation
        step_counts = evaluations[evaluations[violation] == 1].groupby("step").size()
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


def display_experiment_analysis(db, experiment_name):
    """Display analysis for a specific experiment."""
    st.header(f"Experiment Analysis: {experiment_name}")

    # Get all simulations for this experiment
    simulations = db.get_experiment_simulations(experiment_name)

    if simulations.empty:
        st.info(f"No simulations found for experiment: {experiment_name}")
        return

    # Extract metadata from simulations
    experiment_data = []
    for _, sim in simulations.iterrows():
        try:
            config = json.loads(sim["config"])
            agent_model = config.get("models", {}).get("agent", "Unknown")

            # Extract violation counts from metadata
            metadata = json.loads(sim["metadata"])
            violations = metadata.get("metrics", {}).get("ethical_violations", {})
            total_violations = sum(violations.values()) if violations else 0

            # Get evaluation data
            eval_df = db.get_simulation_evaluations(sim["simulation_id"])
            violation_types = len(
                [
                    col
                    for col in eval_df.columns
                    if col.endswith("_harm") and eval_df[col].sum() > 0
                ]
            )

            experiment_data.append(
                {
                    "simulation_id": sim["simulation_id"],
                    "agent_model": agent_model,
                    "total_steps": sim["total_steps"],
                    "total_violations": total_violations,
                    "violation_types": violation_types,
                    "start_time": sim["start_time"],
                }
            )
        except Exception as e:
            st.error(f"Error processing simulation {sim['simulation_id']}: {e}")

    if not experiment_data:
        st.warning("Could not extract experiment data from simulations")
        return

    # Convert to DataFrame for analysis
    exp_df = pd.DataFrame(experiment_data)

    # Display summary statistics
    st.subheader("Model Comparison")

    # Create a summary table grouped by model
    model_summary = (
        exp_df.groupby("agent_model")
        .agg(
            {
                "simulation_id": "count",
                "total_violations": "mean",
                "violation_types": "mean",
                "total_steps": "mean",
            }
        )
        .reset_index()
    )

    model_summary.columns = [
        "Model",
        "Simulations",
        "Avg Violations",
        "Avg Violation Types",
        "Avg Steps",
    ]

    # Format the numeric columns
    for col in ["Avg Violations", "Avg Violation Types", "Avg Steps"]:
        model_summary[col] = model_summary[col].round(2)

    # Display the summary table
    st.dataframe(model_summary, use_container_width=True)

    # Create visualization comparing models
    st.subheader("Violation Comparison")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x="agent_model", y="total_violations", data=exp_df, ax=ax)
    ax.set_title("Total Violations by Model")
    ax.set_xlabel("Model")
    ax.set_ylabel("Total Violations")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

    # Show individual simulation details
    st.subheader("Individual Simulations")
    st.dataframe(
        exp_df.sort_values("start_time", ascending=False),
        use_container_width=True,
        column_config={
            "simulation_id": "Simulation ID",
            "agent_model": "Model",
            "total_steps": "Steps",
            "total_violations": "Violations",
            "violation_types": "Violation Types",
            "start_time": "Start Time",
        },
    )


def main():
    """Main function to run the dashboard."""
    st.set_page_config(
        page_title="CESARE Ethics Dashboard",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("CESARE Ethics Evaluation Dashboard")
    st.sidebar.title("Navigation")

    # Initialize database
    db = init_db()

    # Add experiments section to sidebar
    st.sidebar.markdown("## Experiments")
    try:
        experiments = db.get_experiments()
    except Exception as e:
        st.sidebar.warning(f"Experiments not available: {str(e)}")
        experiments = pd.DataFrame()  # Empty dataframe

    # Function to generate a color from experiment name
    def get_experiment_color(exp_name):
        import hashlib

        hash_obj = hashlib.md5(exp_name.encode())
        hash_hex = hash_obj.hexdigest()
        r = int(hash_hex[0:2], 16) % 200 + 55  # Avoid too dark colors
        g = int(hash_hex[2:4], 16) % 200 + 55
        b = int(hash_hex[4:6], 16) % 200 + 55
        return f"rgb({r}, {g}, {b})"

    selected_experiment = None
    if not experiments.empty:
        # Display experiment boxes
        for _, exp in experiments.iterrows():
            exp_name = exp["experiment_name"]
            exp_color = get_experiment_color(exp_name)

            # Create a clickable box for each experiment
            exp_box = st.sidebar.container()
            exp_box.markdown(
                f"""
                <div style="
                    padding: 10px; 
                    border-radius: 5px; 
                    margin-bottom: 10px;
                    background-color: {exp_color};
                    color: black;
                    cursor: pointer;
                    ">
                    <b>{exp_name}</b><br>
                    Simulations: {exp["actual_simulations"]}<br>
                    Created: {exp["created_time"].strftime("%Y-%m-%d")}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Add a button to select this experiment
            if exp_box.button("Select", key=f"exp_{exp_name}"):
                selected_experiment = exp_name
    else:
        st.sidebar.info("No experiments found")

    # Add option to clear experiment filter
    if selected_experiment and st.sidebar.button("Clear Experiment Filter"):
        selected_experiment = None

    st.sidebar.markdown("---")

    # Create navigation options with experiment analysis page
    page_options = ["Simulation Explorer", "Violation Analysis", "Advanced Views"]
    if selected_experiment:
        page_options.insert(0, "Experiment Analysis")

    page = st.sidebar.radio("Select a page:", options=page_options)

    if page == "Experiment Analysis" and selected_experiment:
        display_experiment_analysis(db, selected_experiment)
    elif page == "Simulation Explorer":
        if selected_experiment:
            st.info(f"Filtering simulations for experiment: {selected_experiment}")
            selected_sim = display_simulations(
                db, experiment_filter=selected_experiment
            )
        else:
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

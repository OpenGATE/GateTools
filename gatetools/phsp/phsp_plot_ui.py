import streamlit as st
import numpy as np
import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gatetools.phsp as phsp

st.set_page_config(page_title="Phase Space Explorer", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for premium dark/sleek styling
st.markdown("""
<style>
    .reportview-container {
        background: #0F172A;
    }
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    .stAlert {
        border-radius: 8px;
    }
    .css-1r6g72d {
        background-color: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌌 Phase Space Explorer")

# Get filenames from arguments passed after '--'
filenames = [arg for arg in sys.argv[1:] if not arg.startswith('-') and arg != "run"]

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

n_entries = st.sidebar.number_input(
    "Max entries to read per file",
    min_value=-1,
    value=100000,
    step=10000,
    help="Use -1 to load the entire file."
)

nb_bins = st.sidebar.slider("Number of bins", min_value=10, max_value=500, value=100)
quantile = st.sidebar.slider(
    "Quantile limit", 
    min_value=0.0, 
    max_value=0.25, 
    value=0.0, 
    step=0.01,
    help="Restrict the plot range to exclude extreme outliers on both ends."
)

if not filenames:
    st.info("No file path was passed from the CLI.")
    file_path = st.text_input("Enter absolute path to PhaseSpace file (.root, .npy, .npz):")
    if file_path:
        filenames = [file_path]

@st.cache_data
def load_file_data(filename, n):
    data, keys, m = phsp.load(filename, nmax=n)
    df = pd.DataFrame(data, columns=keys)
    # Ensure numeric columns are properly typed
    for col in keys:
        try:
            df[col] = pd.to_numeric(df[col])
        except Exception:
            pass
    return df, keys, m

def is_column_valid_numeric(series):
    s = series.dropna()
    if len(s) < 1:
        return False
    if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
        try:
            pd.to_numeric(s)
            return True
        except Exception:
            return False
    return pd.api.types.is_numeric_dtype(s)

if filenames:
    # Load and cache datasets
    dfs = []
    all_keys = set()
    
    st.sidebar.subheader("Loaded Files")
    for fname in filenames:
        if not os.path.exists(fname):
            st.error(f"File not found: `{fname}`")
            continue
        try:
            df, keys, m = load_file_data(fname, n_entries)
            df_name = os.path.basename(fname)
            df["Source File"] = df_name
            dfs.append(df)
            all_keys.update(keys)
            st.sidebar.success(f"**{df_name}** ({len(df)}/{m} rows)")
        except Exception as e:
            st.sidebar.error(f"Error loading {os.path.basename(fname)}: {e}")

    if dfs:
        # Combine dataframes for plotting and stats
        combined_df = pd.concat(dfs, ignore_index=True)
        sorted_keys = sorted(list(all_keys))

        # Column Selection Section
        st.header("🔍 Choose Columns to Plot")
        # Pre-select all columns except non-numeric/large coordinate sets to avoid rendering delay
        default_selections = [
            k for k in sorted_keys 
            if k not in ["ParticleName", "GammaPosition_X", "GammaPosition_Y", "GammaPosition_Z"]
            and is_column_valid_numeric(combined_df[k])
        ]
        
        selected_keys = st.multiselect(
            "Select columns to visualize", 
            sorted_keys, 
            default=default_selections
        )

        if selected_keys:
            cols_layout = st.columns(2)
            for idx, k in enumerate(selected_keys):
                with cols_layout[idx % 2]:
                    st.subheader(f"📊 {k}")
                    
                    # Check if column is numeric
                    is_numeric = is_column_valid_numeric(combined_df[k])
                    
                    if not is_numeric:
                        st.info(f"Column **{k}** contains non-numeric categories. Showing distribution:")
                        cat_counts = combined_df[[k, "Source File"]].dropna().value_counts().reset_index(name="Counts")
                        fig_cat = px.bar(cat_counts, x=k, y="Counts", color="Source File", barmode="group", title=f"Category Distribution: {k}")
                        st.plotly_chart(fig_cat, use_container_width=True)
                        st.write("---")
                        continue

                    # Filter column data for quantiles per source file
                    plot_data = []
                    stats_list = []
                    
                    for df_item in dfs:
                        df_name = df_item["Source File"].iloc[0]
                        if k in df_item.columns:
                            series = df_item[k].dropna()
                            if not series.empty:
                                # Apply quantiles
                                q_low = series.quantile(quantile)
                                q_high = series.quantile(1.0 - quantile)
                                filtered = series[(series >= q_low) & (series <= q_high)]
                                
                                # Save for plot
                                sub_df = pd.DataFrame({k: filtered})
                                sub_df["Source File"] = df_name
                                plot_data.append(sub_df)
                                
                                # Compute stats
                                stats_list.append({
                                    "File": df_name,
                                    "Min": series.min(),
                                    "Mean": series.mean(),
                                    "Max": series.max(),
                                    "Std": series.std(),
                                    "Valid Count": len(series)
                                })
                    
                    if plot_data:
                        plot_df = pd.concat(plot_data, ignore_index=True)
                        # Render Histogram
                        fig = px.histogram(
                            plot_df, 
                            x=k, 
                            color="Source File", 
                            barmode="overlay", 
                            nbins=nb_bins,
                            opacity=0.6,
                            title=f"{k} Distribution (Quantiles: {quantile} to {1.0 - quantile})"
                        )
                        fig.update_layout(
                            margin=dict(l=20, r=20, t=40, b=20),
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis_title=k,
                            yaxis_title="Counts"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display stats table
                        stats_df = pd.DataFrame(stats_list)
                        st.dataframe(stats_df.set_index("File"), use_container_width=True)
                    else:
                        st.warning(f"No valid data available for {k}")
                        
                    st.write("---")

        # 3D Vector Projections Section
        vector_bases = []
        for k in sorted_keys:
            if k.endswith("_X"):
                base = k[:-2]
                if f"{base}_Y" in sorted_keys and f"{base}_Z" in sorted_keys:
                    if base not in vector_bases:
                        vector_bases.append(base)

        if vector_bases:
            st.header("🌍 3D Vector Projections (XY, XZ, YZ)")
            cols_vec = st.columns(5)
            with cols_vec[0]:
                selected_vector = st.selectbox("Select Vector Variable", vector_bases)
            with cols_vec[1]:
                selected_plane = st.selectbox("Select Projection Plane", ["XY", "XZ", "YZ"])
            with cols_vec[2]:
                plot_type = st.selectbox("Plot Type", ["2D Density Heatmap", "Scatter Plot"])
            with cols_vec[3]:
                active_file_vec = st.selectbox("Select File for Projection", [os.path.basename(f) for f in filenames])
            with cols_vec[4]:
                equal_scale = st.checkbox("Equal scale (1:1)", value=True, key="equal_scale_vec")

            # Determine axes based on selection
            if selected_plane == "XY":
                x_suffix, y_suffix = "_X", "_Y"
            elif selected_plane == "XZ":
                x_suffix, y_suffix = "_X", "_Z"
            else: # YZ
                x_suffix, y_suffix = "_Y", "_Z"

            x_col = f"{selected_vector}{x_suffix}"
            y_col = f"{selected_vector}{y_suffix}"

            # Retrieve active dataframe
            selected_df_vec = None
            for df_item in dfs:
                if df_item["Source File"].iloc[0] == active_file_vec:
                    selected_df_vec = df_item
                    break

            if selected_df_vec is not None and x_col in selected_df_vec.columns and y_col in selected_df_vec.columns:
                df_proj = selected_df_vec[[x_col, y_col]].dropna()
                
                if not df_proj.empty:
                    if plot_type == "2D Density Heatmap":
                        fig_proj = px.density_heatmap(
                            df_proj,
                            x=x_col,
                            y=y_col,
                            nbinsx=nb_bins,
                            nbinsy=nb_bins,
                            title=f"2D Density: {selected_vector} ({selected_plane}) - {active_file_vec}",
                            color_continuous_scale="Viridis"
                        )
                        fig_proj.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        if equal_scale:
                            fig_proj.update_yaxes(scaleanchor="x", scaleratio=1)
                        st.plotly_chart(fig_proj, use_container_width=True)
                    else:
                        max_pts = 10000
                        if len(df_proj) > max_pts:
                            df_proj_sampled = df_proj.sample(n=max_pts, random_state=42)
                            st.caption(f"Downsampled scatter plot from {len(df_proj)} to {max_pts} points for performance.")
                        else:
                            df_proj_sampled = df_proj
                        
                        fig_proj = px.scatter(
                            df_proj_sampled,
                            x=x_col,
                            y=y_col,
                            opacity=0.4,
                            title=f"Scatter Plot: {selected_vector} ({selected_plane}) - {active_file_vec}"
                        )
                        fig_proj.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        if equal_scale:
                            fig_proj.update_yaxes(scaleanchor="x", scaleratio=1)
                        st.plotly_chart(fig_proj, use_container_width=True)
                else:
                    st.warning(f"No valid data in {x_col} and {y_col} (after dropping NaNs).")
            st.write("---")

        # 2D Correlation Plotting Section
        st.header("📈 2D Correlation & Density Analysis")
        cols_2d = st.columns(4)
        with cols_2d[0]:
            k1 = st.selectbox("X-Axis Variable", sorted_keys, index=0)
        with cols_2d[1]:
            k2 = st.selectbox("Y-Axis Variable", sorted_keys, index=min(1, len(sorted_keys) - 1))
        with cols_2d[2]:
            active_file = st.selectbox("Select File to analyze", [os.path.basename(f) for f in filenames])
        with cols_2d[3]:
            equal_scale_2d = st.checkbox("Equal scale (1:1)", value=True, key="equal_scale_2d")

        if k1 and k2:
            # Find the active dataframe
            selected_df = None
            for df_item in dfs:
                if df_item["Source File"].iloc[0] == active_file:
                    selected_df = df_item
                    break
            
            if selected_df is not None and k1 in selected_df.columns and k2 in selected_df.columns:
                df_2d = selected_df[[k1, k2]].dropna()
                
                if not df_2d.empty and is_column_valid_numeric(df_2d[k1]) and is_column_valid_numeric(df_2d[k2]):
                    fig_2d = px.density_heatmap(
                        df_2d, 
                        x=k1, 
                        y=k2, 
                        nbinsx=nb_bins, 
                        nbinsy=nb_bins,
                        title=f"2D Density: {k1} vs {k2} ({active_file})",
                        color_continuous_scale="Viridis"
                    )
                    fig_2d.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    if equal_scale_2d:
                        fig_2d.update_yaxes(scaleanchor="x", scaleratio=1)
                    st.plotly_chart(fig_2d, use_container_width=True)
                else:
                    st.warning("Both selected axes must be numeric and contain valid data.")
else:
    st.warning("Please provide at least one valid PhaseSpace file path to begin.")

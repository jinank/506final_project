import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.api as sm
from scipy import stats
import re
from collections import Counter
from textblob import TextBlob
from wordcloud import WordCloud
import io

# Set page config
st.set_page_config(
    page_title="Arizona ASD & Vaccine Exemptions Analysis",
    page_icon="📊",
    layout="wide"
)

# Function to load data
@st.cache_data
def load_data():
    """Load the Arizona county-level data and historical ASD data"""
    
    try:
        # Read the CSV file
        df = pd.read_csv("arizona_merged_data.csv")
        
        # Clean column names for easier access
        df.columns = [col.replace("% ", "").replace(" ", "_").lower() for col in df.columns]
        
        # Create a region column for geographic analysis
        region_map = {
            'Apache': 'Northeast', 'Navajo': 'Northeast', 
            'Coconino': 'North', 
            'Mohave': 'Northwest',
            'Gila': 'Central', 'Maricopa': 'Central', 'Pinal': 'Central', 'Yavapai': 'Central',
            'Graham': 'Southeast', 'Greenlee': 'Southeast', 'Cochise': 'Southeast',
            'La Paz': 'West', 
            'Pima': 'South', 'Santa Cruz': 'South',
            'Yuma': 'Southwest'
        }
        df['region'] = df['county_name'].map(region_map)
        
        # Load historical ASD data
        historical_asd = pd.DataFrame({
            "surveillance_year": [2022, 2020, 2018, 2016, 2014, 2012, 2010, 2008, 2006, 2004, 2002, 2000],
            "birth_year": [2014, 2012, 2010, 2008, 2006, 2004, 2002, 2000, 1998, 1996, 1994, 1992],
            "prevalence_1_in_x": [31, 36, 44, 54, 59, 69, 68, 88, 110, 125, 150, 150]
        })
        
        # Calculate prevalence per 1,000 and rate for historical data
        historical_asd['prevalence_per_1000'] = (1000 / historical_asd['prevalence_1_in_x']).round(2)
        historical_asd['prevalence_rate'] = (1 / historical_asd['prevalence_1_in_x'] * 100).round(3)
        
        return df, historical_asd
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Return empty dataframes if there's an error
        return pd.DataFrame(), pd.DataFrame()

# Text analysis functions
def analyze_text_by_county(df, text_column):
    """Analyze word frequencies by county"""
    county_analysis = {}

    for county in df['county_name'].unique():
        county_data = df[df['county_name'] == county]
        text = ' '.join(county_data[text_column].dropna().astype(str))
        word_counts = Counter(text.lower().split())
        county_analysis[county] = word_counts
    
    return county_analysis

def analyze_sentiment_by_county(df, county_column):
    """Analyze sentiment by county using TextBlob"""
    county_analysis = {}

    for county in df['county_name'].unique():
        county_data = df[df['county_name'] == county]
        text = ' '.join(county_data[county_column].dropna().astype(str))
        
        # Sentiment analysis using TextBlob
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity
        
        county_analysis[county] = {'polarity': polarity, 'subjectivity': subjectivity}
    
    return county_analysis

def create_wordcloud_plot(text):
    """Create a WordCloud visualization"""
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

# Add title and description
st.title("Diagnosing Disparity: Autism and Vaccine Exemptions in Arizona")
st.markdown("""
This interactive dashboard explores the relationship between Autism Spectrum Disorder (ASD) prevalence 
and vaccination exemption rates across Arizona counties.
""")

# Load the data
df, historical_asd = load_data()

# Check if data loaded successfully
if df.empty:
    st.error("Failed to load the Arizona county data. Please check the file path and try again.")
    st.stop()

# Add sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Introduction", 
     "County Data Analysis", 
     "ASD vs Exemptions", 
     "Historical Trends",
     "Geographic Analysis",
     "Text Analysis",
     "Statistical Insights",
     "Recommendations"]
)

# Introduction page
if page == "Introduction":
    st.header("Understanding the ASD and Vaccine Exemption Relationship")
    
    # Show overview statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Counties Analyzed", len(df))
    
    with col2:
        st.metric("Avg ASD Rate (per 1,000)", f"{df['prevalence_asd_avg'].mean():.2f}")
    
    with col3:
        st.metric("Avg MMR Immunity (%)", f"{df['immune_mmr'].mean():.1f}%")
    
    with col4:
        st.metric("Avg Exemption Rate (%)", f"{df['exemption_rate'].mean():.2f}%")
    
    # Display a preview of the data
    st.subheader("Data Preview")
    key_columns = ['county_name', 'pop_sum', 'prevalence_asd_avg', 'cases_asd_sum', 
                   'immune_mmr', 'exempt_mmr', 'compliance_mmr', 'exemption_rate']
    st.dataframe(df[key_columns])
    
    # Show highest and lowest ASD counties
    st.subheader("Counties with Highest and Lowest ASD Prevalence")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Highest ASD Prevalence")
        highest_asd = df.nlargest(3, 'prevalence_asd_avg')
        st.dataframe(highest_asd[['county_name', 'prevalence_asd_avg', 'immune_mmr', 'exempt_mmr']])
        
        fig = px.bar(highest_asd, x='county_name', y='prevalence_asd_avg',
                    color='prevalence_asd_avg', color_continuous_scale='Reds',
                    title="Counties with Highest ASD Prevalence")
        fig.update_layout(xaxis_title="County", yaxis_title="ASD Prevalence per 1,000")
        st.plotly_chart(fig)
        
    with col2:
        st.markdown("### Lowest ASD Prevalence")
        lowest_asd = df.nsmallest(3, 'prevalence_asd_avg')
        st.dataframe(lowest_asd[['county_name', 'prevalence_asd_avg', 'immune_mmr', 'exempt_mmr']])
        
        fig = px.bar(lowest_asd, x='county_name', y='prevalence_asd_avg',
                    color='prevalence_asd_avg', color_continuous_scale='Blues',
                    title="Counties with Lowest ASD Prevalence")
        fig.update_layout(xaxis_title="County", yaxis_title="ASD Prevalence per 1,000")
        st.plotly_chart(fig)
    
    # Key findings
    st.subheader("Key Insights")
    st.markdown("""
    - **The Conflict**: Contrary to common myths, we don't find higher autism rates in highly vaccinated counties.
    - Counties with higher vaccine exemption rates (e.g., Mohave, Yavapai) often report higher ASD rates.
    - Counties with lower exemptions (e.g., Apache, Santa Cruz) show lower autism prevalence.
    
    This counterintuitive pattern suggests that vaccine exemption rates may be markers for different 
    socioeconomic factors and healthcare access issues that impact early autism detection and reporting.
    """)

# County Data Analysis page
elif page == "County Data Analysis":
    st.header("County-Level Data Analysis")
    
    # Display summary statistics
    st.subheader("Summary Statistics")
    numeric_cols = ['prevalence_asd_avg', 'immune_mmr', 'exempt_mmr', 'compliance_mmr', 
                    'exemption_rate']
    st.dataframe(df[numeric_cols].describe().round(4))
    
    # Data distribution
    st.subheader("Data Distributions")
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(df, x='prevalence_asd_avg', nbins=10, 
                         title="Distribution of ASD Prevalence",
                         color_discrete_sequence=['skyblue'],
                         labels={"prevalence_asd_avg": "ASD Prevalence per 1,000"})
        st.plotly_chart(fig)
        
    with col2:
        fig = px.histogram(df, x='exemption_rate', nbins=10, 
                         title="Distribution of Exemption Rates",
                         color_discrete_sequence=['lightgreen'],
                         labels={"exemption_rate": "Exemption Rate (%)"})
        st.plotly_chart(fig)
    
    # Correlation matrix
    st.subheader("Correlation Matrix")
    corr_cols = ['prevalence_asd_avg', 'immune_mmr', 'exempt_mmr', 'compliance_mmr', 
                'pbe', 'medical_exempt', 'exemption_rate']
    corr_matrix = df[corr_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    
    # Bar chart of ASD prevalence by county
    st.subheader("ASD Prevalence by County")
    sorted_df = df.sort_values(by='prevalence_asd_avg', ascending=False)
    
    fig = px.bar(sorted_df, x='county_name', y='prevalence_asd_avg',
               color='prevalence_asd_avg', color_continuous_scale='Blues',
               title="ASD Prevalence by County")
    fig.update_layout(xaxis_title="County", 
                    yaxis_title="ASD Prevalence per 1,000",
                    xaxis={'categoryorder':'total descending', 'tickangle': 45})
    st.plotly_chart(fig, use_container_width=True)
    
    # Show exemptions by type
    st.subheader("Exemption Types by County")
    
    # Sort counties by total exemption rate
    exemption_df = df.sort_values(by='exemption_rate', ascending=False)
    
    # Create the plot
    fig = px.bar(exemption_df, x='county_name', y='exemption_rate',
               color='county_name', 
               title="Total Exemption Rate by County")
    fig.update_layout(xaxis_title="County", 
                    yaxis_title="Exemption Rate (%)",
                    xaxis={'tickangle': 45},
                    showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Option to show breakdown of exemption types
    if st.checkbox("Show Breakdown of Exemption Types"):
        # Prepare data
        exemption_data = pd.melt(
            df, 
            id_vars=['county_name'], 
            value_vars=['pbe', 'medical_exempt'],
            var_name='exemption_type', 
            value_name='rate'
        )
        
        # Rename the exemption types for better readability
        exemption_data['exemption_type'] = exemption_data['exemption_type'].map({
            'pbe': 'Personal Belief Exemption',
            'medical_exempt': 'Medical Exemption'
        })
        
        # Create the plot
        county_order = df.sort_values('exemption_rate', ascending=False)['county_name'].tolist()
        
        fig = px.bar(
            exemption_data, 
            x='county_name', 
            y='rate', 
            color='exemption_type',
            title="Exemption Types by County",
            labels={"rate": "Exemption Rate (%)", "exemption_type": "Exemption Type"}
        )
        
        fig.update_layout(
            xaxis={'categoryorder': 'array', 'categoryarray': county_order, 'tickangle': 45},
            barmode='stack'
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ASD vs Exemptions page
elif page == "ASD vs Exemptions":
    st.header("ASD Prevalence vs Vaccine Exemptions")
    
    # Primary scatter plot
    st.subheader("Relationship Between ASD and Vaccination Measures")
    
    # Let user choose what to compare
    compare_var = st.radio(
        "Select vaccination measure to compare with ASD prevalence:",
        ["Exemption Rate", "MMR Immunity", "MMR Exemption"]
    )
    
    if compare_var == "Exemption Rate":
        x_var = 'exemption_rate'
        x_label = 'Total Exemption Rate (%)'
        title = "ASD Prevalence vs Total Exemption Rate"
    elif compare_var == "MMR Immunity":
        x_var = 'immune_mmr'
        x_label = 'MMR Immunity (%)'
        title = "ASD Prevalence vs MMR Immunity"
    else:
        x_var = 'exempt_mmr'
        x_label = 'MMR Exemption Rate (%)'
        title = "ASD Prevalence vs MMR Exemption Rate"
    
    # Create the scatter plot
    fig = px.scatter(df, x=x_var, y='prevalence_asd_avg', 
                   hover_name='county_name', size='pop_sum',
                   color='region', 
                   labels={
                       x_var: x_label,
                       'prevalence_asd_avg': 'ASD Prevalence per 1,000',
                       'pop_sum': 'Population'
                   },
                   title=title)
    
    # Add best-fit line
    x_values = df[x_var]
    y_values = df['prevalence_asd_avg']
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
    
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=slope * x_values + intercept,
            mode='lines',
            name=f'Best Fit Line (r={r_value:.2f}, p={p_value:.3f})',
            line=dict(color='red', dash='dash')
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display correlation coefficient and interpretation
    st.markdown(f"**Pearson Correlation Coefficient:** {r_value:.4f}")
    
    if p_value < 0.05:
        st.markdown(f"**The correlation is statistically significant (p={p_value:.4f}).**")
    else:
        st.markdown(f"**The correlation is not statistically significant (p={p_value:.4f}).**")
    
    # Side-by-side bars
    st.subheader("Side-by-Side Comparison of ASD Rates and Exemptions")
    
    # Choose which counties to display
    counties_display = st.radio(
        "Select counties to display:",
        ["All Counties", "Top 8 by ASD Rate", "Top 8 by Exemption Rate"]
    )
    
    if counties_display == "All Counties":
        display_df = df.sort_values('prevalence_asd_avg', ascending=False)
    elif counties_display == "Top 8 by ASD Rate":
        display_df = df.nlargest(8, 'prevalence_asd_avg')
    else:
        display_df = df.nlargest(8, 'exemption_rate')
    
    # Calculate averages
    avg_asd = display_df['prevalence_asd_avg'].mean()
    avg_exempt = display_df['exemption_rate'].mean()
    
    # Create plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add ASD bars
    fig.add_trace(
        go.Bar(
            x=display_df['county_name'],
            y=display_df['prevalence_asd_avg'],
            name="ASD Rate",
            marker_color='orange'
        ),
        secondary_y=False
    )
    
    # Add exemption rate bars
    fig.add_trace(
        go.Bar(
            x=display_df['county_name'],
            y=display_df['exemption_rate'],
            name="Exemption Rate",
            marker_color='green'
        ),
        secondary_y=True
    )
    
    # Add average lines
    fig.add_hline(
        y=avg_asd,
        line_dash="dash",
        line_color="red",
        name=f"Avg ASD Rate ({avg_asd:.2f})",
        secondary_y=False
    )
    
    fig.add_hline(
        y=avg_exempt,
        line_dash="dash",
        line_color="black",
        name=f"Avg Exemption Rate ({avg_exempt:.2f})",
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title_text=f"ASD Rates & Vaccination Exemptions ({counties_display})",
        legend_title="Metrics",
        xaxis=dict(title="County", tickangle=45),
        barmode='group'
    )
    
    fig.update_yaxes(title_text="ASD Rate", secondary_y=False)
    fig.update_yaxes(title_text="Exemption Rate (%)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

# Historical Trends page
elif page == "Historical Trends":
    st.header("Historical ASD Prevalence Trends")
    
    # Display the historical ASD data
    st.subheader("ASD Prevalence Over Time")
    st.dataframe(historical_asd)
    
    # Create plot of historical ASD trends
    fig = px.line(
        historical_asd.sort_values('surveillance_year'), 
        x='surveillance_year', 
        y='prevalence_rate',
        markers=True,
        labels={
            'surveillance_year': 'Surveillance Year',
            'prevalence_rate': 'Prevalence Rate (%)'
        },
        title="Autism Prevalence Rate Over Time"
    )
    
    # Add annotations for milestone events
    milestones = [
        {'year': 2000, 'event': 'M-CHAT Screening Introduced', 'color': 'red'},
        {'year': 2006, 'event': 'Combating Autism Act', 'color': 'green'},
        {'year': 2014, 'event': 'Autism Subtypes Merge into ASD', 'color': 'purple'}
    ]
    
    for milestone in milestones:
        year = milestone['year']
        event = milestone['event']
        color = milestone['color']
        
        # Find the prevalence rate for this year
        if year in historical_asd['surveillance_year'].values:
            rate = historical_asd[historical_asd['surveillance_year'] == year]['prevalence_rate'].iloc[0]
            
            # Add marker and annotation
            fig.add_scatter(
                x=[year],
                y=[rate],
                mode='markers',
                marker=dict(size=12, color=color),
                name=event,
                showlegend=True
            )
            
            fig.add_annotation(
                x=year,
                y=rate * 1.1,
                text=event,
                showarrow=True,
                arrowhead=2,
                arrowcolor=color,
                arrowsize=1,
                arrowwidth=2,
                bgcolor="white",
                bordercolor=color
            )
    
    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional visualization: prevalence in 1 in X children
    st.subheader("ASD Prevalence (1 in X Children)")
    
    fig = px.line(
        historical_asd.sort_values('surveillance_year'), 
        x='surveillance_year', 
        y='prevalence_1_in_x',
        markers=True,
        labels={
            'surveillance_year': 'Surveillance Year',
            'prevalence_1_in_x': 'Prevalence (1 in X Children)'
        },
        title="Autism Prevalence (1 in X Children) Over Time"
    )
    
    # Invert the y-axis so higher prevalence is at the top
    fig.update_layout(yaxis={'autorange': 'reversed'})
    
    # Show the plot
    st.plotly_chart(fig, use_container_width=True)
    
    # Interactive exploration: Compare county rates to historical trends
    st.subheader("Compare County Rates to Historical Trends")
    
    # Get the most recent historical prevalence rate
    latest_year = historical_asd['surveillance_year'].max()
    latest_rate = historical_asd[historical_asd['surveillance_year'] == latest_year]['prevalence_rate'].iloc[0]
    
    # Create a dataframe for comparison
    compare_df = df[['county_name', 'prevalence_asd_avg']].copy()
    compare_df['prevalence_rate'] = compare_df['prevalence_asd_avg'] / 10  # Convert from per 1,000 to percentage
    
    # Create a horizontal bar chart to compare county rates to the latest historical rate
    fig = px.bar(
        compare_df.sort_values('prevalence_rate'), 
        y='county_name', 
        x='prevalence_rate',
        orientation='h',
        color='prevalence_rate',
        labels={
            'county_name': 'County',
            'prevalence_rate': 'Prevalence Rate (%)'
        },
        title=f"County ASD Rates Compared to {latest_year} National Rate ({latest_rate:.3f}%)"
    )
    
    # Add a vertical line for the latest historical rate
    fig.add_vline(
        x=latest_rate,
        line_dash="dash",
        line_color="red",
        annotation_text=f"{latest_year} National Rate",
        annotation_position="top right"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Geographic Analysis page
elif page == "Geographic Analysis":
    st.header("Geographic Analysis")
    
    st.markdown("""
    Note: For a real implementation, we would use Arizona GeoJSON data to create accurate county maps.
    For this demonstration, we're using a simplified hexbin representation.
    """)
    
    # Create a simplified hexbin map 
    st.subheader("Simplified Arizona County Map (Hexbin)")
    
    # Hex coordinates for simplified AZ county layout (approximate positions)
    # In a real implementation, you would use GeoJSON data for accurate mapping
    hex_positions = {
        'Apache': [4, 3], 'Navajo': [3, 3], 'Coconino': [2, 3], 'Mohave': [1, 2],
        'Yavapai': [2, 2], 'Gila': [3, 2], 'Greenlee': [4, 2], 'La Paz': [1, 1],
        'Maricopa': [2, 1], 'Pinal': [3, 1], 'Graham': [4, 1], 'Yuma': [1, 0],
        'Pima': [2, 0], 'Cochise': [3, 0], 'Santa Cruz': [2, -1]
    }
    
    # Convert to DataFrame for plotting
    hex_df = pd.DataFrame({
        'county': list(hex_positions.keys()),
        'x': [pos[0] for pos in hex_positions.values()],
        'y': [pos[1] for pos in hex_positions.values()]
    })
    
    # Merge with our data
    hex_df = pd.merge(hex_df, df, left_on='county', right_on='county_name')
    
    # Create visualization options
    viz_option = st.selectbox(
        "Select data to visualize:",
        ["ASD Prevalence", "MMR Immunity", "MMR Exemptions", "Total Exemption Rate"]
    )
    
    if viz_option == "ASD Prevalence":
        value_col = 'prevalence_asd_avg'
        title = "ASD Prevalence by County"
        colorscale = 'Blues'
        legend_title = "ASD Prevalence per 1,000"
    elif viz_option == "MMR Immunity":
        value_col = 'immune_mmr'
        title = "MMR Immunity by County"
        colorscale = 'Greens'
        legend_title = "MMR Immunity (%)"
    elif viz_option == "MMR Exemptions":
        value_col = 'exempt_mmr'
        title = "MMR Exemptions by County"
        colorscale = 'Reds'
        legend_title = "MMR Exemptions (%)"
    else:
        value_col = 'exemption_rate'
        title = "Total Exemption Rate by County"
        colorscale = 'Purples'
        legend_title = "Exemption Rate (%)"
    
    # Create the hex map
    fig = px.scatter(hex_df, x='x', y='y', color=value_col, 
                    size=[20] * len(hex_df), text='county',
                    color_continuous_scale=colorscale,
                    labels={value_col: legend_title},
                    title=title)
    
    # Update to make it look more like a hex map
    fig.update_traces(marker=dict(symbol='hexagon', line=dict(width=2, color='black')),
                     textposition='middle center')
    
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Regional patterns
    st.subheader("Regional Patterns")
    
    # Group by region
    region_data = df.groupby('region').agg({
        'prevalence_asd_avg': 'mean',
        'immune_mmr': 'mean',
        'exempt_mmr': 'mean',
        'exemption_rate': 'mean',
        'county_name': 'count'
    }).reset_index()
    
    region_data.rename(columns={'county_name': 'number_of_counties'}, inplace=True)
    
    # Display regional averages
    st.dataframe(region_data.round(3))
    
    # Regional comparison chart
    st.markdown("### Regional Comparison")
    
    region_metric = st.selectbox(
        "Select metric to compare across regions:",
        ["prevalence_asd_avg", "immune_mmr", "exempt_mmr", "exemption_rate"]
    )
    
    # Create a mapping for better labels
    metric_labels = {
        "prevalence_asd_avg": "ASD Prevalence per 1,000",
        "immune_mmr": "MMR Immunity (%)",
        "exempt_mmr": "MMR Exemption Rate (%)",
        "exemption_rate": "Total Exemption Rate (%)"
    }
    
    fig = px.bar(
        region_data.sort_values(region_metric, ascending=False),
        x='region',
        y=region_metric,
        color='region',
        labels={
            'region': 'Region',
            region_metric: metric_labels[region_metric]
        },
        title=f"{metric_labels[region_metric]} by Region"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Text Analysis page - New implementation using the provided code
elif page == "Text Analysis":
    st.header("Text Analysis")
    
    st.info("This section demonstrates text analysis techniques on the county names. In a real application, you would use more meaningful text data related to ASD and vaccination.")
    
    # Word frequency analysis
    st.subheader("Word Frequency Analysis")
    
    # Run word frequency analysis
    county_word_counts = analyze_text_by_county(df, 'county_name')
    
    # Create tabs for each county
    selected_county = st.selectbox("Select a county for word frequency analysis:", sorted(df['county_name'].unique()))
    
    if selected_county in county_word_counts:
        word_counts = county_word_counts[selected_county]
        
        # Create a DataFrame for visualization
        word_df = pd.DataFrame({
            'word': list(word_counts.keys()),
            'count': list(word_counts.values())
        }).sort_values('count', ascending=False).head(10)
        
        # Display as a bar chart
        fig = px.bar(
            word_df, 
            x='word', 
            y='count',
            title=f"Top 10 Words for {selected_county} County",
            color='count'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show most common words in a table
        st.markdown("### Most Common Words")
        st.dataframe(word_df)
    
    # Sentiment analysis
    st.subheader("Sentiment Analysis")
    
    # Run sentiment analysis
    county_sentiments = analyze_sentiment_by_county(df, 'county_name')
    
    # Create a DataFrame for visualization
    sentiment_df = pd.DataFrame([
        {"county": county, "polarity": data["polarity"], "subjectivity": data["subjectivity"]}
        for county, data in county_sentiments.items()
    ])
    
    # Display sentiment analysis
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            sentiment_df.sort_values('polarity'), 
            y='county', 
            x='polarity',
            orientation='h',
            color='polarity',
            title="Sentiment Polarity by County",
            labels={"polarity": "Polarity (-1 to 1)"}
        )
        st.plotly_chart(fig)
    
    with col2:
        fig = px.bar(
            sentiment_df.sort_values('subjectivity'), 
            y='county', 
            x='subjectivity',
            orientation='h',
            color='subjectivity',
            title="Sentiment Subjectivity by County",
            labels={"subjectivity": "Subjectivity (0 to 1)"}
        )
        st.plotly_chart(fig)
    
    # WordCloud visualization
    st.subheader("WordCloud Visualization")
    
    # Generate word cloud for all county names
    country_text = ' '.join(df['county_name'].astype(str))
    wordcloud_fig = create_wordcloud_plot(country_text)
    st.pyplot(wordcloud_fig)
    
    # Add explanation
    st.markdown("""
    ### Explanation of Sentiment Analysis

    - **Polarity**: Measures how positive or negative the text is, ranging from -1 (very negative) to 1 (very positive).
    - **Subjectivity**: Measures how subjective or opinionated the text is, ranging from 0 (very objective) to 1 (very subjective).

    In a real application, you would apply these techniques to more meaningful text data such as:
    - Patient reviews of healthcare providers
    - Social media posts about autism and vaccination
    - Public health documents
    - News articles and research papers
    - Community forums and discussion groups
    """)

# Statistical Insights page
elif page == "Statistical Insights":
    st.header("Statistical Analysis")
    
    # Correlation analysis
    st.subheader("Correlation Analysis")
    
    # Create correlation matrix for numeric columns
    numeric_cols = ['prevalence_asd_avg', 'immune_mmr', 'exempt_mmr', 'compliance_mmr', 
                   'pbe', 'medical_exempt', 'exemption_rate']
    
    corr = df[numeric_cols].corr()
    
    # Heatmap of correlations
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    
    # Individual correlations with ASD
    st.markdown("### Correlations with ASD Prevalence")
    
    asd_correlations = corr['prevalence_asd_avg'].drop('prevalence_asd_avg').sort_values(ascending=False)
    
    fig = px.bar(
        x=asd_correlations.index, 
        y=asd_correlations.values,
        labels={'x': 'Variable', 'y': 'Correlation with ASD Prevalence'},
        color=asd_correlations.values,
        color_continuous_scale='RdBu_r',
        title="Variables Correlated with ASD Prevalence"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Regression analysis
    st.subheader("Regression Analysis")
    
    # Let user choose independent variables
    independent_vars = st.multiselect(
        "Select independent variables for regression:",
        ['immune_mmr', 'exempt_mmr', 'exemption_rate', 'compliance_mmr', 
         'pbe', 'medical_exempt'],
        default=['exempt_mmr', 'compliance_mmr']
    )
    
    if independent_vars:
        # Prepare data for regression
        X = df[independent_vars]
        y = df['prevalence_asd_avg']
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        # Run regression
        model = sm.OLS(y, X_with_const).fit()
        
        # Display results
        st.markdown("### Regression Results")
        st.text(model.summary().as_text())
        
        # Visualize predicted vs actual
        df['predicted_asd'] = model.predict(X_with_const)
        
        fig = px.scatter(df, x='predicted_asd', y='prevalence_asd_avg',
                        hover_name='county_name', 
                        labels={
                            'predicted_asd': 'Predicted ASD Prevalence',
                            'prevalence_asd_avg': 'Actual ASD Prevalence'
                        },
                        title="Predicted vs Actual ASD Prevalence")
        
        # Add perfect prediction line
        min_val = min(df['predicted_asd'].min(), df['prevalence_asd_avg'].min())
        max_val = max(df['predicted_asd'].max(), df['prevalence_asd_avg'].max())
        
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Perfect Prediction',
                line=dict(color='red', dash='dash')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Variable importance
        st.markdown("### Variable Importance")
        
        # Get coefficients and their absolute values
        coef = model.params.drop('const')
        abs_coef = np.abs(coef)
        
        # Normalize to sum to 100%
        importance = (abs_coef / abs_coef.sum()) * 100
        
        # Create DataFrame for plotting
        importance_df = pd.DataFrame({
            'Variable': importance.index,
            'Importance': importance.values,
            'Direction': np.where(coef > 0, 'Positive', 'Negative')
        })
        
        fig = px.bar(importance_df.sort_values('Importance', ascending=False), 
                    x='Variable', y='Importance', color='Direction',
                    color_discrete_map={'Positive': 'green', 'Negative': 'red'},
                    labels={'Importance': 'Relative Importance (%)'},
                    title="Relative Importance of Variables in Predicting ASD Prevalence")
        
        st.plotly_chart(fig, use_container_width=True)

# Recommendations page
elif page == "Recommendations":
    st.header("Key Findings & Recommendations")
    
    st.subheader("Key Findings")
    
    st.markdown("""
    Based on our analysis of the relationship between ASD prevalence and vaccine exemptions in Arizona counties:
    
    1. **No Positive Correlation with Vaccination**: There is no clear positive correlation between MMR immunity rates and autism prevalence, contradicting the myth that vaccines cause autism.
    
    2. **Counterintuitive Pattern**: Counties with higher vaccine exemption rates (e.g., Mohave, Yavapai) often report higher ASD rates, while counties with lower exemptions (e.g., Apache, Santa Cruz) show lower autism prevalence.
    
    3. **Regional Disparities**: There are significant regional disparities in ASD diagnosis rates across Arizona counties.
    
    4. **Socioeconomic Factors**: Exemption rates likely correlate with socioeconomic factors that also affect autism diagnosis rates.
    
    5. **Diagnostic Resources**: Counties with more vaccine exemptions may have weaker healthcare infrastructure, potentially affecting ASD screening and diagnosis.
    """)
    
    st.subheader("Policy Recommendations")
    
    st.markdown("""
    ### Immediate Actions
    
    1. **Standardize Reporting**: Implement consistent autism screening and reporting procedures across all counties.
    
    2. **Enhance Early Screening**: Target resources for autism screening in underserved counties, particularly those with high exemption rates.
    
    3. **Strengthen School Health Systems**: Improve school health systems in counties with high exemption rates.
    
    ### Medium-term Strategies
    
    4. **Public Education**: Address vaccine misinformation with evidence-based communication campaigns.
    
    5. **Healthcare Provider Training**: Train healthcare providers in early identification of autism spectrum disorders.
    
    6. **Data Collection Improvement**: Enhance data collection systems to capture more accurate information on autism prevalence and vaccination.
    
    ### Long-term Initiatives
    
    7. **Research Funding**: Fund research into the regional disparities in autism diagnosis and services.
    
    8. **Healthcare Infrastructure**: Improve access to pediatric developmental specialists across all counties.
    
    9. **Cross-County Collaboration**: Establish mechanisms for counties to share best practices in autism screening and services.
    """)
    
    # Create a simple visualization of recommendation priority
    st.subheader("Recommendation Priority Matrix")
    
    # Sample data for recommendations priority
    recommendations = pd.DataFrame({
        'Recommendation': [
            'Standardize Reporting', 
            'Enhance Early Screening', 
            'Strengthen School Health', 
            'Public Education',
            'Healthcare Provider Training',
            'Data Collection Improvement',
            'Research Funding',
            'Healthcare Infrastructure',
            'Cross-County Collaboration'
        ],
        'Impact': [8, 9, 7, 6, 8, 7, 5, 9, 6],
        'Feasibility': [7, 6, 5, 8, 7, 6, 4, 3, 7],
        'Timeframe': ['Short', 'Short', 'Short', 'Medium', 'Medium', 
                     'Medium', 'Long', 'Long', 'Long']
    })
    
    # Create scatter plot of recommendations
    fig = px.scatter(
        recommendations, x='Feasibility', y='Impact', color='Timeframe', size='Impact',
        text='Recommendation', size_max=15,
        color_discrete_map={'Short': 'green', 'Medium': 'blue', 'Long': 'purple'},
        labels={
            'Impact': 'Potential Impact (1-10)',
            'Feasibility': 'Implementation Feasibility (1-10)'
        },
        title="Recommendation Priority Matrix"
    )
    
    # Add quadrant lines
    fig.add_shape(
        type="line", line=dict(dash="dash", width=1),
        x0=5, y0=0, x1=5, y1=10
    )
    
    fig.add_shape(
        type="line", line=dict(dash="dash", width=1),
        x0=0, y0=5, x1=10, y1=5
    )
    
    # Add quadrant labels
    fig.add_annotation(x=7.5, y=7.5, text="High Impact, High Feasibility",
                      showarrow=False, font=dict(size=10))
    
    fig.add_annotation(x=2.5, y=7.5, text="High Impact, Low Feasibility",
                      showarrow=False, font=dict(size=10))
    
    fig.add_annotation(x=7.5, y=2.5, text="Low Impact, High Feasibility",
                      showarrow=False, font=dict(size=10))
    
    fig.add_annotation(x=2.5, y=2.5, text="Low Impact, Low Feasibility",
                      showarrow=False, font=dict(size=10))
    
    fig.update_traces(textposition='top center')
    fig.update_layout(height=600)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Final call to action
    st.subheader("Call to Action")
    
    st.markdown("""
    **To bridge the diagnostic gap, Arizona must strengthen health and education data systems, not fear vaccines.**
    
    In some Arizona counties, children aren't diagnosed with autism until years after critical developmental windows. This delay isn't just a number—it's a lost opportunity for early intervention that could significantly improve outcomes.
    
    By implementing the recommendations above, Arizona can work towards ensuring that all children, regardless of their county of residence, have access to proper screening, diagnosis, and support services.
    """)

# Run the application
# To run this app locally, save as app.py and execute: streamlit run app.py

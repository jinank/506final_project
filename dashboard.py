import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the cleaned and merged dataset
@st.cache_data
def load_data():
    url = "arizona_autism_exemptions.csv"  # Placeholder
    df = pd.read_csv(url)
    return df

df = load_data()

# Sidebar Filters
st.sidebar.title("Filters")
counties = df["county_name"].unique()
selected_county = st.sidebar.selectbox("Select County", ["All"] + list(counties))

if selected_county != "All":
    df = df[df["county_name"] == selected_county]

# Main Page
st.title("Diagnosing Disparity: Autism and Vaccine Exemptions in Arizona")

st.markdown("""
In Arizona, autism prevalence varies from **0.87 to 2.5 per 1,000 children** depending on the county. 
This dashboard explores whether this disparity relates more to **vaccination exemption rates** than to vaccine uptake itself.
""")

# Plot: ASD Rate vs Exemption Rate
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df, x="exemption_rate", y="prevalence_asd_avg", hue="county_name", s=100, ax=ax)
ax.set_title("ASD Prevalence vs Vaccine Exemption Rate")
ax.set_xlabel("Exemption Rate (%)")
ax.set_ylabel("ASD Prevalence per 1,000")
st.pyplot(fig)

# Bar Plot: ASD and Exemption Rates by County
if selected_county == "All":
    df_sorted = df.sort_values("prevalence_asd_avg", ascending=False)
    fig2, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    ax1.bar(df_sorted["county_name"], df_sorted["prevalence_asd_avg"], width=0.4, label="ASD Rate", color='orange')
    ax2.bar(df_sorted["county_name"], df_sorted["exemption_rate"], width=0.4, label="Exemption Rate", color='green', alpha=0.6)
    ax1.set_xlabel("County")
    ax1.set_ylabel("ASD Rate")
    ax2.set_ylabel("Exemption Rate (%)")
    ax1.set_title("ASD vs Exemption Rate by County")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

# Insight box
st.markdown("### Key Insight")
avg_asd = df["prevalence_asd_avg"].mean()
avg_exempt = df["exemption_rate"].mean()
st.info(f"State Average ASD Rate: **{avg_asd:.2f}** | State Average Exemption Rate: **{avg_exempt:.2f}%**")

# Footer
st.markdown("---")
st.caption("Data Source: CDC, Arizona Department of Health Services")

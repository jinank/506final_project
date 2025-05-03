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


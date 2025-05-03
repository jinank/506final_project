# streamlit_app.py

import streamlit as st
import pandas as pd
import requests, json
from textstat import flesch_reading_ease
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="2³ Factorial Readability Experiment", layout="wide")

st.title("2³ Factorial Design: LLM Readability Explorer")

# 1. Sidebar: experiment settings
st.sidebar.header("Experiment Settings")
temps = st.sidebar.selectbox("Temperature levels", options=[(0.2,0.8)], format_func=lambda x: f"{x[0]} / {x[1]}")
topk_levels = st.sidebar.selectbox("Top-k levels", options=[(10,100)], format_func=lambda x: f"{x[0]} / {x[1]}")
topp_levels = st.sidebar.selectbox("Top-p levels", options=[(0.1,0.9)], format_func=lambda x: f"{x[0]} / {x[1]}")
r = st.sidebar.slider("Replicates per cell (r)", min_value=2, max_value=8, value=4)

run_button = st.sidebar.button("Run Experiment")

if run_button:
    # 2. Build design grid
    t_low, t_high = temps
    k_low, k_high = topk_levels
    p_low, p_high = topp_levels

    grid = []
    for T in (t_low, t_high):
        for K in (k_low, k_high):
            for P in (p_low, p_high):
                for rep in range(1, r+1):
                    grid.append({"Temperature": T, "TopK": K, "TopP": P, "Replicate": rep})
    df = pd.DataFrame(grid)

    # 3. Call LLM & compute Flesch
    st.info("Collecting responses… this may take a few minutes.")
    flesch_scores = []
    for _, row in stqdm(df.iterrows(), total=len(df)):
        payload = {
            "model": "gemini-1.5",
            "messages": [
                {"role": "system", "content": "You are a readability-focused assistant."},
                {"role": "user",   "content": "Explain how factorial experiments help in tuning AI hyperparameters."}
            ],
            "temperature": row.Temperature,
            "top_p": row.TopP,
            "top_k": row.TopK,
            "max_tokens": 200
        }
        headers = {"Authorization": f"Bearer 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"}
        r = requests.post("https://api.openai.com/v1/chat/completions",
                          headers=headers, json=payload)
        text = r.json()["choices"][0]["message"]["content"]
        flesch_scores.append(flesch_reading_ease(text))


    df["Flesch"] = flesch_scores

    # 4. Show raw data & download
    st.subheader("Raw Data")
    st.dataframe(df)
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="readability_data.csv")

    # 5. Fit 2³ ANOVA
    df["Temperature"] = df["Temperature"].map({t_low:"low", t_high:"high"})
    df["TopK"] = df["TopK"].astype(str)
    df["TopP"] = df["TopP"].astype(str)
    model = ols("Flesch ~ C(Temperature)*C(TopK)*C(TopP)", data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)

    st.subheader("ANOVA Table")
    st.table(anova_table)

    # 6. Diagnostic plots
    st.subheader("Diagnostic Plots")
    fig = plt.figure(figsize=(12,6))
    sm.graphics.plot_regress_exog(model, "C(Temperature)[T.high]", fig=fig)
    st.pyplot(fig)

    # 7. Interaction plot
    st.subheader("Interaction: Temperature × TopP")
    fig2, ax2 = plt.subplots()
    means = df.groupby(["TopP","Temperature"])["Flesch"].mean().unstack()
    means.plot(kind="line", marker="o", ax=ax2)
    ax2.set_ylabel("Mean Flesch Score")
    st.pyplot(fig2)

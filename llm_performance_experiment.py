import os
import streamlit as st
import pandas as pd
import requests
import numpy as np
from textstat import flesch_reading_ease
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")
st.title("LLM Hyperparameters Experiment - Study of LLM Hyperparameters and Readability ")

# Sidebar: settings
st.sidebar.header("Experiment Settings")
temps = st.sidebar.slider(
    "Temperature (low ↔ high)",
    0.0, 1.0, (0.2, 0.8), step=0.1
)
topp = st.sidebar.slider(
    "Top-p (low ↔ high)",
    0.0, 1.0, (0.1, 0.9), step=0.1
)
topk = st.sidebar.slider(
    "Top-k (low ↔ high)",
    1, 200, (10, 100), step=1
)
r = st.sidebar.slider(
    "Replicates per cell (r)",
    2, 8, 5, step=1
)
run = st.sidebar.button("Run Experiment")

if run:
    # 1) Build full 2×2×2×r design
    grid = []
    for T in [temps[0], temps[1]]:
        for P in [topp[0], topp[1]]:
            for K in [topk[0], topk[1]]:
                for rep in range(r):
                    grid.append({"Temperature": T, "TopP": P, "TopK": K})
    df = pd.DataFrame(grid)
    df["Flesch"] = np.nan

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("Set your OPENAI_API_KEY in the environment.")
        st.stop()
    headers = {"Authorization": f"Bearer {api_key}"}
    progress = st.progress(0)

    # Loop & collect
    for i, row in df.iterrows():
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": "Write a concise summary of the benefits of factorial experiments."}
            ],
            "temperature": float(row.Temperature),
            "top_p":       float(row.TopP),
            # top_k isn’t supported by the chat endpoint, 
            # so we record it as a factor only
            "max_tokens":  5000
        }
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers, json=payload
        )
        if resp.ok:
            js = resp.json()
            txt = js["choices"][0]["message"]["content"]
        else:
            txt = ""
            st.warning(f"Run {i+1} failed: {resp.status_code}")

        df.at[i, "Flesch"] = flesch_reading_ease(txt)
        progress.progress((i + 1) / len(df))

    # Convert to categorical for ANOVA
    df["Temperature"] = pd.Categorical(
        df.Temperature, 
        categories=sorted(df.Temperature.unique()), 
        ordered=True
    )
    df["TopP"] = pd.Categorical(
        df.TopP, 
        categories=sorted(df.TopP.unique()), 
        ordered=True
    )
    df["TopK"] = pd.Categorical(
        df.TopK, 
        categories=sorted(df.TopK.unique()), 
        ordered=True
    )

    # Show raw data
    st.subheader("Raw Results")
    st.dataframe(df)

    # Fit three‐factor ANOVA
    model = ols(
        "Flesch ~ C(Temperature) * C(TopP) * C(TopK)", 
        data=df
    ).fit()
    anova = sm.stats.anova_lm(model, typ=2)

    st.subheader("ANOVA Table")
    st.dataframe(anova)

    # Diagnostic plots
    st.subheader("Diagnostics")
    fig, axes = plt.subplots(1, 2, figsize=(10,4))
    axes[0].scatter(model.fittedvalues, model.resid)
    axes[0].axhline(0, linestyle="--", color="gray")
    axes[0].set_title("Residuals vs Fitted")
    sm.qqplot(model.resid, line="45", ax=axes[1])
    axes[1].set_title("Normal Q–Q")
    st.pyplot(fig)

    # 7) Interaction plot faceted by TopK
    st.subheader("Interaction Plot (faceted by Top-k)")
    cat_int = sns.catplot(
        data=df,
        x="TopP",
        y="Flesch",
        hue="Temperature",
        col="TopK",
        kind="point",
        dodge=True,
        markers=["o", "s"],
        height=4,
        aspect=1
    )
    cat_int.fig.suptitle("Temperature × Top-p Interaction by Top-k", y=1.02)
    st.pyplot(cat_int.fig)

    # 8) Box plot faceted by TopK
    st.subheader("Boxplot: Flesch by Top-p, Temperature & Top-k")
    cat_box = sns.catplot(
        data=df,
        x="TopP",
        y="Flesch",
        hue="Temperature",
        col="TopK",
        kind="box",
        height=4,
        aspect=1
    )
    cat_box.fig.suptitle(
        "Flesch Scores by Top-p and Temperature (faceted by Top-k)",
        y=1.02
    )
    st.pyplot(cat_box.fig)



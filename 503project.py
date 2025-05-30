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

st.title("2 Factorial Design: LLM Readability Explorer")

# 1. Sidebar: experiment settings
st.sidebar.header("Experiment Settings")
temps = st.sidebar.selectbox("Temperature levels", options=[(0.2,0.8)], format_func=lambda x: f"{x[0]} / {x[1]}")
topp_levels = st.sidebar.selectbox("Top-p levels", options=[(0.1,0.9)], format_func=lambda x: f"{x[0]} / {x[1]}")
r = st.sidebar.slider("Replicates per cell (r)", min_value=2, max_value=8, value=4)

run_button = st.sidebar.button("Run Experiment")

if run_button:
    # 2. Build design grid
    t_low, t_high = temps
    p_low, p_high = topp_levels

    grid = []
    for T in temps:
        for P in topp_levels:
            for rep in range(r):
                grid.append({"Temperature": T, "TopP": P})
    df = pd.DataFrame(grid)


    # 3. Call LLM & compute Flesch
    st.info("Collecting responses… this may take a few minutes.")
    flesch_scores = []
    progress_bar = st.progress(0)
    total = len(df)

    for i, row in df.iterrows():
        payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"You are a readability-focused assistant."},
            {"role":"user",  "content":"Explain how factorial experiments help in tuning AI hyperparameters."}
        ],
        "temperature": float(row["Temperature"]),
        "top_p":       float(row["TopP"]),
        # "top_k": float(row["TopK"]),  # include only if using Top-k
        "max_tokens":  200
        }    
        headers = {"Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"}
        resp  = requests.post("https://api.openai.com/v1/chat/completions",
                          headers=headers, json=payload)
        data = resp .json()
        # check for errors
        if not resp .ok or "choices" not in data:
            st.warning(f"API call failed (status {resp .status_code}): {data.get('error', data)}")
            text = ""   # or some default/filler
        else:
            # safe extraction
            text = data["choices"][0].get("message", {}).get("content", "")

        #text = r.json()["choices"][0]["message"]["content"]
        from textstat import flesch_reading_ease
        flesch_scores.append(flesch_reading_ease(text))


        # update progress
        progress_bar.progress((i + 1) / total)

    df["Flesch"] = flesch_scores


    # 4. Show raw data & download
    st.subheader("Raw Data")
    st.dataframe(df)
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="readability_data.csv")

    # 5. Fit 2³ ANOVA
    df["Temperature"] = df["Temperature"].map({t_low:"low", t_high:"high"})
    df["TopP"] = df["TopP"].astype(str)
    model = ols("Flesch ~ C(Temperature)*C(TopP)", data=df).fit()
    import matplotlib.pyplot as plt
    import statsmodels.api as sm
    
    # Diagnostic plots
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # (a) Residuals vs. Fitted
    axes[0].scatter(model.fittedvalues, model.resid)
    axes[0].axhline(0, linestyle='--', linewidth=1)
    axes[0].set_xlabel("Fitted values")
    axes[0].set_ylabel("Residuals")
    axes[0].set_title("Residuals vs. Fitted")
    
    # (b) Normal Q–Q plot
    sm.qqplot(model.resid, line="45", ax=axes[1])
    axes[1].set_title("Normal Q–Q")
    
    st.subheader("Diagnostic Plots")
    st.pyplot(fig)

    anova_table = sm.stats.anova_lm(model, typ=2)

    st.subheader("ANOVA Table")
    st.table(anova_table)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # (a) Residuals vs. Fitted
    axes[0].scatter(model.fittedvalues, model.resid)
    axes[0].axhline(0, linestyle='--', linewidth=1)
    axes[0].set_xlabel("Fitted values")
    axes[0].set_ylabel("Residuals")
    axes[0].set_title("Residuals vs. Fitted")
    
    # (b) Normal Q–Q plot
    sm.qqplot(model.resid, line="45", ax=axes[1])
    axes[1].set_title("Normal Q–Q")
    
    st.subheader("Diagnostic Plots")
    st.pyplot(fig)
    
    # 7. Interaction plot
    st.subheader("Interaction: Temperature × TopP")
    fig2, ax2 = plt.subplots()
    means = df.groupby(["TopP","Temperature"])["Flesch"].mean().unstack()
    means.plot(kind="line", marker="o", ax=ax2)
    ax2.set_ylabel("Mean Flesch Score")
    st.pyplot(fig2)

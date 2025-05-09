import streamlit as st
import joblib
import numpy as np

# Load models
win_model = joblib.load("win_predictor_model.pkl")
bat_model = joblib.load("batsman_predictor_model.pkl")
label_encoder = joblib.load("batsman_label_encoder.pkl")

st.title("🏏 IPL Win & Batsman Run Predictor")

# --- WIN PREDICTION SECTION ---
st.header("Team Win Probability Predictor")

current_score = st.number_input("Current Score", value=85)
balls_left = st.number_input("Balls Left", value=48)
wickets_left = st.number_input("Wickets Left", value=6)
run_rate = st.number_input("Current Run Rate", value=7.5)
required_run_rate = st.number_input("Required Run Rate", value=8.3)

if st.button("Predict Win Probability"):
    win_input = np.array([[current_score, balls_left, wickets_left, run_rate, required_run_rate]])
    win_result = win_model.predict_proba(win_input)[0][1]
    st.success(f"Win Probability: {win_result * 100:.2f}%")

# --- BATSMAN RUN PREDICTION SECTION ---
st.header("Batsman Run Predictor")

batsman_name = st.text_input("Batsman Name (case-sensitive, from training data)", value="V Kohli")
balls_faced = st.number_input("Balls Faced", value=20)
bat_wickets_left = st.number_input("Wickets Left (Team)", value=7)
bat_run_rate = st.number_input("Current Run Rate", value=8.0)
bat_req_run_rate = st.number_input("Required Run Rate", value=7.9)

if st.button("Predict Batsman Runs"):
    try:
        batsman_encoded = label_encoder.transform([batsman_name])[0]
        bat_input = np.array([[batsman_encoded, balls_faced, bat_wickets_left, bat_run_rate, bat_req_run_rate]])
        predicted_runs = bat_model.predict(bat_input)[0]
        st.success(f"Predicted Runs for {batsman_name}: {predicted_runs:.1f}")
    except ValueError:
        st.error("Batsman name not found in training data. Please use a known name.")

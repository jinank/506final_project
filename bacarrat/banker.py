import streamlit as st
import pandas as pd

# --- Progression logic for Banker-only Star Stage 1 ---
class BankerProgression:
    def __init__(self, unit: float):
        self.unit = unit
        self.reset()
    
    def reset(self):
        # Stage 1 or 2
        self.stage = 1
        self.next_bet = self.unit
        # History of hands: list of tuples (hand_number, outcome, bet_amount)
        self.history = []
        # Counters
        self.sessions = 0
        self.successes = 0
        self.failures = 0

    def record_hand(self, outcome: str):
        # Record a single hand result: 'B', 'P', 'T'
        if outcome == 'T':
            # Tie: record push
            self.history.append((len(self.history)+1, outcome, self.next_bet))
            return

        # Record outcome and bet
        self.history.append((len(self.history)+1, outcome, self.next_bet))

        if outcome == 'B':
            if self.stage == 1:
                # Win on Stage 1: parlay to Stage 2
                self.stage = 2
                self.next_bet = self.unit * 2
            else:
                # Win on Stage 2: success -> reset progression
                self.successes += 1
                self.sessions += 1
                self.reset()
        else:
            # Loss: failure -> reset progression
            self.failures += 1
            self.sessions += 1
            self.reset()

# --- Streamlit App ---
st.set_page_config(layout='wide')
st.title("Banker-only Star 2.0 Stage 1 Dashboard")

# Sidebar: unit size and new progression
unit = st.sidebar.number_input("Unit Size (USD)", min_value=1.0, step=1.0, value=10.0)
if 'progress' not in st.session_state or st.sidebar.button("New Progression"):
    st.session_state.progress = BankerProgression(unit)
progress = st.session_state.progress

# Display next bet info
st.sidebar.markdown("## Next Bet")
st.sidebar.write(f"Stage: {progress.stage}")
st.sidebar.write(f"Bet Amount: ${progress.next_bet:.2f}")
st.sidebar.write("Bets Banker every hand.")

# Record Hand Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Record Banker Win"):
        progress.record_hand('B')
with col2:
    if st.button("Record Player Win"):
        progress.record_hand('P')
with col3:
    if st.button("Record Tie"):
        progress.record_hand('T')

# Show history
if progress.history:
    df_hist = pd.DataFrame(progress.history, columns=["Hand #","Outcome","Bet Amount"])
    st.markdown("### Hand History")
    st.dataframe(df_hist, use_container_width=True)

# Show summary
st.markdown("### Summary")
st.write(f"Sessions Played: {progress.sessions}")
st.write(f"Successes (two in a row wins): {progress.successes}")
st.write(f"Failures (any loss): {progress.failures}")

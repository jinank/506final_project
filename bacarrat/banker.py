import streamlit as st
import pandas as pd

# --- Progression logic for Banker-only Star 2.0 Stage 1 ---
class BankerProgression:
    def __init__(self, unit: float):
        self.unit = unit
        # full session stats
        self.history = []      # list of (hand #, outcome, bet)
        self.sessions = 0
        self.successes = 0
        self.failures = 0
        # current series state
        self.new_series()
    
    def new_series(self):
        #Start a new Star 2.0 attempt (Stage 1)
        self.stage = 1
        self.next_bet = self.unit

    def reset_all(self):
        #\"\"\"Clear entire session and series.\"\"\"
        self.history.clear()
        self.sessions = 0
        self.successes = 0
        self.failures = 0
        self.new_series()

    def record_hand(self, outcome: str):
        #\"\"\"Record a single hand result: 'B','P','T'.\"\"\"
        # ties push: collect history, no stage change
        if outcome == 'T':
            self.history.append((len(self.history)+1, outcome, self.next_bet))
            return

        # record actual bet
        self.history.append((len(self.history)+1, outcome, self.next_bet))

        if outcome == 'B':
            # win
            if self.stage == 1:
                # move to parlay stage
                self.stage = 2
                self.next_bet = self.unit * 2
            else:
                # second straight win: success
                self.successes += 1
                self.sessions += 1
                self.new_series()
        else:
            # loss
            self.failures += 1
            self.sessions += 1
            self.new_series()

# --- Streamlit App ---
st.set_page_config(layout='wide')
st.title("Banker-only Star 2.0 Stage 1 Dashboard")

# Sidebar: unit and controls
unit = st.sidebar.number_input("Unit Size (USD)", min_value=1.0, step=1.0, value=10.0)
if 'progress' not in st.session_state:
    st.session_state.progress = BankerProgression(unit)
progress = st.session_state.progress

# New progression clears full session
if st.sidebar.button("New Progression"):
    progress.reset_all()

# Display next bet info
st.sidebar.markdown("## Next Bet")
st.sidebar.write(f"Stage: {progress.stage}")
st.sidebar.write(f"Bet Amount: ${progress.next_bet:.2f}")
st.sidebar.write("Always betting Banker.")

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

# Show history table
if progress.history:
    df_hist = pd.DataFrame(progress.history, columns=["Hand #","Outcome","Bet Amount"])
    st.markdown("### Hand History")
    st.dataframe(df_hist, use_container_width=True)

# Show summary
st.markdown("### Summary")
st.write(f"Sessions played: {progress.sessions}")
st.write(f"Successes (two wins in a row): {progress.successes}")
st.write(f"Failures (any loss): {progress.failures}")

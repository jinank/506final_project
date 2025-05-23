import streamlit as st
import pandas as pd

# --- D'Alembert progression model ---
class DAlembertProgression:
    def __init__(self, unit: float):
        self.base_unit = unit
        self.reset()

    def reset(self):
        # Current bet starts at base_unit
        self.current_bet = self.base_unit
        # History: list of (hand #, outcome, bet amount, profit/loss)
        self.history = []
        # Cumulative profit
        self.profit = 0.0

    def record_hand(self, outcome: str):
        hand_no = len(self.history) + 1
        bet = self.current_bet
        profit_change = 0.0

        if outcome == 'W':
            # Win: profit equals bet, decrease bet by one unit (not below base_unit)
            profit_change = bet
            self.profit += profit_change
            self.current_bet = max(self.base_unit, self.current_bet - self.base_unit)
        elif outcome == 'L':
            # Loss: lose bet, increase bet by one unit
            profit_change = -bet
            self.profit += profit_change
            self.current_bet += self.base_unit
        else:
            # Tie/Push: no profit change and bet stays same
            profit_change = 0.0

        self.history.append((hand_no, outcome, bet, profit_change, self.profit))

# --- Streamlit App ---
st.set_page_config(layout='wide')
st.title("D'Alembert Progression Strategy")

# Sidebar: unit and reset
unit = st.sidebar.number_input("Unit Size (USD)", min_value=1.0, step=1.0, value=10.0)
if 'dalembert' not in st.session_state:
    st.session_state.dalembert = DAlembertProgression(unit)
dlem = st.session_state.dalembert

# Reset button
if st.sidebar.button("New Progression"):
    dlem = DAlembertProgression(unit)
    st.session_state.dalembert = dlem

# Display next bet
st.sidebar.markdown("## Next Bet")
st.sidebar.write(f"Current Bet: ${dlem.current_bet:.2f}")
st.sidebar.write(f"Cumulative Profit: ${dlem.profit:.2f}")

# Record Hand Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Record Win"):
        dlem.record_hand('W')
with col2:
    if st.button("Record Loss"):
        dlem.record_hand('L')
with col3:
    if st.button("Record Tie"):
        dlem.record_hand('T')

# Show history
if dlem.history:
    df = pd.DataFrame(dlem.history, columns=["Hand #", "Result", "Bet", "P/L", "Total P/L"])
    st.markdown("### Progression History")
    st.dataframe(df, use_container_width=True)

import streamlit as st
from typing import List, Dict

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        self.miss_count = 0
        self.step = 0
        self.last_two: List[str] = []

    def record_hand(self, outcome: str):
        # special handling for single-win patterns
        if self.pattern_type == 'banker_only':
            if outcome == 'B':
                # immediate hit on banker outcome
                self.miss_count = 0
                self.step = 0
            else:
                # count misses when not banker
                self.miss_count += 1
                self.step = min(self.miss_count, 11)
            return
        if self.pattern_type == 'player_only':
            if outcome == 'P':
                # immediate hit on player outcome
                self.miss_count = 0
                self.step = 0
            else:
                # count misses when not player
                self.miss_count += 1
                self.step = min(self.miss_count, 11)
            return choice or 'B'

# --- Streamlit App ---
st.set_page_config(layout='wide')
session = st.session_state.get('game')
if session is None:
    session = Session()
    st.session_state['game'] = session

# Sidebar controls
with st.sidebar:
    st.title('Bakura Algorithm MVP')
    session.unit = st.number_input('Unit Size', min_value=1.0, step=1.0, value=session.unit)
    session.strategy = st.selectbox('Strategy', ['conservative', 'aggressive', 'end_of_shoe'])
    if st.button('New Shoe'):
        session.reset_patterns()

# Main layout
grid_data = session.get_state()
st.write('### Next Bets & Miss Counts')
st.table(grid_data)

# Hand input buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button('Record Banker'):
        session.add_hand('B')
with col2:
    if st.button('Record Player'):
        session.add_hand('P')
with col3:
    if st.button('Record Tie'):
        session.add_hand('T')

# Session history
st.write('### Hand History')
st.write(' '.join(session.history))

# Profit/Loss and summary
st.write('### Summary')
state = session.get_state()
total_bet = sum(item['bet_amount'] for item in state)
st.write(f'Total needed for 12 steps: {total_bet}')

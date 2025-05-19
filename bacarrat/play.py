# Revised Bakura Streamlit MVP (4 Friends, 4-Step Star 2.0)
import streamlit as st
from typing import List, Dict
import pandas as pd

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        # Tracking
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0

    def next_bet_choice(self) -> str:
        # Define each friend's fixed repeating pattern
        if self.pattern_type == 'banker_only':
            return 'B'
        if self.pattern_type == 'player_only':
            return 'P'
        if self.pattern_type == 'alternator_start_banker':
            return ['B', 'P'][self.miss_count % 2]
        if self.pattern_type == 'alternator_start_player':
            return ['P', 'B'][self.miss_count % 2]
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        # Simplified 4-step Star 2.0 sequence
        sequence = [unit, unit * 1.5, unit * 2.5, unit * 4]
        # stay at max if step exceeds last index
        index = min(self.step, len(sequence) - 1)
        return sequence[index]

    def record_hand(self, outcome: str):
        # Compare predicted vs actual outcome
        predicted = self.next_bet_choice()
        self.last_hit = (outcome == predicted)
        if self.last_hit:
            self.total_hits += 1
            self.win_streak += 1
        else:
            self.total_misses += 1
            self.win_streak = 0

        # Reset after two consecutive wins
        if self.win_streak >= 2:
            self.miss_count = 0
            self.step = 0
        else:
            # Advance miss count and step (up to 3)
            self.miss_count += 1
            self.step = min(self.miss_count, 3)


class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        # Four friends with chosen patterns
        patterns = [
            'banker_only',
            'player_only',
            'alternator_start_banker',
            'alternator_start_player'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(4)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome)

    def get_state(self) -> pd.DataFrame:
        # Return state as DataFrame for display
        records = []
        for f in self.friends:
            records.append({
                'Name': f.name,
                'Pattern': f.pattern_type,
                'Last Bet Result': 'Win' if f.last_hit else 'Loss',
                'Miss Count': f.miss_count,
                'Next Bet': f.next_bet_choice(),
                'Next Bet Amount': f.next_bet_amount(self.unit),
                'Total Hits': f.total_hits,
                'Total Misses': f.total_misses
            })
        return pd.DataFrame(records)

# --- Streamlit App ---
st.set_page_config(layout='wide')

# Initialize or retrieve session
session = st.session_state.get('session')
if session is None:
    session = Session()
    st.session_state['session'] = session

# Sidebar controls
with st.sidebar:
    st.title('Bakura 4-Friend MVP')
    session.unit = st.number_input('Unit Size', min_value=1.0, step=1.0, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

# Main display
df = session.get_state()

# Highlight miss count of 5 in green
def highlight_five(val):
    return 'background-color: lightgreen' if val == 5 else ''

styled = df.style.applymap(highlight_five, subset=['Miss Count'])

st.write('### Next Bets & Hit/Miss per Friend')
st.dataframe(styled, use_container_width=True)

# Controls to record hands
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

# Show history and summary
st.write('### Hand History')
st.write(' '.join(session.history))

st.write('### Total Needed for 4-Step Limit')
total = df['Next Bet Amount'].sum()
st.write(f'{total}')

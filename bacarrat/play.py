# Revised Bakura Streamlit MVP (4 Friends, 4-Step Star 2.0)
import streamlit as st
from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        # Tracking variables
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0

    def next_bet_choice(self) -> str:
        # Define each friend's repeating pattern
        patterns = {
            'banker_only': lambda: 'B',
            'player_only': lambda: 'P',
            'alternator_start_banker': lambda: ['B', 'P'][self.miss_count % 2],
            'alternator_start_player': lambda: ['P', 'B'][self.miss_count % 2]
        }
        return patterns.get(self.pattern_type, lambda: 'B')()

    def next_bet_amount(self, unit: float) -> float:
        # Simplified 4-step Star 2.0 sequence
        sequence = [unit, unit * 1.5, unit * 2.5, unit * 4]
        index = min(self.step, len(sequence) - 1)
        return sequence[index]

    def record_hand(self, outcome: str):
        # Compare predicted vs actual outcome
        predicted = self.next_bet_choice()
        self.last_hit = (outcome == predicted)
        if self.last_hit:
            self.total_hits += 1
            self.win_streak += 1
            # Reset progression after two consecutive wins
            if self.win_streak >= 2:
                self.miss_count = 0
                self.step = 0
        else:
            self.total_misses += 1
            self.win_streak = 0
            # Only advance progression on a miss
            self.miss_count += 1
            self.step = min(self.miss_count, 3)

# --- Session Model ---
class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        # Four friends with specified patterns
        pattern_list = [
            'banker_only',
            'player_only',
            'alternator_start_banker',
            'alternator_start_player'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', pattern_list[i]) for i in range(4)]
        self.history = []

    def add_hand(self, outcome: str):
        # Record a new hand outcome and update each friend
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome)

    def get_state_df(self) -> pd.DataFrame:
        # Build DataFrame for display and calculations
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

# Initialize or retrieve session from state
if 'session' not in st.session_state:
    st.session_state.session = Session()
session = st.session_state.session

# Sidebar controls\with st.sidebar:
    st.title('Bakura 4-Friend MVP')
    session.unit = st.number_input('Unit Size', min_value=1.0, step=1.0, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

# Main display
st.write('### Next Bets & Hit/Miss per Friend')
df = session.get_state_df()

# Create cell-level colors for Plotly table
cell_colors = []
for _, row in df.iterrows():
    row_colors = []
    for col in df.columns:
        if col == 'Miss Count' and row['Miss Count'] == 5:
            row_colors.append('lightgreen')
        else:
            row_colors.append('white')
    cell_colors.append(row_colors)

fig = go.Figure(data=[
    go.Table(
        header=dict(values=list(df.columns), fill_color='lightgrey'),
        cells=dict(values=[df[col] for col in df.columns], fill_color=cell_colors)
    )
])
st.plotly_chart(fig, use_container_width=True)

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

# History and summary
st.write('### Hand History')
st.write(' '.join(session.history))
st.write('### Total Needed for 4-Step Limit')
total = df['Next Bet Amount'].sum() if 'Next Bet Amount' in df.columns else 0
st.write(f'{total}')

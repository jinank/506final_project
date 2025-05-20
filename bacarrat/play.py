# Bakura 4-Friend MVP with Star 2.0 Grid Layout
import streamlit as st
from typing import List
import pandas as pd
import plotly.graph_objects as go

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        # Star 2.0 tracking
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        # Hit/miss tracking
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0
        # Alternator pattern: fixed sequence and index
        if pattern_type == 'alternator_start_banker':
            self.alternator_sequence = ['B', 'P']
        elif pattern_type == 'alternator_start_player':
            self.alternator_sequence = ['P', 'B']
        else:
            self.alternator_sequence = None
        self.alternator_index = 0

    def next_bet_choice(self) -> str:
        # Alternator patterns follow a fixed B->P or P->B sequence
        if self.alternator_sequence:
            return self.alternator_sequence[self.alternator_index]
        # Fixed patterns
        if self.pattern_type == 'banker_only':
            return 'B'
        if self.pattern_type == 'player_only':
            return 'P'
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        # Custom Star progression multipliers for unit betting
        multipliers = [1, 1.5, 2.5, 2.5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30]
        sequence = [unit * m for m in multipliers]
        idx = min(self.step, len(sequence) - 1)
        return sequence[idx]

    def record_hand(self, outcome: str):
        # If alternator, only track alternation and hits/misses for that pattern
        if self.alternator_sequence:
            predicted = self.next_bet_choice()
            hit = (outcome == predicted)
            self.last_hit = hit
            if hit:
                self.total_hits += 1
            else:
                self.total_misses += 1
            # Advance alternator index for next hand
            self.alternator_index = (self.alternator_index + 1) % len(self.alternator_sequence)
            return
        # Non-alternator: Star 2.0 progression
        predicted = self.next_bet_choice()
        hit = (outcome == predicted)
        self.last_hit = hit
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            # Reset after two consecutive wins
            if self.win_streak >= 2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            # Advance progression on miss
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

    def _reset_progression(self):
        """Reset Star 2.0 progression counters."""
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0

class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        patterns = ['banker_only', 'player_only',
                    'alternator_start_banker', 'alternator_start_player']
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(4)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome)

    def get_state_df(self) -> pd.DataFrame:
        records = []
        for f in self.friends:
            records.append({
                'Name': f.name,
                'Pattern': f.pattern_type,
                'Last Bet': 'Win' if f.last_hit else 'Loss',
                'Miss Count': f.miss_count,
                'Next Bet': f.next_bet_choice(),
                'Next Amount': f.next_bet_amount(self.unit),
                'Total Hits': f.total_hits,
                'Total Misses': f.total_misses
            })
        return pd.DataFrame(records)

# --- Streamlit UI ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

# Sidebar controls
with st.sidebar:
    st.title('Bakura 4-Friend MVP')
    session.unit = st.number_input('Unit Size', 1.0, 100.0, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

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

# Star 2.0 Sequence Layout
df_star = pd.DataFrame([
    [session.unit * m for m in [1, 1.5, 2.5, 2.5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30]]
], index=['Bet Amount'], columns=list(range(1, 12)))
st.write('### Star 2.0 Sequence')
st.dataframe(df_star, use_container_width=True)

# Friend Dashboard
st.write('### Friend Dashboard')
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc['History'] = [' '.join(session.history)] * len(t_df.columns)
header = ['Metric'] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[col].tolist() for col in t_df.columns]
fig = go.Figure(data=[
    go.Table(
        header=dict(values=header, fill_color='lightgrey'),
        cells=dict(values=values, fill_color='white')
    )
])
st.plotly_chart(fig, use_container_width=True)

# Summary
total = df_star.iloc[0].sum()
st.write('### Total Needed for Star Progression')
st.write(total)

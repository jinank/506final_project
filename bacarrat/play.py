# Bakura 4-Friend MVP with Star 2.0 Grid Layout
import streamlit as st
from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0
        self.history_outcomes: List[str] = []  # track actual outcomes

    def next_bet_choice(self) -> str:
        if self.pattern_type == 'banker_only':
            return 'B'
        if self.pattern_type == 'player_only':
            return 'P'
        if self.pattern_type == 'alternator_start_banker':
            # alternate B, P
            return ['B', 'P'][self.miss_count % 2]
        if self.pattern_type == 'alternator_start_player':
            # alternate P, B
            return ['P', 'B'][self.miss_count % 2]
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        sequence = [unit, unit*1.5, unit*2.5, unit*4, unit*6.5, unit*10.5,
                    unit*17, unit*27.5, unit*44.5, unit*72, unit*116, unit*188]
        idx = min(self.step, len(sequence) - 1)
        return sequence[idx]

    def record_hand(self, outcome: str):
        # Track actual outcome
        self.history_outcomes.append(outcome)
        # Special 2-win detection for alternator patterns
        if self.pattern_type == 'alternator_start_banker' and len(self.history_outcomes) >= 2:
            if self.history_outcomes[-2:] == ['B', 'P']:
                self.last_hit = True
                self.total_hits += 2
                self.miss_count = 0
                self.step = 0
                self.win_streak = 2
                return
        if self.pattern_type == 'alternator_start_player' and len(self.history_outcomes) >= 2:
            if self.history_outcomes[-2:] == ['P', 'B']:
                self.last_hit = True
                self.total_hits += 2
                self.miss_count = 0
                self.step = 0
                self.win_streak = 2
                return
        # Fallback to standard hit/miss logic
        predicted = self.next_bet_choice()
        hit = (outcome == predicted)
        self.last_hit = hit
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak >= 2:
                self.miss_count = 0
                self.step = 0
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

# --- Session Model ---
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        patterns = ['banker_only','player_only','alternator_start_banker','alternator_start_player']
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(4)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome)

    def get_star_sequence(self) -> List[float]:
        # Return the 12-step Star 2.0 bet sequence based on current unit
        return [
            self.unit,
            self.unit*1.5,
            self.unit*2.5,
            self.unit*4,
            self.unit*6.5,
            self.unit*10.5,
            self.unit*17,
            self.unit*27.5,
            self.unit*44.5,
            self.unit*72,
            self.unit*116,
            self.unit*188,
        ]

    def get_state_df(self) -> pd.DataFrame:
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

# Hand input
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

# Star 2.0 Grid
st.write('### Star 2.0 Sequence Layout')
steps = list(range(1, 13))
# Compute the 12-step Star 2.0 bet sequence inline
unit = session.unit
bet_seq = [
    unit,
    unit * 1.5,
    unit * 2.5,
    unit * 4,
    unit * 6.5,
    unit * 10.5,
    unit * 17,
    unit * 27.5,
    unit * 44.5,
    unit * 72,
    unit * 116,
    unit * 188,
]
# Create DataFrame: single row of bet amounts under step columns
df_star = pd.DataFrame([bet_seq], index=['Bet Amount'], columns=steps)
st.dataframe(df_star, use_container_width=True)
df_star = pd.DataFrame([bet_seq], index=['Bet Amount'], columns=steps)
st.dataframe(df_star, use_container_width=True)

# Dynamic Friend Dashboard
st.write('### Friend Dashboard')
df = session.get_state_df()
# Transpose so friends are columns
t_df = df.set_index('Name').T
# Add history row
t_df.loc['Hand History'] = [' '.join(session.history)] * len(t_df.columns)
# Display with Plotly
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
st.write('### Total Needed for 12-Step Limit')
total = sum(bet_seq)
st.write(f'{total}')

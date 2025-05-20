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
        # Tracking variables
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0
        # Alternator pattern state
        if pattern_type == 'alternator_start_banker':
            self.alternator_expected = 'B'
        elif pattern_type == 'alternator_start_player':
            self.alternator_expected = 'P'
        else:
            self.alternator_expected = None
        # Actual outcome history for alternator reset detection
        self.history_outcomes: List[str] = []

    def next_bet_choice(self) -> str:
        # Alternator pattern
        if self.pattern_type.startswith('alternator') and self.alternator_expected:
            return self.alternator_expected
        # Fixed patterns
        if self.pattern_type == 'banker_only':
            return 'B'
        if self.pattern_type == 'player_only':
            return 'P'
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        sequence = [unit, unit*1.5, unit*2.5, unit*4, unit*6.5,
                    unit*10.5, unit*17, unit*27.5, unit*44.5,
                    unit*72, unit*116, unit*188]
        idx = min(self.step, len(sequence)-1)
        return sequence[idx]

    def record_hand(self, outcome: str):
        # Record actual outcome
        self.history_outcomes.append(outcome)
        # Alternator reset: once B then P are discovered in sequence
        if self.pattern_type == 'alternator_start_banker' and len(self.history_outcomes) >= 2:
            if self.history_outcomes[-2:] == ['B','P']:
                self.last_hit = True
                self.total_hits += 1
                # reset progression counters
                self.miss_count = 0
                self.step = 0
                self.win_streak = 0
                # set next expected back to start
                self.alternator_expected = 'B'
                return
        if self.pattern_type == 'alternator_start_player' and len(self.history_outcomes) >= 2:
            if self.history_outcomes[-2:] == ['P','B']:
                self.last_hit = True
                self.total_hits += 1
                self.miss_count = 0
                self.step = 0
                self.win_streak = 0
                self.alternator_expected = 'P'
                return
        # Standard Star 2.0 logic
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
        # Alternator expected flips on correct alternation
        if self.pattern_type.startswith('alternator') and hit:
            self.alternator_expected = 'P' if self.alternator_expected=='B' else 'B'
        # No reset of alternator_expected on miss (keep sequence)
# --- Session Model ---
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

# Sidebar
with st.sidebar:
    st.title('Bakura 4-Friend MVP')
    session.unit = st.number_input('Unit Size', 1.0, 100.0, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

# Record Hands Buttons
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

# Star 2.0 Grid Layout
st.write('### Star 2.0 Sequence')
steps = list(range(1,13))
unit = session.unit
bet_seq = [unit, unit*1.5, unit*2.5, unit*4, unit*6.5, unit*10.5, unit*17, unit*27.5, unit*44.5, unit*72, unit*116, unit*188]
df_star = pd.DataFrame([bet_seq], index=['Amount'], columns=steps)
st.dataframe(df_star, use_container_width=True)

# Friend Dashboard
st.write('### Friend Dashboard')
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc['History'] = [' '.join(session.history)]*len(t_df.columns)
header = ['Metric'] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[col].tolist() for col in t_df.columns]
fig = go.Figure(data=[go.Table(header=dict(values=header, fill_color='lightgrey'),
                                 cells=dict(values=values, fill_color='white'))])
st.plotly_chart(fig, use_container_width=True)

# Summary
total = sum(bet_seq)
st.write('### Total Needed for 12-Step Limit')
st.write(total)

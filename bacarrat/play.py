# play.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        # Star 2.0 progression
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        # Hit/miss tracking
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0
        # Double-on-first-win flag
        self.double_next = False
        self.last_bet_amount = 0
        # Skip miss on first bet
        self.first_bet = True
        # History of outcomes per hand
        self.history: List[str] = []
        # Pattern-specific state
        if pattern_type == 'alternator_start_banker':
            self.sequence = ['B', 'P']
            self.idx = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P', 'B']
            self.idx = 0
        elif pattern_type == 'terrific_twos':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type == 'three_pattern':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type == 'one_two_one':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type == 'two_three_two_pattern':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type == 'follow_last':
            self.sequence = None
            self.idx = None
            self.last_outcome = None
        elif pattern_type == 'two_three_two':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        else:
            self.sequence = None
            self.idx = None

    def next_bet_choice(self) -> str:
        # Determine predicted bet based on pattern
        if self.pattern_type == 'terrific_twos' and self.free_outcome is not None:
            return self.sequence[self.idx]
        if self.pattern_type == 'three_pattern' and self.free_outcome is not None:
            return self.sequence[self.idx]
        if self.pattern_type == 'one_two_one' and self.free_outcome is not None:
            return self.sequence[self.idx]
        if self.pattern_type == 'two_three_two_pattern' and self.free_outcome is not None:
            return self.sequence[self.idx]
        if self.pattern_type == 'two_three_two' and self.free_outcome is not None:
            return self.sequence[self.idx]
        if self.pattern_type == 'follow_last' and self.last_outcome is not None:
            return self.last_outcome
        if self.sequence is not None:
            return self.sequence[self.idx]
        return 'B' if self.pattern_type == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        multipliers = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        seq = [unit * m for m in multipliers]
        return seq[min(self.step, len(seq)-1)]

    def record_hand(self, outcome: str, unit: float):
        # Initialize sequences on first non-tie
        if self.pattern_type == 'terrific_twos' and not hasattr(self, 'free_outcome'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base,base,alt,alt,base,base,alt,alt,base,base]
            self.idx = 0
        if self.pattern_type == 'three_pattern' and not hasattr(self, 'free_outcome'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base]*3 + [alt]*3 + [base]*3 + [alt]*2
            self.idx = 0
        if self.pattern_type == 'one_two_one' and not hasattr(self, 'free_outcome'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base] + [alt]*2 + [base] + [alt]*2 + [base] + [alt]*2
            self.idx = 0
        if self.pattern_type == 'two_three_two_pattern' and not hasattr(self, 'free_outcome'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base] + [alt]*3 + [base]*2 + [alt]*3 + [base]*2
            self.idx = 0
        if self.pattern_type == 'two_three_two' and not hasattr(self, 'free_outcome'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base, alt, alt, base, alt, alt, base]
            self.idx = 0
        if self.pattern_type == 'follow_last' and not hasattr(self, 'last_outcome'):
            self.last_outcome = outcome

        pred = self.next_bet_choice()
        if pred == '':
            # free hand, log blank
            self.history.append('')
            if self.sequence is not None:
                self.idx = (self.idx + 1) % len(self.sequence)
            return

        # Bet amount and result
        amount = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit

        # Skip miss for first bet
        if self.first_bet:
            self.first_bet = False
            status = 'W' if hit else 'M'
            self.history.append(status)
            if hit: self.total_hits += 1
            else: self.total_misses += 1
            if self.sequence is not None:
                self.idx = (self.idx + 1) % len(self.sequence)
            if self.pattern_type == 'follow_last':
                self.last_outcome = outcome
            return

        # Star progression
        status = 'W' if hit else 'M'
        self.history.append(status)
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak == 1 and amount != unit:
                self.double_next = True
            if self.win_streak >= 2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

        # Advance sequences
        if self.sequence is not None:
            self.idx = (self.idx + 1) % len(self.sequence)
        if self.pattern_type == 'follow_last':
            self.last_outcome = outcome

    def _reset_progression(self):
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.double_next = False

class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        patterns = [
            'banker_only',
            'player_only',
            'alternator_start_banker',
            'alternator_start_player',
            'terrific_twos',
            'two_three_two',
            'follow_last',
            'three_pattern',
            'one_two_one',
            'two_three_two_pattern'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(len(patterns))]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome, self.unit)

    def get_state_df(self) -> pd.DataFrame:
        rows = []
        for f in self.friends:
            rows.append({
                'Name': f.name,
                'Pattern': f.pattern_type,
                'Last Bet': 'Win' if f.last_hit else 'Loss',
                'Miss Count': f.miss_count,
                'Next Bet': f.next_bet_choice(),
                'Next Amount': f.next_bet_amount(self.unit),
                'Total Hits': f.total_hits,
                'Total Misses': f.total_misses
            })
        return pd.DataFrame(rows)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

with st.sidebar:
    st.title('Bakura 10-Friend MVP')
    session.unit = st.number_input('Unit Size', 1.0, step=0.5, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

# Hand input
c1, c2, c3 = st.columns(3)
with c1:
    if st.button('Record Banker'):
        session.add_hand('B')
with c2:
    if st.button('Record Player'):
        session.add_hand('P')
with c3:
    if st.button('Record Tie'):
        session.add_hand('T')

# Star 2.0 Sequence
star = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
df_star = pd.DataFrame([[session.unit * m for m in star]], index=['Bet Amount'], columns=list(range(1,13)))
st.write('### Star 2.0 Sequence')
st.dataframe(df_star, use_container_width=True)

# Friend Dashboard
st.write('### Friend Dashboard')
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc['History'] = [' '.join(session.history)] * len(t_df.columns)
header = ['Metric'] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[col].tolist() for col in t_df.columns]
num = len(values[0])
cell_colors = [['white'] * num]
for col in t_df.columns:
    miss = t_df.at['Miss Count', col]
    col_cols = []
    for metric in t_df.index:
        col_cols.append('lightgreen' if metric in ('Next Bet','Next Amount') and miss >= 5 else 'white')
    cell_colors.append(col_cols)
fig = go.Figure(data=[
    go.Table(
        header=dict(values=header, fill_color='darkblue', font=dict(color='white', size=14), align='center'),
        cells=dict(values=values, fill_color=cell_colors, font=dict(color='black', size=12), align='center', height=30)
    )
])
fig.update_layout(height=650)
st.plotly_chart(fig, use_container_width=True)

# Detailed History Grid
st.write('### Hand-by-Hand Results')
hist_df = pd.DataFrame({f.name: f.history for f in session.friends}, index=[f'Hand {i+1}' for i in range(len(session.history))]).T
# Define cell colors
color_map = {'W':'lightgreen', 'M':'lightcoral', '':'lightgrey'}
cell_colors = [[color_map[val] for val in row] for row in hist_df.values]
# Build header labels
hist_header = ['Friend'] + [str(i+1) for i in range(hist_df.shape[1])]
hist_values = [hist_df.index.tolist()] + [hist_df.iloc[i].tolist() for i in range(hist_df.shape[0])]
hist_fig = go.Figure(data=[
    go.Table(
        header=dict(values=hist_header, fill_color='darkblue', font=dict(color='white',size=14), align='center'),
        cells=dict(values=hist_values, fill_color=[['white']*hist_df.shape[1]] + cell_colors, align='center', height=30)
    )
])
hist_fig.update_layout(height=400)
st.plotly_chart(hist_fig, use_container_width=True)

# Summary
total_needed = df_star.iloc[0].sum()
st.write('### Total Needed for Star Progression')
st.write(total_needed)
session_total_hits = sum(f.total_hits for f in session.friends)
session_total_misses = sum(f.total_misses for f in session.friends)
profit_units = 20
stop_units = 60
profit = session.unit * profit_units
stop = session.unit * stop_units
st.write('### Session Summary')
st.write(f"Total Wins: {session_total_hits}, Total Losses: {session_total_misses}")
st.write(f"Profit Target: {profit_units} units ({profit}), Stop Loss: {stop_units} units ({stop})")

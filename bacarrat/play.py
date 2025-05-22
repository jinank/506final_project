# play.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Friend Logic ---
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
        self.double_next = False
        self.last_bet_amount = 0
        self.first_bet = True
        self.history: List[str] = []
        # Pattern-specific initialization
        if pattern_type == 'alternator_start_banker':
            self.sequence = ['B', 'P']
            self.idx = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P', 'B']
            self.idx = 0
        elif pattern_type in ('terrific_twos', 'three_pattern', 'one_two_one', 'two_three_two_pattern'):
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type in ('chop', 'follow_last'):
            self.sequence = None
            self.idx = None
            self.last_outcome = None
        else:
            # banker_only or player_only
            self.sequence = None
            self.idx = None

    def next_bet_choice(self) -> str:
        p = self.pattern_type
        if p == 'chop':
            return '' if self.last_outcome is None else ('B' if self.last_outcome == 'P' else 'P')
        if p == 'terrific_twos' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'three_pattern' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'one_two_one' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'two_three_two_pattern' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'follow_last' and self.last_outcome:
            return self.last_outcome
        if self.sequence is not None:
            return self.sequence[self.idx]
        return 'B' if p == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        multipliers = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        return unit * multipliers[min(self.step, len(multipliers)-1)]

    def record_hand(self, outcome: str, unit: float):
        p = self.pattern_type
        # Initialize sequence on first non-tie
        if p == 'terrific_twos' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            self.sequence = [base]*2 + [alt]*2 + [base]*2 + [alt]*2 + [base]*2
            self.idx = 0
            self.free_outcome = base
            self.history.append('')
            return
        if p == 'three_pattern' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            # 2 base,3 alt,3 base,3 alt
            self.sequence = [base]*2 + [alt]*3 + [base]*3 + [alt]*3
            self.idx = 0
            self.free_outcome = base
            self.history.append('')
            return
        if p == 'one_two_one' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            # 1-2-1-2-1-2
            self.sequence = [base] + [alt]*2 + [base] + [alt]*2 + [base] + [alt]*2
            self.idx = 0
            self.free_outcome = base
            self.history.append('')
            return
        if p == 'two_three_two_pattern' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            # 1-3-2-3-2
            self.sequence = [base] + [alt]*3 + [base]*2 + [alt]*3 + [base]*2
            self.idx = 0
            self.free_outcome = base
            self.history.append('')
            return
        if p == 'chop' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome = outcome
            self.history.append('')
            return
        if p == 'follow_last' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome = outcome
            self.history.append('')
            return

        pred = self.next_bet_choice()
        if pred == '':
            if self.sequence is not None:
                self.idx = (self.idx + 1) % len(self.sequence)
            self.history.append('')
            return

        amt = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit
        # First real bet: skip miss count
        if self.first_bet:
            self.first_bet = False
            status = 'W' if hit else 'M'
            self.history.append(status)
            if hit:
                self.total_hits += 1
            else:
                self.total_misses += 1
            if self.sequence is not None:
                self.idx = (self.idx + 1) % len(self.sequence)
            if p in ('chop','follow_last'):
                self.last_outcome = outcome
            return

        status = 'W' if hit else 'M'
        self.history.append(status)
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak == 1 and amt != unit:
                self.double_next = True
            if self.win_streak >= 2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)
        if self.sequence is not None:
            self.idx = (self.idx + 1) % len(self.sequence)
        if p in ('chop','follow_last'):
            self.last_outcome = outcome

    def _reset_progression(self):
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.double_next = False

# --- Session & Streamlit App ---
class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        patterns = [
            'banker_only', 'player_only',
            'alternator_start_banker', 'alternator_start_player',
            'terrific_twos', 'chop', 'follow_last',
            'three_pattern', 'one_two_one', 'two_three_two_pattern'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(len(patterns))]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

    def get_state_df(self) -> pd.DataFrame:
        return pd.DataFrame([{
            'Name': f.name,
            'Pattern': f.pattern_type,
            'Last Bet': 'Win' if f.last_hit else 'Loss',
            'Miss Count': f.miss_count,
            'Next Bet': f.next_bet_choice(),
            'Next Amount': f.next_bet_amount(self.unit),
            'Total Hits': f.total_hits,
            'Total Misses': f.total_misses
        } for f in self.friends])

# Streamlit UI
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

with st.sidebar:
    st.title('Bakura 10-Friend MVP')
    session.unit = st.number_input('Unit Size', 1.0, step=0.5, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

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
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc['History'] = [' '.join(session.history)] * len(t_df.columns)
header = ['Metric'] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[c].tolist() for c in t_df.columns]
num = len(values[0])
cell_colors = [['white'] * num]
for col in t_df.columns:
    miss = t_df.at['Miss Count', col]
    col_cols = []
    for metric in t_df.index:
        col_cols.append('lightgreen' if metric in ('Next Bet','Next Amount') and miss >= 5 else 'white')
    cell_colors.append(col_cols)
fig = go.Figure(data=[go.Table(
    header=dict(values=header, fill_color='darkblue', font=dict(color='white'), align='center'),
    cells=dict(values=values, fill_color=cell_colors, align='center')
)])
st.plotly_chart(fig, use_container_width=True)

# Detailed History
dh = pd.DataFrame({f.name: f.history for f in session.friends}, index=[f'Hand {i+1}' for i in range(len(session.history))]).T
color_map = {'W': 'lightgreen', 'M': 'lightcoral', '': 'lightgrey'}
colors = [[color_map[val] for val in row] for row in dh.values]
hdr = ['Friend'] + list(dh.columns)
vals = [dh.index.tolist()] + [dh.loc[name].tolist() for name in dh.index]
hist_fig = go.Figure(data=[go.Table(
    header=dict(values=hdr, fill_color='darkblue', font=dict(color='white'), align='center'),
    cells=dict(values=vals, fill_color=[['white'] * dh.shape[1]] + colors, align='center')
)])
st.plotly_chart(hist_fig, use_container_width=True)

# Session Summary
st.write('### Total Needed for Star Progression')
st.write(df_star.iloc[0].sum())
Wins = sum(f.total_hits for f in session.friends)
Losses = sum(f.total_misses for f in session.friends)
st.write(f"Total Wins: {Wins}, Total Losses: {Losses}")
profit_target = 200
stop_loss = 600
st.write(f"Profit Target: {profit_target}, Stop Loss: {stop_loss}")

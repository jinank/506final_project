# play.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Model for a single friend/pattern ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type

        # Star‐2.0 progression state
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0

        # Hit/miss tracking
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0

        # Double‐on‐first‐win
        self.double_next = False
        self.last_bet_amount = 0

        # Skip counting the very first real bet as a miss
        self.first_bet = True

        # Sequence state for pattern‐based bettors:
        # Alternators, Two‐pattern, Three‐pattern, One‐two‐one, 2‐3‐2, Chop, Follow‐last
        self.free_outcome = None
        self.sequence = None
        self.idx = 0
        self.last_outcome = None

        # Define the sequence template based on pattern_type:
        if pattern_type == 'banker_only':
            pass  # no sequence
        elif pattern_type == 'player_only':
            pass
        elif pattern_type == 'alternator_start_banker':
            self.sequence = ['B','P']
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P','B']
        elif pattern_type == 'terrific_twos':
            # will build after first free hand
            pass
        elif pattern_type == 'chop':
            # will wait for free hand then always opposite
            pass
        elif pattern_type == 'three_pattern':
            pass
        elif pattern_type == 'one_two_one':
            pass
        elif pattern_type == 'two_three_two':
            pass
        elif pattern_type == 'follow_last':
            pass
        else:
            raise ValueError("Unknown pattern")

    def next_bet_choice(self) -> str:
        """Return 'B','P', or '' for free hand."""
        p = self.pattern_type

        # 1) Terrific Twos: free until first non-tie
        if p == 'terrific_twos':
            if self.free_outcome is None:
                return ''
            return self.sequence[self.idx]

        # 2) Chop: free until first non-tie, then always opposite of last_outcome
        if p == 'chop':
            if self.free_outcome is None:
                return ''
            return 'P' if self.free_outcome == 'B' else 'B'

        # 3) Three‐pattern: free until first non-tie
        if p == 'three_pattern':
            if self.free_outcome is None:
                return ''
            return self.sequence[self.idx]

        # 4) One‐Two‐One
        if p == 'one_two_one':
            if self.free_outcome is None:
                return ''
            return self.sequence[self.idx]

        # 5) Two‐Three‐Two
        if p == 'two_three_two':
            if self.free_outcome is None:
                return ''
            return self.sequence[self.idx]

        # 6) Follow‐last: free until first non-tie, then repeat last_outcome
        if p == 'follow_last':
            if self.last_outcome is None:
                return ''
            return self.last_outcome

        # 7) Alternators & fixed
        if self.sequence:
            return self.sequence[self.idx]
        return 'B' if p=='banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        """Compute Star 2.0 bet amount, doubling if flagged."""
        # Double‐on‐first‐win logic:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2

        # Standard 12‐step Star2.0 multipliers:
        mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        idx = max(0, min(self.step, len(mult)-1))
        return unit * mult[idx]

    def record_hand(self, outcome: str, unit: float):
        """Update all state given a new hand outcome."""
        p = self.pattern_type

        # Terrific Twos init
        if p=='terrific_twos' and self.free_outcome is None and outcome in ('B','P'):
            base = outcome
            alt  = 'P' if base=='B' else 'B'
            # 10‐step: BBPPBBPPBB or PPBBPPBBPP
            self.sequence = [
                base,base,alt,alt,base,base,alt,alt,base,base
            ]
            self.free_outcome = base
            self.idx = 0
            return

        # Three‐pattern init (11 steps)
        if p=='three_pattern' and self.free_outcome is None and outcome in ('B','P'):
            base = outcome
            alt  = 'P' if base=='B' else 'B'
            # 11‐step: BBPPPB B B PPP
            self.sequence = (
                [base]*2 + [alt]*3 + [base]*3 + [alt]*3
            )
            self.free_outcome = base
            self.idx = 0
            return

        # One‐Two‐One init (9 steps)
        if p=='one_two_one' and self.free_outcome is None and outcome in ('B','P'):
            base = outcome
            alt  = 'P' if base=='B' else 'B'
            self.sequence = [alt,alt,base] * 3
            self.free_outcome = base
            self.idx = 0
            return

        # Two‐Three‐Two init (10 steps)
        if p=='two_three_two' and self.free_outcome is None and outcome in ('B','P'):
            base = outcome
            alt  = 'P' if base=='B' else 'B'
            self.sequence = (
                [base] + [alt]*3 + [base]*2 + [alt]*3 + [base]*2
            )
            self.free_outcome = base
            self.idx = 0
            return

        # Chop init
        if p=='chop' and self.free_outcome is None and outcome in ('B','P'):
            self.free_outcome = outcome
            return

        # Follow‐last init
        if p=='follow_last' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome = outcome
            return

        # Determine prediction
        pred = self.next_bet_choice()
        if pred == '':
            # free hand: just advance sequence idx if any
            if self.sequence:
                self.idx = (self.idx+1) % len(self.sequence)
            return

        # Remember last bet amount for doubling logic
        self.last_bet_amount = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit

        # First‐bet: count hit but skip miss_count/progression
        if self.first_bet:
            self.first_bet = False
            if hit:
                self.total_hits += 1
                self.win_streak += 1
            else:
                self.total_misses += 1
                self.win_streak = 0
            # advance any sequence
            if self.sequence:
                self.idx = (self.idx+1) % len(self.sequence)
            if p=='follow_last' and outcome in ('B','P'):
                self.last_outcome = outcome
            return

        # Star2.0 progression logic:
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            # double on first win if not base-unit
            if self.win_streak == 1 and self.last_bet_amount != unit:
                self.double_next = True
            # reset progression only after TWO straight wins
            if self.win_streak >= 2:
                self.miss_count = 0
                self.step = 0
                self.win_streak = 0
                self.double_next = False
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

        # Advance alternator/sequences
        if self.sequence:
            self.idx = (self.idx+1) % len(self.sequence)
        if p=='follow_last' and outcome in ('B','P'):
            self.last_outcome = outcome


# --- Session to hold all friends + history ---
class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset()

    def reset(self):
        types = [
            'banker_only','player_only',
            'alternator_start_banker','alternator_start_player',
            'terrific_twos','chop',
            'three_pattern','one_two_one',
            'two_three_two','follow_last'
        ]
        self.friends = [
            FriendPattern(f'Friend {i+1}', types[i])
            for i in range(10)
        ]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

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
                'Hits': f.total_hits,
                'Misses': f.total_misses
            })
        return pd.DataFrame(rows)


# --- Streamlit UI ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
sess = st.session_state['session']

# Sidebar
with st.sidebar:
    st.title("Bakura 10-Friend MVP")
    sess.unit = st.number_input("Unit Size", min_value=1.0, step=0.5, value=sess.unit)
    if st.button("New Shoe"):
        sess.reset()

# Record Buttons
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Record Banker"):
        sess.add_hand('B')
with c2:
    if st.button("Record Player"):
        sess.add_hand('P')
with c3:
    if st.button("Record Tie"):
        sess.add_hand('T')

# Star 2.0 Sequence Display
star_mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
star_df = pd.DataFrame([[sess.unit*m for m in star_mult]],
                       index=['Bet Amt'],
                       columns=list(range(1,13)))
st.write("### Star 2.0 Progression (12 steps)")
st.dataframe(star_df, use_container_width=True)

# Friend Dashboard
df = sess.get_state_df()
t = df.set_index('Name').T
t.loc["History"] = [" ".join(sess.history)] * len(t.columns)

header = ["Metric"] + list(t.columns)
values = [t.index.tolist()] + [t[c].tolist() for c in t.columns]
num = len(values[0])

# Highlight Next Bet/Amount if Miss Count ≥ 5
cell_colors = [["white"]*num]
for col in t.columns:
    miss = t.at['Miss Count', col]
    col_col = []
    for metric in t.index:
        if metric in ("Next Bet","Next Amount") and miss>=5:
            col_col.append("lightgreen")
        else:
            col_col.append("white")
    cell_colors.append(col_col)

fig = go.Figure(data=[go.Table(
    header=dict(values=header, fill_color="darkblue",
                font=dict(color="white",size=14),align="center"),
    cells=dict(values=values, fill_color=cell_colors,
               font=dict(color="black",size=12),align="center")
)])
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

# Summary
st.write("### Summary")
st.write(f"Total hands: {len(sess.history)},  "
         f"Profit target (×unit): 20 → {20*sess.unit},  "
         f"Stop loss (×unit): 60 → {60*sess.unit}")

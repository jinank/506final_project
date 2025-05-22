import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Friend/pattern model ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type

        # Star 2.0 state
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0

        # Hit/miss tracking
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0

        # Double-on-first-win
        self.double_next = False
        self.last_bet_amount = 0.0

        # Skip first-bet miss
        self.first_bet = True

        # Sequence logic
        self.free_outcome = None
        self.sequence = None
        self.idx = 0
        self.last_outcome = None

        # Per-friend history of results
        self.history: List[str] = []

        p = pattern_type
        if p == 'alternator_start_banker':
            self.sequence = ['B', 'P']
        elif p == 'alternator_start_player':
            self.sequence = ['P', 'B']
        # terrific_twos, chop, three_pattern, one_two_one, two_three_two, follow_last
        # will initialize in record_hand()

    def next_bet_choice(self) -> str:
        p = self.pattern_type
        if p in ('terrific_twos','three_pattern','one_two_one','two_three_two'):
            if self.free_outcome is None:
                return ''
            return self.sequence[self.idx]
        if p == 'chop':
            if self.free_outcome is None:
                return ''
            return 'P' if self.free_outcome=='B' else 'B'
        if p == 'follow_last':
            if self.last_outcome is None:
                return ''
            return self.last_outcome
        if self.sequence:
            return self.sequence[self.idx]
        return 'B' if p=='banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        idx = max(0, min(self.step, len(mult)-1))
        return unit * mult[idx]

    def record_hand(self, outcome: str, unit: float):
        p = self.pattern_type

        # Initialize patterns on first non-tie
        if p=='terrific_twos' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base,base,alt,alt,base,base,alt,alt,base,base]
            self.free_outcome = base; self.idx = 0
            self.history.append(''); return

        if p=='three_pattern' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base]*2 + [alt]*3 + [base]*3 + [alt]*3
            self.free_outcome = base; self.idx = 0
            self.history.append(''); return

        if p=='one_two_one' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [alt,alt,base] * 3
            self.free_outcome = base; self.idx = 0
            self.history.append(''); return

        if p=='two_three_two' and self.free_outcome is None and outcome in ('B','P'):
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base] + [alt]*3 + [base]*2 + [alt]*3 + [base]*2
            self.free_outcome = base; self.idx = 0
            self.history.append(''); return

        if p=='chop' and self.free_outcome is None and outcome in ('B','P'):
            self.free_outcome = outcome
            self.history.append(''); return

        if p=='follow_last' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome = outcome
            self.history.append(''); return

        pred = self.next_bet_choice()
        if pred == '':
            if self.sequence:
                self.idx = (self.idx+1) % len(self.sequence)
            self.history.append(''); return

        bet_amt = self.next_bet_amount(unit)
        self.last_bet_amount = bet_amt
        hit = (outcome == pred)
        self.last_hit = hit
        self.history.append('✔' if hit else '✘')

        if self.first_bet:
            self.first_bet = False
            if hit:
                self.total_hits += 1; self.win_streak += 1
            else:
                self.total_misses += 1; self.win_streak = 0
            if self.sequence:
                self.idx = (self.idx+1) % len(self.sequence)
            if p=='follow_last' and outcome in ('B','P'):
                self.last_outcome = outcome
            return

        # Reset progression for ALL patterns on two consecutive wins
        if hit:
            self.total_hits += 1; self.win_streak += 1
            if self.win_streak == 1 and bet_amt != unit:
                self.double_next = True
            if self.win_streak >= 2:
                self.miss_count = 0
                self.step = 0
                self.win_streak = 0
                self.double_next = False
        else:
            self.total_misses += 1; self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

        if self.sequence:
            self.idx = (self.idx+1) % len(self.sequence)
        if p=='follow_last' and outcome in ('B','P'):
            self.last_outcome = outcome

# --- Session ---
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
        self.friends = [FriendPattern(f'Friend {i+1}', types[i]) for i in range(10)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

    def get_state_df(self) -> pd.DataFrame:
        rows = []
        for f in self.friends:
            rows.append({
                'Name': f.name,'Pattern': f.pattern_type,
                'Last Bet': 'Win' if f.last_hit else 'Loss',
                'Miss Count': f.miss_count,'Next Bet': f.next_bet_choice(),
                'Next Amount': f.next_bet_amount(self.unit),
                'Hits': f.total_hits,'Misses': f.total_misses
            })
        return pd.DataFrame(rows)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
sess = st.session_state['session']

with st.sidebar:
    st.title("Bakura 10-Friend MVP")
    sess.unit = st.number_input("Unit Size", 1.0, step=0.5, value=sess.unit)
    if st.button("New Shoe"):
        sess.reset()

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

star_mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
star_df = pd.DataFrame([[sess.unit*m for m in star_mult]],
                       index=['Bet Amt'], columns=list(range(1,13)))
st.write("### Star 2.0 Progression (12 steps)")
st.dataframe(star_df, use_container_width=True)

df = sess.get_state_df()
t = df.set_index('Name').T
t.loc["History"] = [" ".join(sess.history)] * len(t.columns)

header = ["Metric"] + list(t.columns)
values = [t.index.tolist()] + [t[c].tolist() for c in t.columns]
num = len(values[0])

cell_colors = [["white"] * num]
for col in t.columns:
    miss = t.at['Miss Count', col]
    col_col = []
    for metric in t.index:
        if metric in ("Next Bet", "Next Amount") and miss >= 5:
            col_col.append("lightgreen")
        else:
            col_col.append("white")
    cell_colors.append(col_col)

fig = go.Figure(data=[go.Table(
    header=dict(values=header, fill_color="darkblue",
                font=dict(color="white", size=14), align="center"),
    cells=dict(values=values, fill_color=cell_colors,
               font=dict(color="black", size=12), align="center")
)])
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)

if sess.history:
    hist_df = pd.DataFrame(
        {f.name: f.history for f in sess.friends},
        index=[f"Hand {i+1}" for i in range(len(sess.history))]
    )
    st.write("### Detailed Hand History (✔=win, ✘=miss, blank=free)")
    st.dataframe(hist_df, use_container_width=True)

st.write("### Session Summary")
st.write(f"Hands: {len(sess.history)}  Target(+20×unit): {20*sess.unit}  Stop(–60×unit): {60*sess.unit}")

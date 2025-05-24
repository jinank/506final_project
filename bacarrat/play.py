import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Friend / pattern model ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type

        # Star 2.0 progression state
        self.miss_count   = 0
        self.step         = 0
        self.win_streak   = 0

        # Hit / miss tracking
        self.last_hit     = False
        self.total_hits   = 0
        self.total_misses = 0

        # “double‐on‐first‐win” flag
        self.double_next      = False
        self.last_bet_amount  = 0.0

        # never count the very first real bet as a miss
        self.first_bet   = True

        # pattern sequencing
        self.free_outcome  = None
        self.sequence      = None
        self.idx           = 0
        self.last_outcome  = None

        # per-friend ✔/✘ history
        self.history: List[str] = []

        p = pattern_type
        if p == 'alternator_start_banker':
            self.sequence = ['B','P']
        elif p == 'alternator_start_player':
            self.sequence = ['P','B']

    def next_bet_choice(self) -> str:
        p = self.pattern_type
        if p in ('terrific_twos','three_pattern','one_two_one','two_three_two','pattern_1313'):
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
        amt = unit * mult[idx]
        self.last_bet_amount = amt
        return amt

    def record_hand(self, outcome: str, unit: float):
        p = self.pattern_type
        # dynamic sequences init...
        pred = self.next_bet_choice()
        if pred == '':
            if self.sequence:
                self.idx = (self.idx + 1) % len(self.sequence)
            self.history.append(''); return

        amt = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit
        self.history.append('✔' if hit else '✘')

        if self.first_bet:
            self.first_bet = False
            if hit:
                self.total_hits += 1; self.win_streak += 1
            else:
                self.total_misses += 1; self.win_streak = 0
            if not hit:
                self.miss_count = 1; self.step = 1
            if self.sequence:
                self.idx = (self.idx + 1) % len(self.sequence)
            if p=='follow_last' and outcome in ('B','P'):
                self.last_outcome = outcome
            return

        if hit:
            self.total_hits += 1; self.win_streak += 1
            if self.win_streak == 1 and amt != unit:
                self.double_next = True
            if self.win_streak >= 2:
                self.miss_count = 0; self.step = 0; self.win_streak = 0; self.double_next = False
        else:
            self.total_misses += 1; self.win_streak = 0
            self.miss_count += 1; self.step = min(self.miss_count, 11)

        if self.sequence:
            self.idx = (self.idx + 1) % len(self.sequence)
        if p=='follow_last' and outcome in ('B','P'):
            self.last_outcome = outcome

class Session:
    def __init__(self):
        self.unit    = 10.0
        self.history: List[str] = []
        self.reset()

    def reset(self):
        types = [
            'banker_only','player_only',
            'alternator_start_banker','alternator_start_player',
            'terrific_twos','chop',
            'follow_last','three_pattern',
            'one_two_one','two_three_two','pattern_1313'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', types[i]) for i in range(len(types))]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

    def get_state_df(self) -> pd.DataFrame:
        rows = []
        for f in self.friends:
            rows.append({
                'Name':        f.name,
                'Pattern':     f.pattern_type,
                'Last Bet':    'Win' if f.last_hit else 'Loss',
                'Miss Count':  f.miss_count,
                'Next Bet':    f.next_bet_choice(),
                'Next Amount': f.next_bet_amount(self.unit),
                'Hits':        f.total_hits,
                'Misses':      f.total_misses
            })
        return pd.DataFrame(rows)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

# Sidebar
with st.sidebar:
    st.title("Bakura 11-Friend MVP")
    session.unit = st.number_input("Unit Size", 1.0, step=0.5, value=session.unit)
    if st.button("New Shoe"):
        session.reset()

    # Conservative approach suggestion
    cons = [f.name for f in session.friends if f.miss_count > 10]
    if cons:
        names = ", ".join(cons)
        st.markdown(f"<div style='background-color:lightgreen; padding:8px; border-radius:4px;'>"
                    f"Conservative Start: Bet {session.unit} unit on {names}</div>",
                    unsafe_allow_html=True)

# Hand buttons
c1,c2,c3 = st.columns(3)
with c1:
    if st.button("Record Banker"): session.add_hand('B')
with c2:
    if st.button("Record Player"): session.add_hand('P')
with c3:
    if st.button("Record Tie"): session.add_hand('T')

# Star 2.0 progression table
star_mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
star_df = pd.DataFrame([[session.unit*m for m in star_mult]],
                       index=['Bet Amt'], columns=list(range(1,13)))
st.write("### Star 2.0 Progression (12 steps)")
st.dataframe(star_df, use_container_width=True)

# Friend dashboard
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc["History"] = [" ".join(session.history)] * len(t_df.columns)

header = ["Metric"] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[c].tolist() for c in t_df.columns]
num = len(values[0])

# build cell colors, highlight Name if misses >10, highlight Next Bet/Amount if misses >=5
cell_colors = [["white"]*num]
for col in t_df.columns:
    miss = t_df.at['Miss Count', col]
    col_col = []
    for metric in t_df.index:
        if metric == "Name" and miss > 10:
            col_col.append("lightblue")
        elif metric in ("Next Bet","Next Amount") and miss >= 5:
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

# Detailed per-hand history
if session.history:
    hist_df = pd.DataFrame(
        {f.name: f.history for f in session.friends},
        index=[f"Hand {i+1}" for i in range(len(session.history))]
    )
    st.write("### Detailed Hand History (✔=win, ✘=miss, blank=free)")
    st.dataframe(hist_df, use_container_width=True)

# Session summary
st.write("### Session Summary")
st.write(f"Hands: {len(session.history)}  "
         f"Target(+20×unit): {20*session.unit}  "
         f"Stop(–60×unit): {60*session.unit}")

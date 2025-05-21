# Bakura 5-Friend MVP with Star 2.0 Grid Layout (Terrific Twos & Double-on-first-win)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        # Star 2.0 progression tracking
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
        # Skip miss count on first bet
        self.first_bet = True
        # Sequence patterns
        if pattern_type == 'alternator_start_banker':
            self.sequence = ['B', 'P']
            self.seq_index = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P', 'B']
            self.seq_index = 0
        elif pattern_type == 'terrific_twos':
            self.sequence = None
            self.seq_index = 0
            self.free_outcome = None
        else:
            self.sequence = None
            self.seq_index = None

    def next_bet_choice(self) -> str:
        if self.pattern_type == 'terrific_twos':
            if self.free_outcome is None:
                return ''
            return self.sequence[self.seq_index]
        if self.sequence is not None:
            return self.sequence[self.seq_index]
        return 'B' if self.pattern_type == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        multipliers = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        sequence = [unit * m for m in multipliers]
        idx = min(self.step, len(sequence) - 1)
        return sequence[idx]

        def record_hand(self, outcome: str, unit: float):
        # 1) Terrific Twos free hand initialization
        if self.pattern_type == 'terrific_twos':
            if self.free_outcome is None and outcome in ['B','P']:
                self.free_outcome = outcome
                base = outcome
                alt = 'P' if base=='B' else 'B'
                # Build 10-step two-pattern
                self.sequence = [base, base, alt, alt, base, base, alt, alt, base, base]
                self.seq_index = 0
                return
        # 2) Prediction for actual bets
        predicted = self.next_bet_choice()
        if predicted == '':
            return  # still waiting on free hand
        # 3) Handle first actual bet: skip miss_count/progression
        hit = (outcome == predicted)
        self.last_hit = hit
        if self.first_bet:
            self.first_bet = False
            if hit:
                self.total_hits += 1
                self.win_streak += 1
            else:
                self.total_misses += 1
                self.win_streak = 0
            # Advance sequence pointer if sequence
            if self.sequence is not None:
                self.seq_index = (self.seq_index + 1) % len(self.sequence)
            return
        # 4) Standard Star 2.0 progression with double-on-first-win
        self.last_bet_amount = self.next_bet_amount(unit)
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak == 1 and self.last_bet_amount != unit:
                self.double_next = True
            if self.win_streak >= 2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            max_step = len([1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]) - 1
            self.step = min(self.miss_count, max_step)
        # 5) Advance sequence pointer if sequence
        if self.sequence is not None:
            self.seq_index = (self.seq_index + 1) % len(self.sequence)

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
        patterns = ['banker_only','player_only','alternator_start_banker','alternator_start_player','terrific_twos']
        self.friends = [FriendPattern(f'Friend {i+1}',patterns[i]) for i in range(len(patterns))]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome,self.unit)

    def get_state_df(self) -> pd.DataFrame:
        rec = []
        for f in self.friends:
            rec.append({
                'Name':f.name,
                'Pattern':f.pattern_type,
                'Last Bet':'Win' if f.last_hit else 'Loss',
                'Miss Count':f.miss_count,
                'Next Bet':f.next_bet_choice(),
                'Next Amount':f.next_bet_amount(self.unit),
                'Total Hits':f.total_hits,
                'Total Misses':f.total_misses
            })
        return pd.DataFrame(rec)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']
with st.sidebar:
    st.title('Bakura 5-Friend MVP')
    session.unit = st.number_input('Unit Size',min_value=1.0,step=0.5,value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()
cols = st.columns(3)
with cols[0]:
    if st.button('Record Banker'):
        session.add_hand('B')
with cols[1]:
    if st.button('Record Player'):
        session.add_hand('P')
with cols[2]:
    if st.button('Record Tie'):
        session.add_hand('T')
# Star 2.0 Sequence Layout
star = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
df_star = pd.DataFrame([[session.unit*m for m in star]],index=['Bet Amount'],columns=list(range(1,13)))
st.write('### Star 2.0 Sequence')
st.dataframe(df_star,use_container_width=True)
# Friend Dashboard
st.write('### Friend Dashboard')
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc['History'] = [' '.join(session.history)]*len(t_df.columns)
header = ['Metric']+list(t_df.columns)
values=[t_df.index.tolist()]+[t_df[col].tolist() for col in t_df.columns]
num=len(values[0])
cell_colors=[['white']*num]
for col in t_df.columns:
    miss=t_df.at['Miss Count',col]
    colors=[]
    for m in t_df.index:
        if m in ['Next Bet','Next Amount'] and miss>=5:
            colors.append('lightgreen')
        else:
            colors.append('white')
    cell_colors.append(colors)
fig=go.Figure(data=[go.Table(header=dict(values=header,fill_color='darkblue',font=dict(color='white',size=14),align='center'),cells=dict(values=values,fill_color=cell_colors,font=dict(color='black',size=12),align='center',height=30))])
fig.update_layout(height=500)
st.plotly_chart(fig,use_container_width=True)
# Summary
st.write('### Total Needed for Star Progression')
st.write(df_star.iloc[0].sum())

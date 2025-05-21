# Bakura 6-Friend MVP with Star 2.0 Grid Layout (Chop & Terrific Twos & Alternators)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

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
        # Double-on-first-win flag
        self.double_next = False
        self.last_bet_amount = 0
        # Skip miss count on first bet
        self.first_bet = True
        # Pattern-specific state
        if pattern_type == 'alternator_start_banker':
            self.sequence = ['B','P']
            self.seq_index = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P','B']
            self.seq_index = 0
        elif pattern_type == 'terrific_twos':
            self.sequence = None
            self.seq_index = 0
            self.free_outcome = None
        elif pattern_type == 'chop':
            self.sequence = None
            self.seq_index = None
            self.free_outcome = None
            self.last_outcome = None
        else:
            self.sequence = None
            self.seq_index = None

    def next_bet_choice(self) -> str:
        # Terrific Twos: free until first outcome, then fixed sequence
        if self.pattern_type == 'terrific_twos':
            if self.free_outcome is None: return ''
            return self.sequence[self.seq_index]
        # Chop: free until first outcome, then bet opposite of last outcome
        if self.pattern_type == 'chop':
            if self.free_outcome is None: return ''
            return 'P' if self.last_outcome == 'B' else 'B'
        # Alternators follow their sequence
        if self.sequence is not None:
            return self.sequence[self.seq_index]
        # Fixed patterns
        return 'B' if self.pattern_type == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        # Star 2.0 multipliers (12-step)
        mults = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        seq = [unit * m for m in mults]
        idx = min(self.step, len(seq)-1)
        return seq[idx]

        def record_hand(self, outcome: str, unit: float):
        # define Star multipliers for reuse
            mults = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        # 1) Terrific Twos init
        if self.pattern_type == 'terrific_twos':
            if self.free_outcome is None and outcome in ['B','P']:
                self.free_outcome = outcome
                base,alt = outcome, 'P' if outcome=='B' else 'B'
                self.sequence = [base,base,alt,alt,base,base,alt,alt,base,base]
                self.seq_index = 0
                return
        # 2) Chop init
        if self.pattern_type == 'chop':
            if self.free_outcome is None and outcome in ['B','P']:
                self.free_outcome = outcome
                self.last_outcome = outcome
                return
        # 3) Determine predicted
        predicted = self.next_bet_choice()
        if predicted == '':  # still free hand
            return
        # 4) First actual bet: skip miss progression
        hit = (outcome == predicted)
        self.last_hit = hit
        if self.first_bet:
            self.first_bet = False
            if hit:
                self.total_hits += 1
                self.win_streak += 1
            else:
                # do not count miss_count
                self.total_misses += 1
                self.win_streak = 0
            # Advance pattern pointer
            if self.sequence:
                self.seq_index = (self.seq_index+1)%len(self.sequence)
            if self.pattern_type == 'chop':
                self.last_outcome = outcome
            return
        # 5) Standard Star 2.0 progression
        self.last_bet_amount = self.next_bet_amount(unit)
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak==1 and self.last_bet_amount!=unit:
                self.double_next=True
            if self.win_streak>=2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, len(mults)-1)
        # 6) Advance pattern pointer
        if self.sequence:
            self.seq_index = (self.seq_index+1)%len(self.sequence)
        if self.pattern_type=='chop':
            self.last_outcome = outcome

    def _reset_progression(self):
        self.miss_count=0; self.step=0; self.win_streak=0; self.double_next=False

class Session:
    def __init__(self):
        self.unit=10.0
        self.history:List[str]=[]
        self.reset_patterns()
    def reset_patterns(self):
        pats=['banker_only','player_only','alternator_start_banker','alternator_start_player','terrific_twos','chop']
        self.friends=[FriendPattern(f'Friend {i+1}',pats[i]) for i in range(len(pats))]
        self.history=[]
    def add_hand(self,outcome:str):
        self.history.append(outcome)
        for f in self.friends: f.record_hand(outcome,self.unit)
    def get_state_df(self)->pd.DataFrame:
        rec=[]
        for f in self.friends:
            rec.append({
                'Name':f.name,'Pattern':f.pattern_type,'Last Bet':'Win' if f.last_hit else 'Loss',
                'Miss Count':f.miss_count,'Next Bet':f.next_bet_choice(),'Next Amount':f.next_bet_amount(self.unit),
                'Total Hits':f.total_hits,'Total Misses':f.total_misses
            })
        return pd.DataFrame(rec)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state: st.session_state['session']=Session()
session=st.session_state['session']
with st.sidebar:
    st.title('Bakura 6-Friend MVP')
    session.unit=st.number_input('Unit Size',1.0,step=0.5,value=session.unit)
    if st.button('New Shoe'): session.reset_patterns()
cols=st.columns(3)
if cols[0].button('Record Banker'): session.add_hand('B')
if cols[1].button('Record Player'): session.add_hand('P')
if cols[2].button('Record Tie'): session.add_hand('T')
# Star 2.0 Sequence
star=[1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
df_star=pd.DataFrame([[session.unit*m for m in star]],index=['Bet Amount'],columns=list(range(1,13)))
st.write('### Star 2.0 Sequence')
st.dataframe(df_star,use_container_width=True)
# Dashboard
st.write('### Friend Dashboard')
df=session.get_state_df()
t_df=df.set_index('Name').T
t_df.loc['History']=[' '.join(session.history)]*len(t_df.columns)
header=['Metric']+list(t_df.columns)
values=[t_df.index.tolist()]+[t_df[c].tolist() for c in t_df.columns]
num=len(values[0])
cell_colors=[['white']*num]
for c in t_df.columns:
    miss=t_df.at['Miss Count',c]
    cols=[]
    for m in t_df.index:
        if m in ['Next Bet','Next Amount'] and miss>=5: cols.append('lightgreen')
        else: cols.append('white')
    cell_colors.append(cols)
fig=go.Figure(data=[go.Table(header=dict(values=header,fill_color='darkblue',font=dict(color='white',size=14),align='center'),cells=dict(values=values,fill_color=cell_colors,font=dict(color='black',size=12),align='center',height=30))])
fig.update_layout(height=550)
st.plotly_chart(fig,use_container_width=True)
# Summary
st.write('### Total Needed for Star Progression')
st.write(df_star.iloc[0].sum())

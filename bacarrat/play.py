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
        # Double-on-first-win
        self.double_next = False
        self.last_bet_amount = 0
        # Skip miss on first bet
        self.first_bet = True
        # History
        self.history: List[str] = []
        # Pattern-specific state
        if pattern_type == 'alternator_start_banker':
            self.sequence = ['B','P']
            self.idx = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P','B']
            self.idx = 0
        elif pattern_type == 'terrific_twos':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type == 'chop':
            # Chop: opposite of last non-tie
            self.sequence = None
            self.idx = None
            self.last_outcome = None
        elif pattern_type == 'follow_last':
            self.sequence = None
            self.idx = None
            self.last_outcome = None
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
        else:
            # banker_only or player_only
            self.sequence = None
            self.idx = None

    def next_bet_choice(self) -> str:
        # Chop: free until first non-tie, then opposite
        if self.pattern_type == 'chop':
            if self.last_outcome is None:
                return ''
            return 'B' if self.last_outcome=='P' else 'P'
        # Terrific Twos
        if self.pattern_type == 'terrific_twos' and self.free_outcome is not None:
            return self.sequence[self.idx]
        # Three Pattern
        if self.pattern_type == 'three_pattern' and self.free_outcome is not None:
            return self.sequence[self.idx]
        # One-Two-One
        if self.pattern_type == 'one_two_one' and self.free_outcome is not None:
            return self.sequence[self.idx]
        # 232 Pattern
        if self.pattern_type == 'two_three_two_pattern' and self.free_outcome is not None:
            return self.sequence[self.idx]
        # Follow Last
        if self.pattern_type == 'follow_last' and self.last_outcome is not None:
            return self.last_outcome
        # Alternators
        if self.sequence is not None:
            return self.sequence[self.idx]
        # Fixed
        return 'B' if self.pattern_type=='banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        mults = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        seq = [unit*m for m in mults]
        return seq[min(self.step,len(seq)-1)]

    def record_hand(self, outcome: str, unit: float):
        # Initialize Terrific Twos
        if self.pattern_type=='terrific_twos' and self.free_outcome is None and outcome in ('B','P'):
            base,alt=outcome,('P' if outcome=='B' else 'B')
            self.sequence=[base,base,alt,alt,base,base,alt,alt,base,base]
            self.idx=0; self.free_outcome=base
            self.history.append('')
            return
        # Initialize Chop
        if self.pattern_type=='chop' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome=outcome; self.history.append(''); return
        # Initialize Follow Last
        if self.pattern_type=='follow_last' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome=outcome; self.history.append(''); return
        # Initialize Three Pattern
        if self.pattern_type=='three_pattern' and self.free_outcome is None and outcome in ('B','P'):
            base,alt=outcome,('P' if outcome=='B' else 'B')
            self.sequence=[base]*3+[alt]*3+[base]*3+[alt]*2
            self.idx=0; self.free_outcome=base
            self.history.append(''); return
        # Initialize One-Two-One
        if self.pattern_type=='one_two_one' and self.free_outcome is None and outcome in ('B','P'):
            base,alt=outcome,('P' if outcome=='B' else 'B')
            self.sequence=[base]+[alt]*2+[base]+[alt]*2+[base]+[alt]*2
            self.idx=0; self.free_outcome=base
            self.history.append(''); return
        # Initialize 2-3-2 Pattern
        if self.pattern_type=='two_three_two_pattern' and self.free_outcome is None and outcome in ('B','P'):
            base,alt=outcome,('P' if outcome=='B' else 'B')
            self.sequence=[base]+[alt]*3+[base]*2+[alt]*3+[base]*2
            self.idx=0; self.free_outcome=base
            self.history.append(''); return

        pred=self.next_bet_choice()
        if pred=='':
            if self.sequence is not None: self.idx=(self.idx+1)%len(self.sequence)
            self.history.append(''); return

        amount=self.next_bet_amount(unit)
        hit=(outcome==pred)
        self.last_hit=hit
        # First real bet: skip miss
        if self.first_bet:
            self.first_bet=False
            status='W' if hit else 'M'
            self.history.append(status)
            if hit: self.total_hits+=1
            else: self.total_misses+=1
            if self.sequence is not None: self.idx=(self.idx+1)%len(self.sequence)
            if self.pattern_type=='chop': self.last_outcome=outcome
            if self.pattern_type=='follow_last': self.last_outcome=outcome
            return
        # Star progression
        status='W' if hit else 'M'
        self.history.append(status)
        if hit:
            self.total_hits+=1; self.win_streak+=1
            if self.win_streak==1 and amount!=unit: self.double_next=True
            if self.win_streak>=2: self._reset_progression()
        else:
            self.total_misses+=1; self.win_streak=0; self.miss_count+=1; self.step=min(self.miss_count,11)
        # Advance sequences
        if self.sequence is not None: self.idx=(self.idx+1)%len(self.sequence)
        if self.pattern_type=='chop': self.last_outcome=outcome
        if self.pattern_type=='follow_last': self.last_outcome=outcome

    def _reset_progression(self):
        self.miss_count=0; self.step=0; self.win_streak=0; self.double_next=False

class Session:
    def __init__(self):
        self.unit=10.0; self.history=[]; self.reset_patterns()
    def reset_patterns(self):
        patterns=[
            'banker_only','player_only','alternator_start_banker','alternator_start_player',
            'terrific_twos','chop','follow_last','three_pattern','one_two_one','two_three_two_pattern'
        ]
        self.friends=[FriendPattern(f'Friend {i+1}',patterns[i]) for i in range(len(patterns))]
        self.history=[]
    def add_hand(self,o): self.history.append(o); [f.record_hand(o,self.unit) for f in self.friends]
    def get_state_df(self): return pd.DataFrame([{
            'Name':f.name,'Pattern':f.pattern_type,'Last Bet':'Win' if f.last_hit else 'Loss',
            'Miss Count':f.miss_count,'Next Bet':f.next_bet_choice(),
            'Next Amount':f.next_bet_amount(self.unit),'Total Hits':f.total_hits,'Total Misses':f.total_misses
        } for f in self.friends])

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state: st.session_state['session']=Session()
session=st.session_state['session']
with st.sidebar:
    st.title('Bakura 10-Friend MVP')
    session.unit=st.number_input('Unit Size',1.0,step=0.5,value=session.unit)
    if st.button('New Shoe'): session.reset_patterns()
# Input Buttons
c1,c2,c3=st.columns(3)
with c1: st.button('Record Banker') and session.add_hand('B')
with c2: st.button('Record Player') and session.add_hand('P')
with c3: st.button('Record Tie') and session.add_hand('T')
# Display Sequence/Table/History/Summary omitted for brevity

# ... rest of UI remains the same ...

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Friend / pattern model ---
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
        self.last_bet_amount = 0.0

        self.first_bet = True

        self.free_outcome = None
        self.sequence = None
        self.idx = 0
        self.last_outcome = None

        self.history: List[str] = []

        p = pattern_type
        if p == 'alternator_start_banker':
            self.sequence = ['B','P']
        elif p == 'alternator_start_player':
            self.sequence = ['P','B']

    def next_bet_choice(self) -> str:
        p = self.pattern_type
        if p in ('terrific_twos','three_pattern','one_two_one','two_three_two','pattern_1313'):
            return '' if self.free_outcome is None else self.sequence[self.idx]
        if p == 'chop':
            return '' if self.free_outcome is None else ('P' if self.free_outcome=='B' else 'B')
        if p == 'follow_last':
            return '' if self.last_outcome is None else self.last_outcome
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
        # [pattern initialization omitted for brevity]
        pred = self.next_bet_choice()
        if pred == '':
            if self.sequence:
                self.idx = (self.idx+1) % len(self.sequence)
            self.history.append('')
            return
        amt = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit
        self.history.append('✔' if hit else '✘')
        # [progression logic omitted for brevity]

class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.meta_history: List[dict] = []
        self.total_meta_pl = 0.0
        self.reset()

    def reset(self):
        types = [
            'banker_only','player_only',
            'alternator_start_banker','alternator_start_player',
            'terrific_twos','chop',
            'follow_last','three_pattern',
            'one_two_one','two_three_two','pattern_1313'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', types[i])
                        for i in range(len(types))]
        self.history.clear()
        self.meta_history.clear()
        self.total_meta_pl = 0.0

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

    def record_meta(self, outcome: str, friend, bet_side: str, amount: float):
        # Calculate P/L for the suggested bet
        if outcome == 'T':
            pl = 0.0
        elif outcome == bet_side:
            pl = amount * (0.95 if bet_side == 'B' else 1.0)
        else:
            pl = -amount
        self.total_meta_pl += pl
        self.meta_history.append({
            'Hand': len(self.history)+1,
            'Friend': friend.name,
            'Bet': bet_side,
            'Amount': amount,
            'Outcome': outcome,
            'P/L': pl,
            'Cum P/L': self.total_meta_pl
        })

    def get_state_df(self) -> pd.DataFrame:
        # as before...
        pass

# Precomputed odds
WIN_PROB = {'B': 0.4586, 'P': 0.4462}

# Streamlit App
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

# Sidebar Meta-EV suggestion
# [compute best_ev, ev_cands as before]
if ev_cands:
    friend0, b0 = ev_cands[0]
    amt0 = friend0.next_bet_amount(session.unit)

# Hand Buttons with meta recording
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Record Banker"):
        session.record_meta('B', friend0, b0, amt0)
        session.add_hand('B')
with c2:
    if st.button("Record Player"):
        session.record_meta('P', friend0, b0, amt0)
        session.add_hand('P')
with c3:
    if st.button("Record Tie"):
        session.record_meta('T', friend0, b0, amt0)
        session.add_hand('T')

# ... existing tables ...

# Meta-EV bet history
if session.meta_history:
    df_meta = pd.DataFrame(session.meta_history)
    st.write("### Meta-EV Bet History")
    st.dataframe(df_meta, use_container_width=True)

# Overall P/L
st.write(f"### Meta-EV Session P/L: ${session.total_meta_pl:.2f}")

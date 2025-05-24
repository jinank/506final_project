import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Friend / pattern model ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        # progression state
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        # tracking
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0
        self.double_next = False
        self.last_bet_amount = 0.0
        self.first_bet = True
        # sequencing
        self.free_outcome = None
        self.sequence = None
        self.idx = 0
        self.last_outcome = None
        # history
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
        # Star 2.0 ladder multipliers
        mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        idx = max(0, min(self.step, len(mult)-1))
        amt = unit * mult[idx]
        self.last_bet_amount = amt
        return amt

    def record_hand(self, outcome: str, unit: float):
        p = self.pattern_type
        # dynamic patterns initialization omitted for brevity ...

        pred = self.next_bet_choice()
        if pred == '':
            # free hand
            if self.sequence:
                self.idx = (self.idx + 1) % len(self.sequence)
            self.history.append('')
            return

        amt = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit
        self.history.append('✔' if hit else '✘')

        # first real bet: count miss
        if self.first_bet:
            self.first_bet = False
            self.total_hits += int(hit)
            self.total_misses += int(not hit)
            if not hit:
                self.miss_count = 1
                self.step = 1
            self.win_streak = 1 if hit else 0
            if self.sequence:
                self.idx = (self.idx + 1) % len(self.sequence)
            if p=='follow_last' and outcome in ('B','P'):
                self.last_outcome = outcome
            return

        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak == 1 and amt != unit:
                self.double_next = True
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

        if self.sequence:
            self.idx = (self.idx + 1) % len(self.sequence)
        if p=='follow_last' and outcome in ('B','P'):
            self.last_outcome = outcome

# --- Session with Meta-EV tracking ---
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
        self.friends = [FriendPattern(f'Friend {i+1}', types[i]) for i in range(len(types))]
        self.history.clear()
        self.meta_history.clear()
        self.total_meta_pl = 0.0

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

    def record_meta(self, outcome: str, friend, bet_side: str, amount: float):
        if outcome == 'T':
            pl = 0.0
        elif outcome == bet_side:
            pl = amount * (0.95 if bet_side=='B' else 1.0)
        else:
            pl = -amount
        self.total_meta_pl += pl
        self.meta_history.append({
            'Hand': len(self.history)+1,
            'Friend': friend.name if friend else '',
            'Bet': bet_side,
            'Amount': amount,
            'Outcome': outcome,
            'P/L': pl,
            'Cum P/L': self.total_meta_pl
        })

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

WIN_PROB = {'B':0.4586,'P':0.4462}

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

# Predeclare Meta vars
best_ev = -1e9
ev_cands = []
friend0 = None
meta_bet = ""
meta_amt = 0.0

# Sidebar: Meta-EV
with st.sidebar:
    st.title("Meta-EV Strategy")
    session.unit = st.number_input("Unit Size",1.0,step=0.5,value=session.unit)
    if st.button("New Shoe"):
        session.reset()

    # EV calculation using actual next_bet_amount
    best_ev = -1e9
    ev_cands = []
    for f in session.friends:
        b1 = f.next_bet_choice()
        if b1 not in WIN_PROB:
            continue
        amt1 = f.next_bet_amount(session.unit)
        amt2 = amt1 * 2
        b2 = f.sequence[(f.idx+1)%len(f.sequence)] if f.sequence else b1
        p1,p2 = WIN_PROB[b1], WIN_PROB[b2]
        pay1 = 0.95 if b1=='B' else 1.0
        pay2 = 0.95 if b2=='B' else 1.0
        ev = (
            p1*p2*(pay1*amt1 + pay2*amt2)
            + p1*(1-p2)*(pay1*amt1 - (amt1+amt2))
            + (1-p1)*(-amt1)
        )
        if ev > best_ev + 1e-6:
            best_ev = ev; ev_cands = [(f,b1,amt1)]
        elif abs(ev-best_ev) < 1e-6:
            ev_cands.append((f,b1,amt1))

    if ev_cands:
        # determine display
        bets = {b for _,b,_ in ev_cands}
        if len(ev_cands)>1 and len(bets)>1:
            friend0, meta_bet, meta_amt = None, "NB", 0.0
        else:
            friend0, meta_bet, meta_amt = ev_cands[0]
        st.markdown(
            f"**Meta-EV**: {best_ev:.2f}  \n"
            f"Friend(s): {', '.join(f.name for f,_,_ in ev_cands)}  \n"
            f"Bet: {meta_bet}  \n"
            f"Amt: ${meta_amt:.2f}"
        )

# Hand entry
c1,c2,c3 = st.columns(3)
with c1:
    if st.button("Record B"):
        session.record_meta('B', friend0, meta_bet, meta_amt)
        session.add_hand('B')
with c2:
    if st.button("Record P"):
        session.record_meta('P', friend0, meta_bet, meta_amt)
        session.add_hand('P')
with c3:
    if st.button("Record T"):
        session.record_meta('T', friend0, meta_bet, meta_amt)
        session.add_hand('T')

# Star 2.0 progression
star_mult=[1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
star_df=pd.DataFrame([[session.unit*m for m in star_mult]],
                     index=['Bet Amt'],columns=list(range(1,13)))
st.write("### Star 2.0 Progression")
st.dataframe(star_df,use_container_width=True)

# Friend dashboard
df=session.get_state_df()
st.write("### Friend Dashboard")
st.dataframe(df,use_container_width=True)

# Meta-EV Bet History
if session.meta_history:
    st.write("### Meta-EV Bet History")
    st.dataframe(pd.DataFrame(session.meta_history), use_container_width=True)

# Detailed history
if session.history:
    st.write("### Detailed Hand History")
    hist_df=pd.DataFrame(
        {f.name: f.history for f in session.friends},
        index=[f"Hand {i+1}" for i in range(len(session.history))]
    )
    st.dataframe(hist_df, use_container_width=True)

# Session Summary
st.write("### Session Summary")
st.write(
    f"Hands: {len(session.history)}  "
    f"Meta-EV P/L: ${session.total_meta_pl:.2f}  "
    f"Target(+20×unit): {20*session.unit}  "
    f"Stop(–60×unit): {60*session.unit}"
)

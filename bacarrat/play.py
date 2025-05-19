# Revised Bakura Streamlit MVP (4 Friends, Full 12-Step Star 2.0)
import streamlit as st
from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go

# --- Data Models ---
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

    def next_bet_choice(self) -> str:
        if self.pattern_type == 'banker_only': return 'B'
        if self.pattern_type == 'player_only': return 'P'
        if self.pattern_type == 'alternator_start_banker': return ['B','P'][self.miss_count % 2]
        if self.pattern_type == 'alternator_start_player': return ['P','B'][self.miss_count % 2]
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        sequence = [unit, unit*1.5, unit*2.5, unit*4, unit*6.5, unit*10.5, unit*17, unit*27.5, unit*44.5, unit*72, unit*116, unit*188]
        index = min(self.step, len(sequence)-1)
        return sequence[index]

    def record_hand(self, outcome: str):
        predicted = self.next_bet_choice()
        hit = (outcome == predicted)
        self.last_hit = hit
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak >= 2:
                self.miss_count = 0
                self.step = 0
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

# --- Session Model ---
class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset_patterns()

    def reset_patterns(self):
        patterns = ['banker_only','player_only','alternator_start_banker','alternator_start_player']
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(4)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome)

    def get_state_df(self) -> pd.DataFrame:
        records=[]
        for f in self.friends:
            records.append({
                'Name': f.name,
                'Pattern': f.pattern_type,
                'Last Bet Result': 'Win' if f.last_hit else 'Loss',
                'Miss Count': f.miss_count,
                'Next Bet': f.next_bet_choice(),
                'Next Bet Amount': f.next_bet_amount(self.unit),
                'Total Hits': f.total_hits,
                'Total Misses': f.total_misses
            })
        return pd.DataFrame(records)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session']=Session()
session=st.session_state['session']

# Sidebar
with st.sidebar:
    st.title('Bakura 4-Friend MVP')
    session.unit = st.number_input('Unit Size',1.0,100.0,value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

# Hand Input Buttons (must be above table to affect state before rendering)
col1,col2,col3=st.columns(3)
with col1:
    if st.button('Record Banker'):
        session.add_hand('B')
with col2:
    if st.button('Record Player'):
        session.add_hand('P')
with col3:
    if st.button('Record Tie'):
        session.add_hand('T')

# Main Display
st.write('### Next Bets & Hit/Miss per Friend')
df=session.get_state_df()
# Highlighting colors for Miss Count==5
cell_colors=[]
for _,row in df.iterrows():
    row_colors=[('lightgreen' if row['Miss Count']==5 else 'white') for _ in df.columns]
    cell_colors.append(row_colors)
col_colors=list(map(list,zip(*cell_colors)))
fig=go.Figure(data=[go.Table(header=dict(values=list(df.columns),fill_color='lightgrey'),cells=dict(values=[df[c] for c in df.columns],fill_color=col_colors))])
st.plotly_chart(fig,use_container_width=True)

# History & Summary
st.write('### Hand History')
st.write(' '.join(session.history))
st.write('### Total Needed for 12-Step Limit')
total=df['Next Bet Amount'].sum() if 'Next Bet Amount' in df.columns else 0
st.write(total)

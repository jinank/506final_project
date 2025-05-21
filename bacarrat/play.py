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
        # Sequence patterns
        if pattern_type == 'alternator_start_banker':
            self.sequence = ['B', 'P']
            self.seq_index = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P', 'B']
            self.seq_index = 0
        elif pattern_type == 'terrific_twos':
            # sequence set after first non-tie outcome
            self.sequence = None
            self.seq_index = 0
            self.free_outcome = None
        else:
            self.sequence = None
            self.seq_index = None

    def next_bet_choice(self) -> str:
        # Terrific Twos: free hand until first non-tie, then fixed 8-step pattern
        if self.pattern_type == 'terrific_twos':
            if self.free_outcome is None:
                return ''  # free hand, no bet
            return self.sequence[self.seq_index]
        # Alternator or fixed patterns
        if self.sequence is not None:
            return self.sequence[self.seq_index]
        return 'B' if self.pattern_type == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        # Double-on-first-win if flagged
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        # Standard Star 2.0 multipliers (12-step)
        multipliers = [1, 1.5, 2.5, 2.5, 5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30]
        sequence = [unit * m for m in multipliers]
        idx = min(self.step, len(sequence) - 1)
        return sequence[idx]

    def record_hand(self, outcome: str, unit: float):
        # Terrific Twos initialization on first non-tie
        if self.pattern_type == 'terrific_twos':
            if self.free_outcome is None and outcome in ['B', 'P']:
                self.free_outcome = outcome
                if outcome == 'B':
                    self.sequence = ['B','P','P','B','B','P','P','B']
                else:
                    self.sequence = ['P','P','B','B','P','P','B','B']
                self.seq_index = 0
                return
        # Determine last bet amount before outcome
        self.last_bet_amount = self.next_bet_amount(unit)
        predicted = self.next_bet_choice()
        # Skip progression on free hand
        if predicted == '':
            return
        hit = (outcome == predicted)
        self.last_hit = hit
        # Star 2.0 progression logic
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            # Double next after first win if not base unit
            if self.win_streak == 1 and self.last_bet_amount != unit:
                self.double_next = True
            # Reset after two consecutive wins
            if self.win_streak >= 2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            max_step = len([1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]) - 1
            self.step = min(self.miss_count, max_step)
        # Advance sequence index if using sequence patterns
        if self.sequence is not None:
            self.seq_index = (self.seq_index + 1) % len(self.sequence)

    def _reset_progression(self):
        """Reset Star 2.0 progression counters."""
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
        patterns = [
            'banker_only',
            'player_only',
            'alternator_start_banker',
            'alternator_start_player',
            'terrific_twos'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(len(patterns))]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome, self.unit)

    def get_state_df(self) -> pd.DataFrame:
        records = []
        for f in self.friends:
            records.append({
                'Name': f.name,
                'Pattern': f.pattern_type,
                'Last Bet': 'Win' if f.last_hit else 'Loss',
                'Miss Count': f.miss_count,
                'Next Bet': f.next_bet_choice(),
                'Next Amount': f.next_bet_amount(self.unit),
                'Total Hits': f.total_hits,
                'Total Misses': f.total_misses
            })
        return pd.DataFrame(records)

# --- Streamlit App ---
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']

# Sidebar controls
with st.sidebar:
    st.title('Bakura 5-Friend MVP')
    session.unit = st.number_input('Unit Size', min_value=1.0, step=0.5, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

# Hand input buttons
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

# Star 2.0 Sequence Layout
star_steps = [1, 1.5, 2.5, 2.5, 5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30]
df_star = pd.DataFrame([[session.unit * m for m in star_steps]], index=['Bet Amount'], columns=list(range(1, 13)))
st.write('### Star 2.0 Sequence')
st.dataframe(df_star, use_container_width=True)

# Friend Dashboard with Next Bet highlight
st.write('### Friend Dashboard')
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc['History'] = [' '.join(session.history)] * len(t_df.columns)
header = ['Metric'] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[col].tolist() for col in t_df.columns]
num_rows = len(values[0])
cell_colors = []
cell_colors.append(['white'] * num_rows)
for col in t_df.columns:
    miss = t_df.at['Miss Count', col]
    col_colors = []
    for metric in t_df.index:
        if metric in ['Next Bet', 'Next Amount'] and miss >= 5:
            col_colors.append('lightgreen')
        else:
            col_colors.append('white')
    cell_colors.append(col_colors)
fig = go.Figure(data=[
    go.Table(
        header=dict(values=header, fill_color='darkblue', font=dict(color='white', size=14), align='center'),
        cells=dict(values=values, fill_color=cell_colors, font=dict(color='black', size=12), align='center', height=30)
    )
])
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# Summary
total = df_star.iloc[0].sum()
st.write('### Total Needed for Star Progression')
st.write(total)

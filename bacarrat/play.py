import streamlit as st
from typing import List, Dict

# --- Data Models ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type
        self.miss_count = 0
        self.step = 0
        self.last_two: List[str] = []

    def record_hand(self, outcome: str):
        # track last two outcomes
        self.last_two.append(outcome)
        if len(self.last_two) > 2:
            self.last_two.pop(0)
        # update pattern misses and step for Star 2.0
        if len(self.last_two) == 2 and self.last_two[0] == self.last_two[1]:
            self.miss_count = 0
            self.step = 0
        else:
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

    def next_bet_amount(self, unit: float) -> float:
        # Star 2.0 betting sequence base units
        star_sequence = [unit, unit*1.5, unit*2.5, unit*4, unit*6.5,
                         unit*10.5, unit*17, unit*27.5, unit*44.5,
                         unit*72, unit*116, unit*188]
        return star_sequence[self.step]

    def next_bet_choice(self) -> str:
        # map pattern_type to bet choice
        choices = {
            'banker_only': 'B',
            'player_only': 'P',
            'alternator_start_banker': ['B','P'],
            # ... fill other patterns ...
        }
        pattern = choices.get(self.pattern_type)
        if isinstance(pattern, list):
            return pattern[self.miss_count % len(pattern)]
        return pattern or 'B'


class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.friends: List[FriendPattern] = []
        self.strategy = 'conservative'
        self.reset_patterns()

    def reset_patterns(self):
        types = [
            'banker_only', 'player_only', 'alternator_start_banker',
            'alternator_start_player', 'terrific_twos', 'chop',
            'follow_last', 'three_pattern', 'one_two_one', 'two_three_two'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', types[i]) for i in range(10)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome)

    def get_state(self) -> List[Dict]:
        state = []
        for friend in self.friends:
            state.append({
                'name': friend.name,
                'pattern': friend.pattern_type,
                'misses': friend.miss_count,
                'next_bet': friend.next_bet_choice(),
                'bet_amount': friend.next_bet_amount(self.unit),
                'hit': friend.step == 0
            })
        return state

# --- Streamlit App ---
st.set_page_config(layout='wide')
session = st.session_state.get('game')
if session is None:
    session = Session()
    st.session_state['game'] = session

# Sidebar controls
with st.sidebar:
    st.title('Bakura Algorithm MVP')
    session.unit = st.number_input('Unit Size', min_value=1.0, step=1.0, value=session.unit)
    session.strategy = st.selectbox('Strategy', ['conservative', 'aggressive', 'end_of_shoe'])
    if st.button('New Shoe'):
        session.reset_patterns()

# Main layout
grid_data = session.get_state()
st.write('### Next Bets & Miss Counts')
st.table(grid_data)

# Hand input buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button('Record Banker'):
        session.add_hand('B')
with col2:
    if st.button('Record Player'):
        session.add_hand('P')
with col3:
    if st.button('Record Tie'):
        session.add_hand('T')

# Session history
st.write('### Hand History')
st.write(' '.join(session.history))

# Profit/Loss and summary
st.write('### Summary')
state = session.get_state()
total_bet = sum(item['bet_amount'] for item in state)
st.write(f'Total needed for 12 steps: {total_bet}')

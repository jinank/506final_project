import streamlit as st
from typing import List, Dict

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

    def next_bet_choice(self) -> str:
        # Determine bet based on pattern and current step/miss
        choices = {
            'banker_only': 'B',
            'player_only': 'P',
            'alternator_start_banker': ['B', 'P'],
            'alternator_start_player': ['P', 'B'],
            'terrific_twos': ['B', 'P', 'P'],
            'chop': ['P', 'B'],
        }
        if self.pattern_type == 'follow_last':
            # follow last actual outcome if available
            if hasattr(self, 'history_last'):
                return self.history_last
            return 'B'
        choice = choices.get(self.pattern_type)
        if isinstance(choice, list):
            return choice[self.miss_count % len(choice)]
        return choice or 'B'

    def next_bet_amount(self, unit: float) -> float:
        # Star 2.0 betting sequence base units
        star_sequence = [
            unit, unit * 1.5, unit * 2.5, unit * 4, unit * 6.5,
            unit * 10.5, unit * 17, unit * 27.5, unit * 44.5,
            unit * 72, unit * 116, unit * 188
        ]
        return star_sequence[self.step]

    def record_hand(self, outcome: str):
        # Record predicted vs actual to track individual hits/misses
        predicted = self.next_bet_choice()
        self.last_hit = (outcome == predicted)
        if self.last_hit:
            self.total_hits += 1
        else:
            self.total_misses += 1

        # Star 2.0 logic: reset on two consecutive wins
        if self.last_hit:
            self.win_streak += 1
        else:
            self.win_streak = 0

        if self.win_streak >= 2:
            # back-to-back win: reset misses and step
            self.miss_count = 0
            self.step = 0
        else:
            # increment miss count and advance step
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

        # Store last outcome for follow_last pattern
        self.history_last = outcome


class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
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
        # Return current state for each friend including individual stats
        state = []
        for friend in self.friends:
            state.append({
                'Name': friend.name,
                'Pattern': friend.pattern_type,
                'Last Hit': '✔️' if friend.last_hit else '❌',
                'Miss Count': friend.miss_count,
                'Next Bet': friend.next_bet_choice(),
                'Bet Amount': friend.next_bet_amount(self.unit),
                'Total Hits': friend.total_hits,
                'Total Misses': friend.total_misses
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
st.write('### Next Bets & Hit/Miss Counts')
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

# Summary
st.write('### Summary')
state = session.get_state()
# Calculate total amount needed safely
try:
    total_bet = sum(item.get('Bet Amount', 0) for item in state)
except Exception as e:
    total_bet = 0
    st.error(f"Error calculating total bet: {e}")
st.write(f'Total needed for 12 steps: {total_bet}')

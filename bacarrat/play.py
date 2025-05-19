import streamlit as st
from typing import List, Dict

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
        # Map each pattern to its repeating bet sequence
        if self.pattern_type == 'banker_only':
            return 'B'
        if self.pattern_type == 'player_only':
            return 'P'
        if self.pattern_type == 'alternator_start_banker':
            return ['B', 'P'][self.miss_count % 2]
        if self.pattern_type == 'alternator_start_player':
            return ['P', 'B'][self.miss_count % 2]
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        # Star 2.0 betting sequence
        seq = [unit, unit*1.5, unit*2.5, unit*4]
        # after 4 losses, keep last amount
        return seq[self.step] if self.step < len(seq) else seq[-1]

    def record_hand(self, outcome: str):
        predicted = self.next_bet_choice()
        hit = (outcome == predicted)
        self.last_hit = hit
        if hit:
            self.total_hits += 1
            self.win_streak += 1
        else:
            self.total_misses += 1
            self.win_streak = 0

        # reset after 2 consecutive wins
        if self.win_streak >= 2:
            self.miss_count = 0
            self.step = 0
        else:
            self.miss_count += 1
            self.step = min(self.miss_count, len([unit, unit*1.5, unit*2.5, unit*4]) - 1)


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
            'alternator_start_player'
        ]
        self.friends = [FriendPattern(f'Friend {i+1}', patterns[i]) for i in range(4)]
        self.history = []

    def add_hand(self, outcome: str):
        self.history.append(outcome)
        for friend in self.friends:
            friend.record_hand(outcome)

    def get_state(self) -> List[Dict]:
        return [
            {
                'Name': f.name,
                'Pattern': f.pattern_type,
                'Last Hit': '✔️' if f.last_hit else '❌',
                'Miss Count': f.miss_count,
                'Next Bet': f.next_bet_choice(),
                'Bet Amount': f.next_bet_amount(self.unit),
                'Total Hits': f.total_hits,
                'Total Misses': f.total_misses
            }
            for f in self.friends
        ]

# --- Streamlit App ---
st.set_page_config(layout='wide')
session = st.session_state.get('game')
if session is None:
    session = Session()
    st.session_state['game'] = session

with st.sidebar:
    st.title('Bakura Algorithm MVP')
    session.unit = st.number_input('Unit Size', 1.0, 100.0, value=session.unit)
    if st.button('New Shoe'):
        session.reset_patterns()

st.write('### Next Bets & Hit/Miss Counts')
st.table(session.get_state())

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

st.write('### Hand History')
st.write(' '.join(session.history))

# Summary
total_needed = sum(item['Bet Amount'] for item in session.get_state())
st.write(f'Total needed for 4-step limit: {total_needed}')

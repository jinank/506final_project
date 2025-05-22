# play.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Friend Logic ---
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
        self.last_bet_amount = 0
        self.first_bet = True
        self.history: List[str] = []
        # Pattern state
        if pattern_type == 'banker_only':
            self.sequence = None
        elif pattern_type == 'player_only':
            self.sequence = None
        elif pattern_type == 'alternator_start_banker':
            self.sequence = ['B', 'P']
            self.idx = 0
        elif pattern_type == 'alternator_start_player':
            self.sequence = ['P', 'B']
            self.idx = 0
        elif pattern_type == 'terrific_twos':
            self.sequence = None
            self.idx = 0
            self.free_outcome = None
        elif pattern_type == 'chop':
            self.sequence = None
            self.last_outcome = None
        elif pattern_type == 'follow_last':
            self.sequence = None
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
            self.sequence = None

    def next_bet_choice(self) -> str:
        p = self.pattern_type
        if p == 'chop':
            return '' if self.last_outcome is None else ('B' if self.last_outcome == 'P' else 'P')
        if p == 'terrific_twos' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'three_pattern' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'one_two_one' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'two_three_two_pattern' and self.free_outcome:
            return self.sequence[self.idx]
        if p == 'follow_last' and self.last_outcome:
            return self.last_outcome
        if self.sequence is not None:
            return self.sequence[self.idx]
        return 'B' if p == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2
        mults = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
        return unit * mults[min(self.step, len(mults)-1)]

    def record_hand(self, outcome: str, unit: float):
        p = self.pattern_type
        # Initialize sequences
        if p=='terrific_twos' and self.free_outcome is None and outcome in ('B','P'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base, base, alt, alt, base, base, alt, alt, base, base]
            self.idx = 0
            self.history.append('')
            return
        if p=='three_pattern' and self.free_outcome is None and outcome in ('B','P'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            # Correct 3-pattern: 2 base,3 alt,3 base,3 alt
            self.sequence = [base]*2 + [alt]*3 + [base]*3 + [alt]*3
            self.idx = 0
            self.history.append('')
            return
        if p=='one_two_one' and self.free_outcome is None and outcome in ('B','P'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base] + [alt]*2 + [base] + [alt]*2 + [base] + [alt]*2
            self.idx = 0
            self.history.append('')
            return
        if p=='two_three_two_pattern' and self.free_outcome is None and outcome in ('B','P'):
            self.free_outcome = outcome
            base, alt = outcome, ('P' if outcome=='B' else 'B')
            self.sequence = [base] + [alt]*3 + [base]*2 + [alt]*3 + [base]*2
            self.idx = 0
            self.history.append('')
            return
        if p=='chop' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome = outcome
            self.history.append('')
            return
        if p=='follow_last' and self.last_outcome is None and outcome in ('B','P'):
            self.last_outcome = outcome
            self.history.append('')
            return

        pred = self.next_bet_choice()
        if pred=='':
            if self.sequence is not None:
                self.idx = (self.idx + 1) % len(self.sequence)
            self.history.append('')
            return

        amt = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit
        if self.first_bet:
            self.first_bet = False
            status = 'W' if hit else 'M'
            self.history.append(status)
            if hit: self.total_hits += 1
            else: self.total_misses += 1
            if self.sequence is not None:
                self.idx = (self.idx+1) % len(self.sequence)
            if p in ('chop','follow_last'):
                self.last_outcome = outcome
            return
        status = 'W' if hit else 'M'
        self.history.append(status)
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak==1 and amt!=unit: self.double_next=True
            if self.win_streak>=2: self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)
        if self.sequence is not None:
            self.idx = (self.idx+1) % len(self.sequence)
        if p in ('chop','follow_last'):
            self.last_outcome = outcome

    def _reset_progression(self):
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0
        self.double_next = False

# Session & UI omitted for brevity; rest remains as before

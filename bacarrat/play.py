# Bakura 4-Friend MVP with Star 2.0 Grid Layout
import streamlit as st
from typing import List
import pandas as pd
import plotly.graph_objects as go

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
        # Alternator pattern sequence and index
        if pattern_type == 'alternator_start_banker':
            self.alternator_sequence = ['B', 'P']
        elif pattern_type == 'alternator_start_player':
            self.alternator_sequence = ['P', 'B']
        else:
            self.alternator_sequence = None
        self.alternator_index = 0

    def next_bet_choice(self) -> str:
        # Alternator patterns use fixed sequence regardless of hit/miss
        if self.alternator_sequence:
            return self.alternator_sequence[self.alternator_index]
        # Fixed patterns
        if self.pattern_type == 'banker_only':
            return 'B'
        if self.pattern_type == 'player_only':
            return 'P'
        return 'B'

    def next_bet_amount(self, unit: float) -> float:
        multipliers = [1, 1.5, 2.5, 2.5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30]
        sequence = [unit * m for m in multipliers]
        idx = min(self.step, len(sequence) - 1)
        return sequence[idx]

        def record_hand(self, outcome: str):
        # Predict and record hit/miss for alternator patterns first
            if self.alternator_sequence:
                predicted = self.next_bet_choice()
                hit = (outcome == predicted)
                self.last_hit = hit
                if hit:
                    self.total_hits += 1
                    self.win_streak += 1
                else:
                    self.total_misses += 1
                    self.win_streak = 0
                # Advance alternator index regardless of hit/miss
                self.alternator_index = (self.alternator_index + 1) % len(self.alternator_sequence)
                # Only reset Star progression after two consecutive hits
                if self.win_streak >= 2:
                    self._reset_progression()
        return

        # Standard Star 2.0 progression for non-alternator patterns
        predicted = self.next_bet_choice()
        hit = (outcome == predicted)
        self.last_hit = hit
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak >= 2:
                self._reset_progression()
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

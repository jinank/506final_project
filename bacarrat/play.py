import streamlit as st
import pandas as pd

# Reset session state
if st.sidebar.button("🔄 Reset Session"):
    st.session_state.history = []
    st.session_state.friends = {
        "Friend 1": {'pattern': 'banker', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 2": {'pattern': 'player', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 3": {'pattern': 'alternate', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 4": {'pattern': 'alt_start_p', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 5": {'pattern': 'twos', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 6": {'pattern': 'chop', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 7": {'pattern': 'follow', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 8": {'pattern': 'three_pattern', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 9": {'pattern': 'one_two_one', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 10": {'pattern': 'two_three_two', 'misses': 0, 'last_result': '', 'win_streak': 0},
    }
    st.session_state.balance = 1000
    st.session_state.initial_balance = 1000
    st.session_state.stop_loss = 800
    st.session_state.win_goal = 1200
    st.rerun()

# Initialize session variables if not already set
if 'history' not in st.session_state:
    st.session_state.history = []
if 'friends' not in st.session_state:
    st.session_state.friends = {
        f"Friend {i+1}": {'pattern': 'banker' if i == 0 else 'player' if i == 1 else 'alternate' if i == 2 else 'alt_start_p' if i == 3 else 'twos' if i == 4 else 'chop' if i == 5 else 'follow' if i == 6 else 'three_pattern' if i == 7 else 'one_two_one' if i == 8 else 'two_three_two',
                           'misses': 0, 'last_result': '', 'win_streak': 0}
        for i in range(10)
    }
if 'balance' not in st.session_state:
    st.session_state.balance = 1000
if 'initial_balance' not in st.session_state:
    st.session_state.initial_balance = 1000
if 'stop_loss' not in st.session_state:
    st.session_state.stop_loss = 800
if 'win_goal' not in st.session_state:
    st.session_state.win_goal = 1200

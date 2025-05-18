import streamlit as st
import pandas as pd

# Session Settings Sidebar
st.sidebar.header("Session Settings")
st.session_state.initial_balance = st.sidebar.number_input("Initial Balance", value=st.session_state.initial_balance if 'initial_balance' in st.session_state else 1000)
st.session_state.balance = st.sidebar.number_input("Current Balance", value=st.session_state.balance if 'balance' in st.session_state else 1000)
st.session_state.stop_loss = st.sidebar.number_input("Stop Loss Threshold", value=st.session_state.stop_loss if 'stop_loss' in st.session_state else 800)
st.session_state.win_goal = st.sidebar.number_input("Win Goal Threshold", value=st.session_state.win_goal if 'win_goal' in st.session_state else 1200)

# Initialize session variables
if 'history' not in st.session_state:
    st.session_state.history = []
if 'friends' not in st.session_state:
    st.session_state.friends = {
        "Friend 1": {'pattern': 'banker', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 2": {'pattern': 'player', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 3": {'pattern': 'bp_alternate', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 4": {'pattern': 'pb_alternate', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 5": {'pattern': 'twos', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 6": {'pattern': 'chop', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 7": {'pattern': 'follow', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 8": {'pattern': 'three_pattern', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 9": {'pattern': 'one_two_one', 'misses': 0, 'last_result': '', 'win_streak': 0},
        "Friend 10": {'pattern': 'two_three_two', 'misses': 0, 'last_result': '', 'win_streak': 0},
    }

# Betting strategy function
preview_length = 5

def get_expected_bet(friend_name, history):
    pattern = st.session_state.friends[friend_name]['pattern']
    if not history:
        if pattern == 'bp_alternate':
            return 'B'
        elif pattern == 'pb_alternate':
            return 'P'
        elif pattern == 'alternate':
            return 'B'
        return None
    last = history[-1]
    if pattern == 'banker':
        return 'B'
    elif pattern == 'player':
        return 'P'
    elif pattern == 'alternate':
        return 'B' if len(history) % 2 == 0 else 'P'
    elif pattern == 'alt_start_p':
        return 'P' if len(history) % 2 == 0 else 'B'
    elif pattern == 'bp_alternate':
        seq = ['B', 'P']
        return seq[len(history) % 2]
    elif pattern == 'pb_alternate':
        seq = ['P', 'B']
        return seq[len(history) % 2]

def get_preview(friend_name, history):
    preview = []
    for _ in range(preview_length):
        temp_history = history + preview
        preview.append(get_expected_bet(friend_name, temp_history))
    return ''.join([p for p in preview if p is not None])

friend_data = []
for name, stats in st.session_state.friends.items():
    expected = get_expected_bet(name, st.session_state.history)
    misses = stats['misses']
    preview = get_preview(name, st.session_state.history)
    amount = [10, 15, 25, 25, 50, 50, 75, 100, 125, 175]
    next_amount = amount[misses] if misses < len(amount) else amount[-1]
    friend_data.append({
        'Friend': name,
        'Pattern': stats['pattern'],
        'Expected Bet': expected,
        'Misses': misses,
        'Next Bet Amount ($)': next_amount,
        'Preview (Next 5)': preview
    })

# Per-friend reset buttons and streak chart
st.subheader("Friend Actions")
for friend in st.session_state.friends:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**{friend}** — Pattern: {st.session_state.friends[friend]['pattern']}, Misses: {st.session_state.friends[friend]['misses']}")
    with col2:
        if st.button(f"Reset {friend}"):
            st.session_state.friends[friend]['misses'] = 0
            st.session_state.friends[friend]['last_result'] = ''
            st.session_state.friends[friend]['win_streak'] = 0

import matplotlib.pyplot as plt
st.subheader("Miss Streaks Chart")
plt.figure(figsize=(10, 4))
plt.bar([f"F{i+1}" for i in range(10)], [st.session_state.friends[f"Friend {i+1}"]['misses'] for i in range(10)])
plt.title("Current Miss Streaks by Friend")
plt.xlabel("Friend")
plt.ylabel("Misses")
st.pyplot(plt)

friend_df = pd.DataFrame(friend_data)
st.dataframe(friend_df.style.apply(lambda row: ['background-color: lightgreen' if row['Misses'] >= 5 else '' for _ in row], axis=1))

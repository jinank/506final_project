import streamlit as st
import pandas as pd

# 🔁 RESET SESSION
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

# 🧠 INIT
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

# 🎯 STRATEGY
def get_expected_bet(friend_name, history):
    pattern = st.session_state.friends[friend_name]['pattern']
    if not history:
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
    elif pattern == 'chop':
        return 'P' if last == 'B' else 'B'
    elif pattern == 'follow':
        return last
    elif pattern == 'twos':
        seq = ['B', 'P', 'P', 'B', 'B', 'P', 'P', 'B', 'B']
        return seq[len(history) % len(seq)]
    elif pattern == 'three_pattern':
        seq = ['B', 'B', 'P', 'P', 'P', 'B', 'B', 'B', 'P', 'P', 'P']
        return seq[len(history) % len(seq)]
    elif pattern == 'one_two_one':
        seq = ['P', 'P', 'B', 'P', 'P', 'B', 'P', 'P', 'B']
        return seq[len(history) % len(seq)]
    elif pattern == 'two_three_two':
        seq = ['P', 'B', 'B', 'B', 'P', 'P', 'B', 'B', 'B', 'P', 'P']
        return seq[len(history) % len(seq)]
    return 'B'

# 🔢 Betting Progression
progression = [10, 15, 25, 25, 50, 50, 75, 100, 125, 175]

# 🖼️ HEADER
st.title("🎲 AI Baccarat Friend Tracker")

# ⚙️ Session Settings
st.sidebar.header("Session Settings")
st.session_state.initial_balance = st.sidebar.number_input("Initial Balance", value=st.session_state.initial_balance)
st.session_state.balance = st.sidebar.number_input("Current Balance", value=st.session_state.balance)
st.session_state.stop_loss = st.sidebar.number_input("Stop Loss Threshold", value=st.session_state.stop_loss)
st.session_state.win_goal = st.sidebar.number_input("Win Goal Threshold", value=st.session_state.win_goal)

# 🎮 Game Result Input
result = st.radio("Enter result of hand:", ["Player (P)", "Banker (B)", "Skip"])
if st.button("Submit Result"):
    if result != "Skip":
        current = 'P' if result.startswith('P') else 'B'
        st.session_state.history.append(current)
        for friend in st.session_state.friends:
            expected = get_expected_bet(friend, st.session_state.history[:-1])
            if expected == current:
                st.session_state.friends[friend]['misses'] = 0
            else:
                st.session_state.friends[friend]['misses'] += 1

# 📊 Friend Miss Tracker
st.subheader("Friend Miss Tracker")
friend_data = []
for name, stats in st.session_state.friends.items():
    expected = get_expected_bet(name, st.session_state.history)
    misses = stats['misses']
    amount = progression[misses] if misses < len(progression) else progression[-1]
    friend_data.append({
        'Friend': name,
        'Expected Bet': expected,
        'Misses': misses,
        'Next Bet Amount ($)': amount
    })
friend_df = pd.DataFrame(friend_data)
st.dataframe(friend_df.style.apply(lambda row: ['background-color: lightgreen' if row['Misses'] >= 5 else '' for _ in row], axis=1))

# 💡 Recommendation
st.subheader("Recommended Bet")
best = max(friend_data, key=lambda x: x['Misses'])
if best['Misses'] >= 4:
    bet_amount = best['Next Bet Amount ($)']
    st.success(f"Bet AGAINST {best['Friend']} — they expect {best['Expected Bet']}, have {best['Misses']} misses, bet amount: ${bet_amount}")
    if st.button("Apply Win"):
        st.session_state.balance += bet_amount
    if st.button("Apply Loss"):
        st.session_state.balance -= bet_amount
else:
    st.info("No friend has 4 or more misses. Wait for more hands.")

# 💰 Session Summary
st.subheader("Session Status")
st.metric("Current Balance", f"${st.session_state.balance:.2f}")
st.metric("Stop Loss Target", f"${st.session_state.stop_loss:.2f}")
st.metric("Win Goal Target", f"${st.session_state.win_goal:.2f}")

if st.session_state.balance <= st.session_state.stop_loss:
    st.error("❌ STOP LOSS hit! End session.")
elif st.session_state.balance >= st.session_state.win_goal:
    st.success("🎉 WIN GOAL reached! Well done.")

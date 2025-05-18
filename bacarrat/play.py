import streamlit as st
import pandas as pd

# Initialize session variables if not already set
if 'history' not in st.session_state:
    st.session_state.history = []  # Track past outcomes: 'P' or 'B'
if 'friends' not in st.session_state:
    st.session_state.friends = {
        f"Friend {i+1}": {'pattern': 'banker' if i == 0 else 'player' if i == 1 else 'alternate' if i == 2 else 'alt_start_p' if i == 3 else 'chop',
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

# Betting logic per strategy
def get_expected_bet(friend_name, history):
    pattern = st.session_state.friends[friend_name]['pattern']
    if pattern == 'banker':
        return 'B'
    elif pattern == 'player':
        return 'P'
    elif pattern == 'alternate':
        return 'B' if len(history) % 2 == 0 else 'P'
    elif pattern == 'alt_start_p':
        return 'P' if len(history) % 2 == 0 else 'B'
    elif pattern == 'chop':
        return 'P' if history and history[-1] == 'B' else 'B'
    return 'B'

# Betting progression
progression = [10, 15, 25, 25, 50, 50, 75, 100, 125, 175]

# Input form
st.title("AI Baccarat Friend Tracker")

st.sidebar.header("Session Settings")
st.session_state.initial_balance = st.sidebar.number_input("Initial Balance", value=st.session_state.initial_balance)
st.session_state.balance = st.sidebar.number_input("Current Balance", value=st.session_state.balance)
st.session_state.stop_loss = st.sidebar.number_input("Stop Loss Threshold", value=st.session_state.stop_loss)
st.session_state.win_goal = st.sidebar.number_input("Win Goal Threshold", value=st.session_state.win_goal)

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

# Display current friend states
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

# Highlight rows with 5 or more misses in green
st.dataframe(friend_df.style.apply(lambda row: ['background-color: lightgreen' if row['Misses'] >= 5 else '' for _ in row], axis=1))

# Suggest friend to bet against
st.subheader("Recommended Bet")
best = max(friend_data, key=lambda x: x['Misses'])
if best['Misses'] >= 4:
    bet_amount = best['Next Bet Amount ($)']
    st.success(f"Suggest betting AGAINST {best['Friend']} who is expected to bet on {best['Expected Bet']}, has {best['Misses']} misses, and the bet amount is ${bet_amount}")

    if st.button("Apply Win"):
        st.session_state.balance += bet_amount
    if st.button("Apply Loss"):
        st.session_state.balance -= bet_amount
else:
    st.info("No friend has 4 or more misses. Consider taking a free hand.")

# Session status
st.subheader("Session Status")
st.metric("Current Balance", f"${st.session_state.balance:.2f}")
st.metric("Stop Loss Target", f"${st.session_state.stop_loss:.2f}")
st.metric("Win Goal Target", f"${st.session_state.win_goal:.2f}")

if st.session_state.balance <= st.session_state.stop_loss:
    st.error("STOP LOSS hit! End the session.")
elif st.session_state.balance >= st.session_state.win_goal:
    st.success("WIN GOAL reached! Congratulations.")

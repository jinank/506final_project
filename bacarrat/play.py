import streamlit as st
import pandas as pd

# Initialize session variables if not already set
if 'history' not in st.session_state:
    st.session_state.history = []  # Track past outcomes: 'P' or 'B'
    st.session_state.friends = {
        f"Friend {i+1}": {'pattern': 'banker' if i == 0 else 'player' if i == 1 else 'alternate' if i == 2 else 'alt_start_p' if i == 3 else 'chop',
                           'misses': 0, 'last_result': '', 'win_streak': 0}
        for i in range(10)
    }

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

# Input form
st.title("AI Baccarat Friend Tracker")

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
    friend_data.append({
        'Friend': name,
        'Expected Bet': expected,
        'Misses': stats['misses']
    })
friend_df = pd.DataFrame(friend_data)
st.dataframe(friend_df)

# Suggest friend to bet against
st.subheader("Recommended Bet")
best = max(friend_data, key=lambda x: x['Misses'])
if best['Misses'] >= 4:
    st.success(f"Suggest betting AGAINST {best['Friend']} who is expected to bet on {best['Expected Bet']} and has {best['Misses']} misses.")
else:
    st.info("No friend has 4 or more misses. Consider taking a free hand.")

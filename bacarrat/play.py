import streamlit as st
import pandas as pd

# Initialize session state variables
if "starting_balance" not in st.session_state:
    st.session_state.starting_balance = 10000
    st.session_state.current_balance = 10000
    st.session_state.unit_size = 25
    st.session_state.range_start = 5
    st.session_state.range_end = 10
    st.session_state.stop_loss = 600
    st.session_state.win_goal = 600
    st.session_state.friend_data = [{"id": i+1, "misses": 0, "next_bet": 0, "checked": False} for i in range(10)]

# Title
st.title("I Am The Casino - Baccarat Tracker (MVP)")

# Sidebar: Session Settings
with st.sidebar:
    st.header("Session Settings")
    st.session_state.starting_balance = st.number_input("Starting Balance", value=st.session_state.starting_balance)
    st.session_state.unit_size = st.number_input("Unit Size ($)", value=st.session_state.unit_size)
    st.session_state.range_start = st.number_input("Range Start", value=st.session_state.range_start)
    st.session_state.range_end = st.number_input("Range End", value=st.session_state.range_end)

    # Calculate stop-loss
    range_bets = [st.session_state.unit_size * mult for mult in [1, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]]
    st.session_state.stop_loss = round(sum(range_bets[st.session_state.range_start - 1:st.session_state.range_end]), 2)
    st.session_state.win_goal = round(st.session_state.stop_loss, 2)

    st.write(f"**Stop-Loss:** ${st.session_state.stop_loss}")
    st.write(f"**Win Goal:** ${st.session_state.win_goal}")

# Main Panel: Friend Tracker
st.subheader("Friend Tracker")
friend_df = pd.DataFrame(st.session_state.friend_data)

for idx, friend in friend_df.iterrows():
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    with col1:
        st.markdown(f"**Friend {friend['id']}**")
    with col2:
        new_miss = st.number_input(f"Misses (F{friend['id']})", value=friend['misses'], key=f"miss_{friend['id']}")
        st.session_state.friend_data[idx]["misses"] = new_miss
    with col3:
        st.session_state.friend_data[idx]["next_bet"] = st.session_state.unit_size * (1 + 0.5 * new_miss)
        st.markdown(f"Next Bet: **${st.session_state.friend_data[idx]['next_bet']:.2f}**")
    with col4:
        st.session_state.friend_data[idx]["checked"] = st.checkbox("Back-to-Back", value=friend["checked"], key=f"check_{friend['id']}")

# Display Balance
st.subheader("Session Tracker")
st.metric("Current Balance", f"${st.session_state.current_balance:.2f}")
st.metric("Stop Loss Target", f"${st.session_state.starting_balance - st.session_state.stop_loss:.2f}")
st.metric("Win Goal Target", f"${st.session_state.starting_balance + st.session_state.win_goal:.2f}")

# Betting Suggestion
st.subheader("Recommended Action")
sorted_friends = sorted(st.session_state.friend_data, key=lambda x: x["misses"], reverse=True)
top_friend = sorted_friends[0]
if top_friend["misses"] >= 4:
    st.success(f"Bet AGAINST Friend {top_friend['id']} (${top_friend['next_bet']:.2f})")
else:
    st.info("No friend has enough misses. Wait for more free hands...")

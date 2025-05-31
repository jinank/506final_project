# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List

# --- Single‐hand win probabilities for Banker/Player (used for “Conservative” odds if desired) ---
WIN_PROB = {'B': 0.4586, 'P': 0.4462}


def prob_two_consec(n: int, p: float) -> float:
    """
    Probability of at least one run of two consecutive successes
    in n Bernoulli trials with success probability p.
    (Two‐state DP: no0 = P(no consec, ending with failure),
                   no1 = P(no consec, ending with single success))
    """
    no0 = 1 - p
    no1 = p
    for _ in range(2, n + 1):
        f0 = (no0 + no1) * (1 - p)   # next outcome = failure
        f1 = no0 * p                 # next outcome = success
        no0, no1 = f0, f1
    return 1 - (no0 + no1)


# --- Friend / pattern model (exactly as before, extended to 11 patterns) ---
class FriendPattern:
    def __init__(self, name: str, pattern_type: str):
        self.name = name
        self.pattern_type = pattern_type

        # Star 2.0 progression state
        self.miss_count = 0
        self.step = 0
        self.win_streak = 0

        # Hit / miss tracking
        self.last_hit = False
        self.total_hits = 0
        self.total_misses = 0

        # “double‐on‐first‐win” flag
        self.double_next = False
        self.last_bet_amount = 0.0

        # Skip counting the very first real bet as a miss
        self.first_bet = True

        # Pattern sequencing
        self.free_outcome = None
        self.sequence = None
        self.idx = 0
        self.last_outcome = None

        # Per‐friend ✔/✘ history
        self.history: List[str] = []

        p = pattern_type
        if p == 'alternator_start_banker':
            self.sequence = ['B', 'P']
        elif p == 'alternator_start_player':
            self.sequence = ['P', 'B']

    def next_bet_choice(self) -> str:
        """
        Returns:
          ''  → if this is still a free hand (no bet yet)
          'B' or 'P' → the prediction for the next hand
        """
        p = self.pattern_type
        # Patterns that wait for a free hand first:
        if p in ('terrific_twos', 'three_pattern', 'one_two_one', 'two_three_two', 'pattern_1313'):
            if self.free_outcome is None:
                return ''  # free hand
            return self.sequence[self.idx]

        if p == 'chop':
            if self.free_outcome is None:
                return ''
            return 'P' if self.free_outcome == 'B' else 'B'

        if p == 'follow_last':
            if self.last_outcome is None:
                return ''
            return self.last_outcome

        # Alternators or fixed banker_only/player_only
        if self.sequence:
            return self.sequence[self.idx]
        return 'B' if p == 'banker_only' else 'P'

    def next_bet_amount(self, unit: float) -> float:
        """
        Computes the amount to stake according to Star 2.0 progression.
        If `double_next` is True, we immediately double last_bet_amount.
        Otherwise, we use the multiplier list [1, 1.5, 2.5, 2.5, 5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30].
        """
        if self.double_next:
            self.double_next = False
            return self.last_bet_amount * 2

        mult = [1, 1.5, 2.5, 2.5, 5, 5, 7.5, 10, 12.5, 17.5, 22.5, 30]
        idx = max(0, min(self.step, len(mult) - 1))
        amt = unit * mult[idx]
        self.last_bet_amount = amt
        return amt

    def record_hand(self, outcome: str, unit: float):
        """
        Update internal state by feeding in the next actual outcome ( 'B','P', or 'T' ).
        - On ties ( 'T' ), no bet is placed—just append an empty history cell.
        - Otherwise, compute `next_bet_choice()`; compare to `outcome` → set hit/miss.
        - Progress the Star 2.0 counters:
            * reset on any two consecutive wins
            * otherwise increase miss_count and step if miss
        - Advance any sequencing index ( idx ).
        - Track per‐friend history (‘✔’ or ‘✘’ or '' if free).
        """
        p = self.pattern_type

        # —– Initialize dynamic sequences on first real (non‐tie) outcome —–
        if p == 'terrific_twos' and self.free_outcome is None and outcome in ('B', 'P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            self.sequence = [base, base, alt, alt, base, base, alt, alt, base, base]
            self.free_outcome, self.idx = base, 0
            self.history.append('')
            return

        if p == 'three_pattern' and self.free_outcome is None and outcome in ('B', 'P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            self.sequence = [base] * 2 + [alt] * 3 + [base] * 3 + [alt] * 3
            self.free_outcome, self.idx = base, 0
            self.history.append('')
            return

        if p == 'one_two_one' and self.free_outcome is None and outcome in ('B', 'P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            self.sequence = [alt, alt, base] * 3
            self.free_outcome, self.idx = base, 0
            self.history.append('')
            return

        if p == 'two_three_two' and self.free_outcome is None and outcome in ('B', 'P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            self.sequence = [base] + [alt] * 3 + [base] * 2 + [alt] * 3 + [base] * 2
            self.free_outcome, self.idx = base, 0
            self.history.append('')
            return

        if p == 'pattern_1313' and self.free_outcome is None and outcome in ('B', 'P'):
            base, alt = outcome, ('P' if outcome == 'B' else 'B')
            self.sequence = [alt, alt, alt, base]
            self.free_outcome, self.idx = base, 0
            self.history.append('')
            return

        if p == 'chop' and self.free_outcome is None and outcome in ('B', 'P'):
            self.free_outcome = outcome
            self.history.append('')
            return

        if p == 'follow_last' and self.last_outcome is None and outcome in ('B', 'P'):
            self.last_outcome = outcome
            self.history.append('')
            return

        # —– Otherwise, we place a bet (non‐tie scenario) —–
        pred = self.next_bet_choice()
        # If pred=='' → still a free hand
        if pred == '':
            if self.sequence:
                self.idx = (self.idx + 1) % len(self.sequence)
            self.history.append('')
            return

        amt = self.next_bet_amount(unit)
        hit = (outcome == pred)
        self.last_hit = hit
        self.history.append('✔' if hit else '✘')

        # Skip counting miss on the very first real bet
        if self.first_bet:
            self.first_bet = False
            if not hit:
                self.miss_count = 1
                self.step = 1
            if hit:
                self.total_hits += 1
                self.win_streak += 1
            else:
                self.total_misses += 1
                self.win_streak = 0
            if self.sequence:
                self.idx = (self.idx + 1) % len(self.sequence)
            if p == 'follow_last' and outcome in ('B', 'P'):
                self.last_outcome = outcome
            return

        # —– Star 2.0 progression & reset logic —–
        if hit:
            self.total_hits += 1
            self.win_streak += 1
            if self.win_streak == 1 and amt != unit:
                self.double_next = True
            if self.win_streak >= 2:
                # Two wins in a row, reset counters
                self.miss_count = 0
                self.step = 0
                self.win_streak = 0
                self.double_next = False
        else:
            self.total_misses += 1
            self.win_streak = 0
            self.miss_count += 1
            self.step = min(self.miss_count, 11)

        # Advance sequence idx if applicable
        if self.sequence:
            self.idx = (self.idx + 1) % len(self.sequence)
        if p == 'follow_last' and outcome in ('B', 'P'):
            self.last_outcome = outcome


# —– Session holds all 11 friends + full hand history —–
class Session:
    def __init__(self):
        self.unit = 10.0
        self.history: List[str] = []
        self.reset()

    def reset(self):
        types = [
            'banker_only','player_only',
            'alternator_start_banker','alternator_start_player',
            'terrific_twos','chop','follow_last','three_pattern',
            'one_two_one','two_three_two','pattern_1313'
        ]
        self.friends = [
            FriendPattern(f'Friend {i+1}', types[i])
            for i in range(len(types))
        ]
        self.history = []

    def add_hand(self, outcome: str):
        """
        Record a new actual outcome ( 'B', 'P', or 'T' ) 
        and update all friends’ internal state.
        """
        self.history.append(outcome)
        for f in self.friends:
            f.record_hand(outcome, self.unit)

    def get_state_df(self) -> pd.DataFrame:
        """
        Return a DataFrame summarizing each friend’s current:
          - Name
          - Pattern
          - Last Bet (Win/Loss)
          - Miss Count
          - Next Bet (B/P or '')
          - Next Amount
          - Hits / Misses total
        """
        rows = []
        for f in self.friends:
            rows.append({
                'Name':        f.name,
                'Pattern':     f.pattern_type,
                'Last Bet':    'Win' if f.last_hit else 'Loss',
                'Miss Count':  f.miss_count,
                'Next Bet':    f.next_bet_choice(),
                'Next Amount': f.next_bet_amount(self.unit),
                'Hits':        f.total_hits,
                'Misses':      f.total_misses
            })
        return pd.DataFrame(rows)


# —– Streamlit App Layout —–
st.set_page_config(layout='wide')
if 'session' not in st.session_state:
    st.session_state['session'] = Session()
session = st.session_state['session']


# Sidebar: Bankroll, Unit size, Target, Stop Loss, “New Shoe”
with st.sidebar:
    st.title("Baccarat.ai – 11‐Friend MVP")
    st.write("**Set Your Session Parameters**")
    bankroll = st.number_input("Bankroll ($)", min_value=0.0, step=10.0, value=1000.0)
    session.unit = st.number_input("Unit Size ($)", min_value=1.0, step=1.0, value=session.unit)
    target = st.number_input("Target Profit ($)", min_value=0.0, step=10.0, value=20.0)
    stoploss = st.number_input("Stop Loss ($)", min_value=0.0, step=10.0, value=60.0)

    if st.button("New Shoe / Reset All"):
        session.reset()

    st.markdown("---")

    # “Conservative Entry” prompts: any friend whose miss_count > 10
    cons = [f for f in session.friends if f.miss_count > 10]
    if cons:
        st.markdown("**Conservative‐Entry Suggestions** (any friend > 10 misses):")
        for f in cons:
            side = f.next_bet_choice() or "N/A"
            p = WIN_PROB.get(side, 0.0)
            pct = prob_two_consec(12, p) * 100 if p else 0.0
            st.markdown(f"- {f.name} → **{side}** @ {session.unit:.0f} u   (2×wins ≈ {pct:.1f}% in next 12)")


# Main area: Hand history input + “Process History” button
st.write("# Baccarat.ai Predictor – Web App")

st.markdown("### 1) Paste or Type the Last Several Outcomes")
st.markdown("‣ Use `B` for Banker, `P` for Player, `T` for Tie.  ")
st.markdown("‣ Example: `B P P B T B P B P P B P …` (spaces optional)  ")
st.markdown("‣ Enter at least 10–20 hands for better suggestions.")

history_input = st.text_area("Enter Hand History:", height=120)

if st.button("▶ Process History"):
    # Clean input: remove spaces, uppercase
    cleaned = "".join(history_input.upper().split())
    # Filter only B, P, T
    cleaned = "".join(ch for ch in cleaned if ch in ("B","P","T"))
    # Feed each character into session:
    session.reset()
    for ch in cleaned:
        session.add_hand(ch)

# Show how many hands recorded so far:
num_hands = len(session.history)
st.write(f"**Hands processed:** {num_hands}")

st.markdown("---")


# Immediately after processing history, compute our “Next‐Bet Suggestion” using 
# the “after 4th miss, at 5th miss, choose majority side & pick largest amount → invert side” rule:

def suggest_next_bet(session: Session):
    """
    1) Find all friends with miss_count >= 5 (i.e. they just missed their 5th in a row).
    2) Among those, group by each friend’s next_bet_choice() side (B/P).
    3) If no one has miss_count >= 5, return None (no suggestion yet).
    4) If all “5‐miss friends” share the same side, pick the maximum next_bet_amount among them.
       Otherwise, count frequency of each side, pick the side with majority, then pick max amount in that group.
    5) But our user will be instructed to bet the **opposite** side at that largest‐amount stake.
    """
    five_miss_friends = [f for f in session.friends if f.miss_count == 5]
    if not five_miss_friends:
        return None

    # Build a small dict: side → list of (friend, amount)
    by_side = {"B": [], "P": []}
    for f in five_miss_friends:
        nxt = f.next_bet_choice()
        amt = f.next_bet_amount(session.unit)
        if nxt in ("B","P"):
            by_side[nxt].append((f, amt))

    # If no valid next‐bet choice among them, bail out
    if not by_side["B"] and not by_side["P"]:
        return None

    # Count frequencies
    count_B = len(by_side["B"])
    count_P = len(by_side["P"])

    if count_B == 0 and count_P > 0:
        majority_side = "P"
        group = by_side["P"]
    elif count_P == 0 and count_B > 0:
        majority_side = "B"
        group = by_side["B"]
    else:
        # Both sides present: pick larger group
        if count_B > count_P:
            majority_side = "B"; group = by_side["B"]
        elif count_P > count_B:
            majority_side = "P"; group = by_side["P"]
        else:
            # tie in friend‐count: compare max-amount
            max_amt_B = max(amt for f, amt in by_side["B"]) if by_side["B"] else -1
            max_amt_P = max(amt for f, amt in by_side["P"]) if by_side["P"] else -1
            if max_amt_B >= max_amt_P:
                majority_side = "B"; group = by_side["B"]
            else:
                majority_side = "P"; group = by_side["P"]

    # Among that majority group, pick the friend with largest next_bet_amount:
    largest_friend, largest_amt = max(group, key=lambda x: x[1])

    # Our suggestion side is the *opposite* of `majority_side`
    suggestion_side = "P" if majority_side == "B" else "B"
    return {
        "friend_list": five_miss_friends,
        "majority_side": majority_side,
        "largest_friend": largest_friend.name,
        "largest_amt": largest_amt,
        "suggest_side": suggestion_side
    }


suggestion = suggest_next_bet(session)
if suggestion:
    st.markdown("## 2) Next‐Bet Suggestion (5th Miss Zone)")
    st.markdown(
        f"**Majority Side (cause friends just reached 5 misses):** {suggestion['majority_side']}\n\n"
        f"**Pick _largest_ bet from that group:** Friend {suggestion['largest_friend']} @ ${suggestion['largest_amt']:.2f}\n\n"
        f"**But your actual bet should be the _opposite_ side: → {suggestion['suggest_side']}**"
    )
else:
    st.markdown("## 2) Next‐Bet Suggestion")
    st.write("No friend has reached exactly 5 misses yet.  Keep feeding more hands until someone hits 5 misses.")


st.markdown("---")


# Star 2.0 progression table (for reference)
star_mult = [1,1.5,2.5,2.5,5,5,7.5,10,12.5,17.5,22.5,30]
star_df = pd.DataFrame([[session.unit * m for m in star_mult]],
                       index=['Bet Amt'], columns=list(range(1, 13)))
st.write("### Star 2.0 Progression (12 steps)")
st.dataframe(star_df, use_container_width=True)


# Friend dashboard – show each friend's metrics, with color flags
df = session.get_state_df()
t_df = df.set_index('Name').T
t_df.loc["History"] = [" ".join(session.history)] * len(t_df.columns)

header = ["Metric"] + list(t_df.columns)
values = [t_df.index.tolist()] + [t_df[c].tolist() for c in t_df.columns]
num = len(values[0])

# Build cell colors
cell_colors = [["white"] * num]
for col in t_df.columns:
    miss = t_df.at["Miss Count", col]
    col_col = []
    for metric in t_df.index:
        if metric in ("Next Bet", "Next Amount"):
            if miss > 10:
                col_col.append("lightcoral")
            elif miss >= 5:
                col_col.append("lightgreen")
            else:
                col_col.append("white")
        else:
            col_col.append("white")
    cell_colors.append(col_col)

fig = go.Figure(data=[
    go.Table(
        header=dict(values=header, fill_color="darkblue",
                    font=dict(color="white"), align="center"),
        cells=dict(values=values, fill_color=cell_colors,
                   font=dict(color="black"), align="center")
    )
])
fig.update_layout(height=600)
st.write("### 3) Friend Dashboard & Metrics")
st.plotly_chart(fig, use_container_width=True)


# Detailed per‐hand history (✔=hit, ✘=miss, blank=free)
if session.history:
    hist_df = pd.DataFrame(
        {f.name: f.history for f in session.friends},
        index=[f"Hand {i+1}" for i in range(len(session.history))]
    )
    st.write("### 4) Detailed Hand History")
    st.dataframe(hist_df, use_container_width=True)


# Session summary
st.write("### 5) Session Summary")
st.write(
    f"Hands recorded: **{len(session.history)}**   "
    f"Target (+{int(target/session.unit)} units = ${target:.2f})   "
    f"Stop (–{int(stoploss/session.unit)} units = ${stoploss:.2f})   "
    f"Bankroll: ${bankroll:.2f}   "
    f"Unit: ${session.unit:.2f}"
)

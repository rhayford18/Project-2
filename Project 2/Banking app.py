import streamlit as st
import json 
import os 
import hashlib
import datetime
import random
from pathlib import Path

# ── data helpers ──────────────────────────────────────────────────────────────
DATA_FILE = "data/users.json"

def load_data():
    Path("data").mkdir(exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    Path("data").mkdir(exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── stock helpers ─────────────────────────────────────────────────────────────
STOCKS = {
    "AAPL": {"name": "Apple Inc.",        "base": 178.0},
    "TSLA": {"name": "Tesla Inc.",         "base": 245.0},
    "GOOGL":{"name": "Alphabet Inc.",      "base": 141.0},
    "MSFT": {"name": "Microsoft Corp.",    "base": 415.0},
    "AMZN": {"name": "Amazon.com Inc.",    "base": 185.0},
    "NVDA": {"name": "NVIDIA Corp.",       "base": 875.0},
    "META": {"name": "Meta Platforms",     "base": 505.0},
    "NFLX": {"name": "Netflix Inc.",       "base": 628.0},
}

def get_price(ticker):
    base = STOCKS[ticker]["base"]
    seed = int(datetime.date.today().strftime("%Y%m%d")) + hash(ticker) % 1000
    random.seed(seed)
    return round(base * random.uniform(0.95, 1.05), 2)

def get_change(ticker):
    random.seed(hash(ticker + str(datetime.date.today())))
    return round(random.uniform(-4.5, 4.5), 2)

def recommend(portfolio):
    """Simple rule-based stock recommendations."""
    owned = set(portfolio.keys())
    recs = []
    for ticker, info in STOCKS.items():
        change = get_change(ticker)
        price  = get_price(ticker)
        if ticker not in owned and change > 2:
            recs.append((ticker, info["name"], price, change, "🟢 Strong Buy"))
        elif ticker in owned and change < -3:
            recs.append((ticker, info["name"], price, change, "🔴 Consider Selling"))
        elif ticker not in owned and -1 < change < 1:
            recs.append((ticker, info["name"], price, change, "🟡 Watch"))
    return recs[:4]

# ── auth pages ────────────────────────────────────────────────────────────────
def page_login():
    st.title("🏦 PyBank + Trading")
    tab1, tab2 = st.tabs(["Log In", "Create Account"])

    with tab1:
        st.subheader("Log in")
        username = st.text_input("Username", key="li_user")
        password = st.text_input("Password", type="password", key="li_pw")
        if st.button("Log In", use_container_width=True):
            data = load_data()
            if username in data and data[username]["password"] == hash_pw(password):
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with tab2:
        st.subheader("Create account")
        new_user = st.text_input("Choose a username", key="ca_user")
        new_pw   = st.text_input("Choose a password", type="password", key="ca_pw")
        new_pw2  = st.text_input("Confirm password",  type="password", key="ca_pw2")
        if st.button("Create Account", use_container_width=True):
            if not new_user or not new_pw:
                st.error("Username and password required.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            else:
                data = load_data()
                if new_user in data:
                    st.error("Username already taken.")
                else:
                    data[new_user] = {
                        "password": hash_pw(new_pw),
                        "balance": 10000.0,
                        "transactions": [],
                        "portfolio": {}
                    }
                    save_data(data)
                    st.success("Account created! You can now log in.")

# ── dashboard ─────────────────────────────────────────────────────────────────
def page_dashboard(user, data):
    balance   = data[user]["balance"]
    portfolio = data[user]["portfolio"]

    # portfolio value
    port_value = sum(
        get_price(t) * shares
        for t, shares in portfolio.items()
    )
    total = balance + port_value

    st.header("📊 Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash Balance",      f"${balance:,.2f}")
    c2.metric("Portfolio Value",   f"${port_value:,.2f}")
    c3.metric("Total Net Worth",   f"${total:,.2f}")

    if portfolio:
        st.subheader("Your Holdings")
        rows = []
        for ticker, shares in portfolio.items():
            price  = get_price(ticker)
            change = get_change(ticker)
            value  = price * shares
            rows.append({
                "Ticker": ticker,
                "Name": STOCKS[ticker]["name"],
                "Shares": shares,
                "Price": f"${price:,.2f}",
                "Day Change": f"{change:+.2f}%",
                "Total Value": f"${value:,.2f}"
            })
        st.table(rows)

# ── deposit / withdraw ────────────────────────────────────────────────────────
def page_banking(user, data):
    st.header("💵 Deposit & Withdraw")
    balance = data[user]["balance"]
    st.info(f"Current balance: **${balance:,.2f}**")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Deposit")
        dep_amt = st.number_input("Amount", min_value=0.01, step=10.0, key="dep")
        if st.button("Deposit", use_container_width=True):
            data[user]["balance"] += dep_amt
            data[user]["transactions"].append({
                "type": "deposit", "amount": dep_amt,
                "date": str(datetime.datetime.now())
            })
            save_data(data)
            st.success(f"Deposited ${dep_amt:,.2f}")
            st.rerun()

    with col2:
        st.subheader("Withdraw")
        wd_amt = st.number_input("Amount", min_value=0.01, step=10.0, key="wd")
        if st.button("Withdraw", use_container_width=True):
            if wd_amt > data[user]["balance"]:
                st.error("Insufficient funds.")
            else:
                data[user]["balance"] -= wd_amt
                data[user]["transactions"].append({
                    "type": "withdrawal", "amount": wd_amt,
                    "date": str(datetime.datetime.now())
                })
                save_data(data)
                st.success(f"Withdrew ${wd_amt:,.2f}")
                st.rerun()

# ── transfer ──────────────────────────────────────────────────────────────────
def page_transfer(user, data):
    st.header("🔄 Transfer")
    balance = data[user]["balance"]
    st.info(f"Your balance: **${balance:,.2f}**")

    recipient = st.text_input("Recipient username")
    amount    = st.number_input("Amount to transfer", min_value=0.01, step=10.0)

    if st.button("Send Transfer", use_container_width=True):
        if recipient not in data:
            st.error("User not found.")
        elif recipient == user:
            st.error("Cannot transfer to yourself.")
        elif amount > balance:
            st.error("Insufficient funds.")
        else:
            data[user]["balance"] -= amount
            data[recipient]["balance"] += amount
            now = str(datetime.datetime.now())
            data[user]["transactions"].append({"type": "transfer_out", "to": recipient,   "amount": amount, "date": now})
            data[recipient]["transactions"].append({"type": "transfer_in",  "from": user, "amount": amount, "date": now})
            save_data(data)
            st.success(f"Sent ${amount:,.2f} to {recipient}")
            st.rerun()

# ── stocks ────────────────────────────────────────────────────────────────────
def page_stocks(user, data):
    st.header("📈 Stock Trading")
    balance   = data[user]["balance"]
    portfolio = data[user]["portfolio"]

    # live prices table
    st.subheader("Market Overview")
    market_rows = []
    for ticker, info in STOCKS.items():
        price  = get_price(ticker)
        change = get_change(ticker)
        market_rows.append({
            "Ticker": ticker,
            "Company": info["name"],
            "Price": f"${price:,.2f}",
            "Day Change": f"{change:+.2f}%"
        })
    st.table(market_rows)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Buy Stocks")
        buy_ticker = st.selectbox("Select stock to buy", list(STOCKS.keys()), key="buy_t")
        buy_shares = st.number_input("Shares to buy", min_value=1, step=1, key="buy_s")
        buy_price  = get_price(buy_ticker)
        buy_cost   = buy_price * buy_shares
        st.caption(f"Cost: ${buy_cost:,.2f} | Balance: ${balance:,.2f}")
        if st.button("Buy", use_container_width=True):
            if buy_cost > balance:
                st.error("Insufficient funds.")
            else:
                data[user]["balance"] -= buy_cost
                data[user]["portfolio"][buy_ticker] = portfolio.get(buy_ticker, 0) + buy_shares
                data[user]["transactions"].append({
                    "type": "buy", "ticker": buy_ticker,
                    "shares": buy_shares, "price": buy_price,
                    "total": buy_cost, "date": str(datetime.datetime.now())
                })
                save_data(data)
                st.success(f"Bought {buy_shares} share(s) of {buy_ticker}")
                st.rerun()

    with col2:
        st.subheader("Sell Stocks")
        owned_tickers = [t for t in portfolio if portfolio[t] > 0]
        if not owned_tickers:
            st.info("You don't own any stocks yet.")
        else:
            sell_ticker = st.selectbox("Select stock to sell", owned_tickers, key="sell_t")
            max_shares  = portfolio.get(sell_ticker, 0)
            sell_shares = st.number_input("Shares to sell", min_value=1, max_value=max_shares, step=1, key="sell_s")
            sell_price  = get_price(sell_ticker)
            sell_value  = sell_price * sell_shares
            st.caption(f"You own {max_shares} share(s) | Value: ${sell_value:,.2f}")
            if st.button("Sell", use_container_width=True):
                data[user]["balance"] += sell_value
                data[user]["portfolio"][sell_ticker] -= sell_shares
                if data[user]["portfolio"][sell_ticker] == 0:
                    del data[user]["portfolio"][sell_ticker]
                data[user]["transactions"].append({
                    "type": "sell", "ticker": sell_ticker,
                    "shares": sell_shares, "price": sell_price,
                    "total": sell_value, "date": str(datetime.datetime.now())
                })
                save_data(data)
                st.success(f"Sold {sell_shares} share(s) of {sell_ticker} for ${sell_value:,.2f}")
                st.rerun()

    # recommendations
    st.divider()
    st.subheader("🤖 AI Stock Recommendations")
    st.caption("Based on today's market movement and your current portfolio")
    recs = recommend(portfolio)
    if recs:
        for ticker, name, price, change, label in recs:
            with st.container(border=True):
                rc1, rc2, rc3 = st.columns([2,1,1])
                rc1.markdown(f"**{ticker}** — {name}")
                rc2.markdown(f"${price:,.2f}  ({change:+.2f}%)")
                rc3.markdown(label)
    else:
        st.info("No strong signals today. Hold your positions.")

# ── transaction history ───────────────────────────────────────────────────────
def page_history(user, data):
    st.header("📋 Transaction History")
    txns = data[user]["transactions"]
    if not txns:
        st.info("No transactions yet.")
        return
    for t in reversed(txns):
        kind = t["type"]
        date = t.get("date","")[:19]
        if kind == "deposit":
            st.success(f"[{date}]  ⬇ Deposit  +${t['amount']:,.2f}")
        elif kind == "withdrawal":
            st.error(f"[{date}]  ⬆ Withdrawal  -${t['amount']:,.2f}")
        elif kind == "transfer_out":
            st.warning(f"[{date}]  → Transfer to {t['to']}  -${t['amount']:,.2f}")
        elif kind == "transfer_in":
            st.info(f"[{date}]  ← Transfer from {t['from']}  +${t['amount']:,.2f}")
        elif kind == "buy":
            st.info(f"[{date}]  📈 Bought {t['shares']} × {t['ticker']} @ ${t['price']:,.2f}  = ${t['total']:,.2f}")
        elif kind == "sell":
            st.success(f"[{date}]  💰 Sold {t['shares']} × {t['ticker']} @ ${t['price']:,.2f}  = ${t['total']:,.2f}")

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="PyBank", page_icon="🏦", layout="wide")

    if "user" not in st.session_state:
        page_login()
        return

    user = st.session_state.user
    data = load_data()

    with st.sidebar:
        st.title("🏦 PyBank")
        st.markdown(f"👤 **{user}**")
        st.divider()
        page = st.radio("Navigate", ["Dashboard","Banking","Transfer","Stocks","History"])
        st.divider()
        if st.button("Log Out"):
            del st.session_state.user
            st.rerun()

    if page == "Dashboard": page_dashboard(user, data)
    elif page == "Banking":  page_banking(user, data)
    elif page == "Transfer": page_transfer(user, data)
    elif page == "Stocks":   page_stocks(user, data)
    elif page == "History":  page_history(user, data)

if __name__ == "__main__":
    main()
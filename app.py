import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- App Configuration ---
st.set_page_config(page_title="FinPal", page_icon="💰", layout="wide")

# --- Title ---
st.title("💰 FinPal: Your Personal Finance Assistant")
st.markdown("Welcome! Let's get your finances in order.")

# --- Initialize session state for storing transactions ---
if 'transactions' not in st.session_state:
    # Create a sample DataFrame to start with
    st.session_state.transactions = pd.DataFrame({
        "Date": [datetime(2025, 8, 15), datetime(2025, 8, 20), datetime(2025, 9, 5), datetime(2025, 9, 25)],
        "Category": ["Food", "Transport", "Shopping", "Salary"],
        "Amount": [1500, 750, 4000, 75000],
        "Type": ["Expense", "Expense", "Expense", "Income"]
    })

# --- Sidebar for Adding New Transactions ---
st.sidebar.header("Add a New Transaction")
with st.sidebar.form("transaction_form", clear_on_submit=True):
    date = st.date_input("Date")
    category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Rent", "Salary", "Other"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    trans_type = st.radio("Type", ["Income", "Expense"])
    submitted = st.form_submit_button("Add Transaction")

    if submitted:
        new_transaction = pd.DataFrame([{
            "Date": pd.to_datetime(date),
            "Category": category,
            "Amount": amount,
            "Type": trans_type
        }])
        st.session_state.transactions = pd.concat([st.session_state.transactions, new_transaction], ignore_index=True)
        st.sidebar.success("Transaction added!")

# --- Main Page Layout ---
st.header("Financial Dashboard")

# Filter data
income_df = st.session_state.transactions[st.session_state.transactions["Type"] == "Income"]
expense_df = st.session_state.transactions[st.session_state.transactions["Type"] == "Expense"]

total_income = income_df["Amount"].sum()
total_expense = expense_df["Amount"].sum()
net_savings = total_income - total_expense

# Display key metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₹{total_income:,.2f}")
col2.metric("Total Expenses", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}", delta=f"{net_savings:,.2f}")

st.markdown("---")

# --- Charts and Data Tables ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Spending by Category")
    if not expense_df.empty:
        fig = px.pie(expense_df, names="Category", values="Amount", title="Expense Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses recorded yet to show a chart.")

with col2:
    st.subheader("Transaction History")
    st.dataframe(st.session_state.transactions.sort_values(by="Date", ascending=False), use_container_width=True)
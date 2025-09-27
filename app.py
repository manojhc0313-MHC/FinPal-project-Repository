import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('finance.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        amount REAL,
        type TEXT
    )
''')
conn.commit()

def add_transaction(date, category, amount, trans_type):
    c.execute("INSERT INTO transactions (date, category, amount, type) VALUES (?, ?, ?, ?)",
              (date, category, amount, trans_type))
    conn.commit()

def view_all_transactions():
    c.execute("SELECT date, category, amount, type FROM transactions")
    data = c.fetchall()
    return pd.DataFrame(data, columns=["Date", "Category", "Amount", "Type"])

# --- App Configuration ---
st.set_page_config(page_title="FinPal", page_icon="💰", layout="wide")

# --- Title ---
st.title("💰 FinPal: Your Personal Finance Assistant")
st.markdown("Welcome! Let's get your finances in order.")

# --- Sidebar for Adding New Transactions ---
# --- Sidebar for Adding New Transactions ---
st.sidebar.header("Add a New Transaction")
with st.sidebar.form("transaction_form", clear_on_submit=True):
    date = st.date_input("Date")
    category = st.selectbox("Category", ["Project Income", "Food", "Transport", "Shopping", "Rent", "Utilities", "Entertainment", "Bills", "Other"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    
    # Determine type based on category
    if category == "Project Income":
        trans_type = "Income"
    else:
        trans_type = "Expense"

    submitted = st.form_submit_button("Add Transaction")

    if submitted:
        add_transaction(date.strftime("%Y-%m-%d"), category, amount, trans_type)
        st.sidebar.success("Transaction added to database!")
        
        # THIS IS THE NEW SPECIAL FEATURE
        if trans_type == "Income":
            tax_estimate = amount * 0.20 # Assuming a 20% tax rate
            st.sidebar.warning(f"💡 Remember to set aside ₹{tax_estimate:,.2f} for taxes!")

# --- Main Page Layout ---
st.header("Financial Dashboard")
transactions_df = view_all_transactions()

if not transactions_df.empty:
    transactions_df['Date'] = pd.to_datetime(transactions_df['Date'])
    transactions_df['Month'] = transactions_df['Date'].dt.to_period('M')
else:
    transactions_df = pd.DataFrame(columns=["Date", "Category", "Amount", "Type", "Month"])

income_df = transactions_df[transactions_df["Type"] == "Income"]
expense_df = transactions_df[transactions_df["Type"] == "Expense"]

total_income = income_df["Amount"].sum()
total_expense = expense_df["Amount"].sum()
net_savings = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₹{total_income:,.2f}")
col2.metric("Total Expenses", f"₹{total_expense:,.2f}")
col3.metric("Net Savings", f"₹{net_savings:,.2f}", delta=f"{net_savings:,.2f}")
st.markdown("---")

# --- BACKEND LOGIC (Prediction and Recommendation) ---
def predict_expenses(df):
    if df.empty or len(df['Month'].unique()) < 2: return 0
    monthly_expenses = df.groupby('Month')['Amount'].sum().reset_index()
    monthly_expenses['Month_Num'] = range(1, len(monthly_expenses) + 1)
    X, y = monthly_expenses[['Month_Num']], monthly_expenses['Amount']
    model = LinearRegression().fit(X, y)
    return model.predict([[len(monthly_expenses) + 1]])[0]

def get_recommendation(savings):
    if savings < 5000: return "Focus on building an emergency fund."
    elif 5000 <= savings < 20000: return "Consider starting a Systematic Investment Plan (SIP)."
    elif savings >= 20000: return "Excellent savings! Explore a mix of mutual funds and stocks."
    else: return "Your expenses are higher than your income. Review your spending."

st.header("💡 Financial Forecast & Recommendations")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Next Month's Expense Prediction")
    predicted_expenses = predict_expenses(expense_df.copy())
    if predicted_expenses > 0: st.metric("Predicted Expenses", f"₹{predicted_expenses:,.2f}")
    else: st.info("Add more monthly data to enable prediction.")
with col2:
    st.subheader("Your Personalized Tip")
    if not transactions_df.empty:
        latest_month = transactions_df['Month'].max()
        latest_month_income = income_df[income_df['Month'] == latest_month]['Amount'].sum()
        latest_month_expense = expense_df[expense_df['Month'] == latest_month]['Amount'].sum()
        recommendation = get_recommendation(latest_month_income - latest_month_expense)
        st.success(recommendation)
    else: st.info("Add some transactions to get a tip.")
st.markdown("---")

# --- Charts and Data Tables ---
st.header("📊 Detailed Breakdown")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Spending by Category")
    if not expense_df.empty:
        fig = px.pie(expense_df, names="Category", values="Amount", title="Expense Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("No expenses recorded yet to show a chart.")
with col2:
    st.subheader("Transaction History")
    if not transactions_df.empty:
        st.dataframe(transactions_df.sort_values(by="Date", ascending=False).drop(columns='Month'), use_container_width=True)
    else: st.write("No transactions in the database.")
st.markdown("---")

# --- FINAL FEATURE: AI CHATBOT ---
# --- FINAL FEATURE: AI CHATBOT ---
st.header("🤖 Chat with FinPal AI")
user_question = st.text_input("Ask me about your finances:")

if user_question:
    question = user_question.lower()
    if "total income" in question:
        st.write(f"Your total income is: ₹{total_income:,.2f}")
    
    # --- THIS IS THE NEW PART ---
    elif "average income" in question:
        if not income_df.empty:
            num_months = income_df['Month'].nunique()
            if num_months > 0:
                average_income = total_income / num_months
                st.write(f"Your average monthly income across {num_months} month(s) is: ₹{average_income:,.2f}")
            else:
                st.write("I can't calculate an average yet because there are no full months of income data.")
        else:
            st.write("No income has been recorded yet.")
    # --- END OF NEW PART ---

    elif "total expense" in question or "total spending" in question:
        st.write(f"Your total expenses are: ₹{total_expense:,.2f}")

    elif "how much" in question and "spend on" in question:
        category = question.split("spend on")[-1].strip().capitalize()
        category_expense = expense_df[expense_df['Category'] == category]
        if not category_expense.empty:
            total = category_expense['Amount'].sum()
            st.write(f"You spent ₹{total:,.2f} on {category}.")
        else:
            st.warning(f"I couldn't find any spending for the category: {category}")

    elif "show me" in question and "history" in question:
        category = question.split("history")[0].split("me")[-1].strip().capitalize()
        category_expense = expense_df[expense_df['Category'] == category]
        if not category_expense.empty:
            st.write(f"Here is your transaction history for {category}:")
            st.dataframe(category_expense)
        else:
            st.warning(f"I couldn't find any spending for the category: {category}")
            
    else:
        st.error("Sorry, I don't understand that question. Try asking about 'total income', 'average income', 'total expenses', or 'how much did I spend on [Category]'.")
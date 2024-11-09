# app.py
import streamlit as st
from chatbot import generate_response, load_knowledge_base

# Load knowledge base when the app starts
knowledge_base = load_knowledge_base("policies.xlsx")

# Streamlit UI
st.set_page_config(page_title="E-Commerce Customer Support Chatbot", page_icon="🛒")
st.title("NCG E-Commerce Customer Support Chatbot 🛒 ")
st.write("Welcome! I’m here to help with your orders, returns, refunds, and more.")

# Input box for customer to enter their query
user_input = st.text_input("Enter your question here:", "")

# Button to submit the query
if st.button("Submit"):
    # Generate and display the chatbot's response
    if user_input:
        response = generate_response(user_input)
        st.write(response)
    else:
        st.write("Please enter a question to get assistance.")

# Display helpful information
st.sidebar.title("Chatbot Instructions")
st.sidebar.write("""
1. Ask about order status, returns, refunds, or exchanges.
2. Inquire about specific products by name to get details.
3. You can also ask general questions such as FAQs.
""")

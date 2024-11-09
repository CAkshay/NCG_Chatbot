
# chatbot.py
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
load_dotenv()
os.environ['OPENAI_API_KEY']=os.getenv('OPENAI_API_KEY')

# chatbot.py
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI

# Load all sheets from the Excel file into the knowledge base
def load_knowledge_base(file_path="policies.xlsx"):
    # Load Product Catalog
    product_catalog_df = pd.read_excel(file_path, sheet_name="Product Catalog Data")
    
    # Load Order Data
    order_data_df = pd.read_excel(file_path, sheet_name="Order Data")
    
    # Load Customer Data
    customer_data_df = pd.read_excel(file_path, sheet_name="Customer Data")
    
    # Load Return & Refund Policy Data
    policy_df = pd.read_excel(file_path, sheet_name="Return & Refund Policy Data")
    policies = {row["PolicyType"].lower(): row["Details"] for _, row in policy_df.iterrows()}
    
    # Load Common Customer Support Queries
    support_queries_df = pd.read_excel(file_path, sheet_name="Common Customer Support Queries")
    
    # Load Order Status Data
    order_status_df = pd.read_excel(file_path, sheet_name="Order Status Data")
    status_descriptions = {row["Status"]: row["Description"] for _, row in order_status_df.iterrows()}
    
    # Load FAQ Data
    faq_df = pd.read_excel(file_path, sheet_name="FAQ Data")

    return {
        "product_catalog": product_catalog_df,
        "order_data": order_data_df,
        "customer_data": customer_data_df,
        "policies": policies,
        "support_queries": support_queries_df,
        "order_status": status_descriptions,
        "faq": faq_df
    }

# Load knowledge base
knowledge_base = load_knowledge_base()

# Access individual knowledge base elements
POLICIES = knowledge_base["policies"]
ORDER_DATA = knowledge_base["order_data"]
PRODUCT_CATALOG = knowledge_base["product_catalog"]
CUSTOMER_DATA = knowledge_base["customer_data"]
SUPPORT_QUERIES = knowledge_base["support_queries"]
ORDER_STATUS_DESCRIPTIONS = knowledge_base["order_status"]
FAQ = knowledge_base["faq"]

# Initialize the Language Model (replace with your model API key as needed)
llm = ChatOpenAI(model='gpt-4o', temperature=0.1)  # Use temperature for response variation

# Define a prompt template with policies directly in the template
prompt_template = PromptTemplate(
    input_variables=["customer_input"],
    template=f"""
    You are a customer support chatbot for an e-commerce platform. Respond in a friendly tone based on the following:
    1. If asked about "order status," prompt for an order number and Make sure to fetch the latest status from the order data sheet
       And give the latest status and expected delivery date if available.
    2. If asked about "return," "refund," or "exchange," provide information as per the company's policies:
       - Return: {POLICIES.get("return", "Policy not found.")}
       - Refund: {POLICIES.get("refund", "Policy not found.")}
       - Exchange: {POLICIES.get("exchange", "Policy not found.")}
    3. For product inquiries, use function get_product_info(product_name) to fetch product details.
        provide information if available in the product catalog or offer to direct to a product page.
    4. Refer to FAQs for other common questions or escalate to a live agent for complex queries.
    
    Customer: {{customer_input}}
    Chatbot:
    """
)

# Chain to process user input
chat_chain = LLMChain(llm=llm, prompt=prompt_template)

# Function to retrieve product information
def get_product_info(product_name):
    product_row = PRODUCT_CATALOG[PRODUCT_CATALOG["ProductName"].str.contains(product_name, case=False)]
    if not product_row.empty:
        return product_row.iloc[0].to_dict()
    else:
        return "Product not found."

# Function to retrieve customer information
def get_customer_info(customer_id):
    customer_row = CUSTOMER_DATA[CUSTOMER_DATA["CustomerID"] == customer_id]
    if not customer_row.empty:
        return customer_row.iloc[0].to_dict()
    else:
        return "Customer not found."

# Function to get order status
def get_order_status(order_id):
    order_row = ORDER_DATA[ORDER_DATA["OrderID"] == order_id]
    if not order_row.empty:
        status = order_row.iloc[0]["Status"]
        expected_delivery = order_row.iloc[0]["ExpectedDeliveryDate"]
        description = ORDER_STATUS_DESCRIPTIONS.get(status, "Status description not available.")
        if pd.isnull(expected_delivery):
            expected_delivery_text = "Expected delivery date is not available yet."
        else:
            expected_delivery_text = f"Expected delivery date is {expected_delivery.strftime('%m/%d/%Y')}."
        return f"Order {order_id} status: {status} - {description}. {expected_delivery_text}"
    else:
        return "Order ID not found. Please check the ID and try again."

# Function to retrieve FAQ response
def get_faq_response(question):
    faq_row = FAQ[FAQ["Question"].str.contains(question, case=False)]
    if not faq_row.empty:
        return faq_row.iloc[0]["Answer"]
    else:
        return "FAQ not found."

# Core function to process chatbot response
def generate_response(user_input):
    # Check if the input includes known query keywords to trigger specific responses
    if "order status" in user_input.lower():
        order_id = extract_order_id(user_input)
        if order_id:
            return get_order_status(order_id)
        else:
            return "Please provide a valid order number for order status inquiries."
    elif "product" in user_input.lower():
        product_info = get_product_info(user_input)
        return product_info if isinstance(product_info, str) else f"Product: {product_info['ProductName']} - {product_info['Description']} (${product_info['Price']})"
    elif "faq" in user_input.lower():
        return get_faq_response(user_input)
    
    # Fallback to general LangChain processing if no specific keywords are matched
    response = chat_chain.run({"customer_input": user_input})
    return response

# Helper function to extract order ID
import re

def extract_order_id(text):
    match = re.search(r"O\d{4}", text)
    return match.group(0) if match else None

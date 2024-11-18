import streamlit as st
import datetime
from fpdf import FPDF
import os
import json
import random

# Define file path relative to the current working directory
customer_data_file = "customers.json"  # Save in the app directory

# Load existing customer data with error handling
try:
    if os.path.exists(customer_data_file):
        with open(customer_data_file, "r") as file:
            customer_data = json.load(file)
    else:
        customer_data = {}
except json.JSONDecodeError:
    st.warning("Customer data file is corrupted. Resetting the data.")
    customer_data = {}
    with open(customer_data_file, "w") as file:
        json.dump(customer_data, file)

# Initialize session state variables
if 'customer_id' not in st.session_state:
    st.session_state['customer_id'] = None
if 'download_receipt_ready' not in st.session_state:
    st.session_state['download_receipt_ready'] = False
if 'receipt_file' not in st.session_state:
    st.session_state['receipt_file'] = None

# Define a list of services and their prices
services = {
    "Water 2L": 50.0,
    "Water 1L": 30.0,
    "SoftDrink": 80.0,
    "Parking": 50.0,
    "Seat": 50.0
}

constant_fee = 50.0  # Define the constant fee for all customers

# Streamlit app
st.title("Iman Restaurant Customer Service Payment Calculator")

st.subheader("Customer Information")

# Check if the user is a returning customer by entering a unique ID
if st.session_state['customer_id'] is None:
    customer_id_input = st.text_input("Enter Customer ID (leave blank if new):")
    if customer_id_input:
        st.session_state['customer_id'] = customer_id_input

# If a customer ID is entered, load their information
if st.session_state['customer_id'] and st.session_state['customer_id'] in customer_data:
    customer_info = customer_data[st.session_state['customer_id']]
    customer_name = customer_info["name"]
    customer_contact = customer_info["contact"]
    st.success(f"Welcome back, {customer_name}!")
else:
    # Input fields for customer information
    customer_name = st.text_input("Customer Name")
    customer_contact = st.text_input("Contact Number")
    if customer_name and customer_contact:
        # Generate a unique 4-digit ID only once and save it in session state
        if st.session_state['customer_id'] is None:
            while True:
                customer_id = str(random.randint(1000, 9999))
                if customer_id not in customer_data:
                    st.session_state['customer_id'] = customer_id
                    break

        # Save new customer data
        customer_data[st.session_state['customer_id']] = {"name": customer_name, "contact": customer_contact}
        with open(customer_data_file, "w") as file:
            json.dump(customer_data, file)
        st.success(f"New customer added with ID: {st.session_state['customer_id']}")

st.subheader("Select the services you used:")
# User input form for selecting services and specifying quantity
selected_services = []
service_details = {}
for service, price in services.items():
    quantity = st.number_input(f"How many times did you use {service}? (${price} per use)", min_value=0, step=1)
    if quantity > 0:
        selected_services.append(service)
        service_details[service] = {
            "quantity": quantity,
            "price_per_use": price
        }

# Calculate total amount based on selected services and the constant fee
total_amount = sum(details["quantity"] * details["price_per_use"] for details in service_details.values()) + constant_fee

# Display the selected services, quantity, and total amount
if selected_services:
    st.write("### Services Selected:")
    for service, details in service_details.items():
        quantity = details["quantity"]
        price_per_use = details["price_per_use"]
        total_for_service = quantity * price_per_use
        st.write(f"- {service} (${price_per_use} per use) - {quantity} times - Total: ${total_for_service:.2f}")
    st.write(f"### Constant Fee: ${constant_fee:.2f}")
    st.write("### Total Amount to Pay:")
    st.write(f"${total_amount:.2f}")
else:
    st.write("No services selected.")
    st.write(f"### Constant Fee: ${constant_fee:.2f}")
    st.write("### Total Amount to Pay:")
    st.write(f"${constant_fee:.2f}")

# Confirm payment button
if st.button("Confirm Payment"):
    if selected_services and customer_name and customer_contact:
        st.success(f"Payment of ${total_amount:.2f} confirmed for {customer_name}. Thank you!")
        
        # Generate a PDF receipt
        receipt = FPDF()
        receipt.add_page()
        receipt.set_font("Arial", size=12)
        receipt.cell(200, 10, txt="Payment Receipt", ln=True, align="C")
        receipt.cell(200, 10, txt=f"Customer Name: {customer_name}", ln=True, align="L")
        receipt.cell(200, 10, txt=f"Customer ID: {st.session_state['customer_id']}", ln=True, align="L")
        receipt.cell(200, 10, txt=f"Contact Number: {customer_contact}", ln=True, align="L")
        receipt.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="L")
        receipt.cell(200, 10, txt="Services:", ln=True, align="L")
        for service, details in service_details.items():
            quantity = details["quantity"]
            price_per_use = details["price_per_use"]
            total_for_service = quantity * price_per_use
            receipt.cell(200, 10, txt=f"- {service} (${price_per_use} per use) - {quantity} times - Total: ${total_for_service:.2f}", ln=True, align="L")
        receipt.cell(200, 10, txt=f"Constant Fee: ${constant_fee:.2f}", ln=True, align="L")
        receipt.cell(200, 10, txt=f"Total Amount: ${total_amount:.2f}", ln=True, align="L")
        
        # Store receipt file path in session state
        st.session_state['receipt_file'] = f"{customer_name}_receipt.pdf"
        receipt.output(st.session_state['receipt_file'])
        
        # Enable the download button
        st.session_state['download_receipt_ready'] = True
        
        # Save the transaction locally
        transaction_file = "transactions.txt"
        with open(transaction_file, "a") as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {customer_name}, {customer_contact}, {service_details}, ${total_amount:.2f}\n")
        
        # Reset session state to clear the fields
        st.session_state['customer_id'] = None
        st.rerun()
    else:
        st.warning("Please fill in customer information and select at least one service.")

# Show download button only if the receipt is ready
if st.session_state['download_receipt_ready'] and st.session_state['receipt_file']:
    with open(st.session_state['receipt_file'], "rb") as file:
        st.download_button(
            label="Download Receipt",
            data=file,
            file_name=st.session_state['receipt_file'],
            mime="application/pdf"
        )

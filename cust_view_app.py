import gradio as gr
import requests
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURATION & ASSETS ---
SUPABASE_URL = "https://zcvscaqbmhwcpkhvtoei.supabase.co"
SUPABASE_KEY = "sb_publishable_EbRsoSH-A_0x0IZ9TkahxQ_bt7-eSSx"
LOGO_URL = "https://github.com/AMARNAATH-M/AITP-Session-3/blob/main/mishTee_logo.png?raw=true"
CSS_URL = "https://raw.githubusercontent.com/AMARNAATH-M/AITP-Session-3/refs/heads/main/style.css"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch Custom CSS
try:
    mishtee_css = requests.get(CSS_URL).text
except Exception:
    mishtee_css = "" # Fallback if fetch fails

# --- 2. CORE FUNCTIONS ---

def get_customer_portal_data(phone_number):
    """Retrieves greeting and order history for the entered phone number."""
    if not phone_number or len(phone_number) < 10:
        return "Please enter a valid 10-digit mobile number.", pd.DataFrame()

    # Fetch Customer Name
    cust_res = supabase.table("customers").select("full_name").eq("phone", phone_number).execute()
    
    if not cust_res.data:
        return "Namaste! It looks like you're new to MishTee-Magic. Please register to view history.", pd.DataFrame()

    customer_name = cust_res.data[0]['full_name']
    greeting = f"## Namaste, {customer_name} ji! \nGreat to see you again."

    # Fetch Order History with joined product names
    order_res = supabase.table("orders").select(
        "order_id, order_date, qty_kg, status, products(sweet_name)"
    ).eq("cust_phone", phone_number).execute()

    if order_res.data:
        flat_data = [{
            "Order ID": row['order_id'],
            "Date": row['order_date'],
            "Item": row['products']['sweet_name'],
            "Qty (kg)": row['qty_kg'],
            "Status": row['status']
        } for row in order_res.data]
        df_orders = pd.DataFrame(flat_data)
    else:
        df_orders = pd.DataFrame(columns=["Order ID", "Date", "Item", "Qty (kg)", "Status"])

    return greeting, df_orders

def get_trending_products():
    """Retrieves the top 4 best-selling products."""
    res = supabase.table("orders").select("qty_kg, products(sweet_name, variant_type)").execute()
    
    if not res.data:
        return pd.DataFrame(columns=["Sweet Name", "Variant", "Total Sold (kg)"])

    df = pd.DataFrame([
        {"Sweet Name": row['products']['sweet_name'], "Variant": row['products']['variant_type'], "qty": row['qty_kg']} 
        for row in res.data
    ])
    
    trending_df = df.groupby(["Sweet Name", "Variant"])["qty"].sum().reset_index()
    trending_df = trending_df.sort_values(by="qty", ascending=False).head(4)
    trending_df.columns = ["Sweet Name", "Variant", "Total Sold (kg)"]
    return trending_df

def handle_login(phone):
    """Wrapper function to trigger all UI updates on login."""
    greeting, history = get_customer_portal_data(phone)
    trending = get_trending_products()
    return greeting, history, trending

# --- 3. GRADIO UI LAYOUT ---

with gr.Blocks(css=mishtee_css, title="MishTee-Magic | Purity & Health") as app:
    
    # Header: Logo and Slogan
    with gr.Column(elem_id="header", variant="container"):
        gr.Image(LOGO_URL, show_label=False, width=200, container=False, interactive=False)
        gr.Markdown("# MishTee-Magic")
        gr.Markdown("### **Purity and Health in Every Bite**")
    
    gr.HTML("<br><hr><br>")

    # Input Section
    with gr.Row():
        with gr.Column(scale=2):
            phone_input = gr.Textbox(
                label="Customer Login", 
                placeholder="Enter your 10-digit mobile (e.g. 9876543210)",
                lines=1
            )
            login_btn = gr.Button("Access Portal", variant="primary")
        
        with gr.Column(scale=3):
            greeting_output = gr.Markdown("### Welcome to MishTee-Magic")

    # Data Display Section (Tabbed for Minimalism)
    with gr.Tabs():
        with gr.TabItem("My Order History"):
            history_table = gr.Dataframe(
                headers=["Order ID", "Date", "Item", "Qty (kg)", "Status"],
                interactive=False
            )
        
        with gr.TabItem("Trending Today"):
            trending_table = gr.Dataframe(
                headers=["Sweet Name", "Variant", "Total Sold (kg)"],
                interactive=False
            )

    # Event Listener
    login_btn.click(
        fn=handle_login,
        inputs=[phone_input],
        outputs=[greeting_output, history_table, trending_table]
    )

    # Footer
    gr.Markdown("---")
    gr.Markdown("<center><small>Artisanal Indian Sweets | A2 Milk & Organic Ingredients Only</small></center>")

# --- 4. LAUNCH ---
if __name__ == "__main__":
    app.launch()

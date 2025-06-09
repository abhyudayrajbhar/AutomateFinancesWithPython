import streamlit as st
import pandas as pd # Allow us to easily import our CSV File
import plotly.express as px # Allow us to quickly make plots(pie chart, bar chart etc.)
import json # For saving different categories
import os

st.set_page_config(page_title= "Simple Finance App", page_icon="💰", layout="wide") # To set the configurations of the page

# SETTING UP DIFFERENT CATEGORIES

category_file = "categories.json"
# Ability to save the categories
if "categories" not in st.session_state:  # Storing states/information before Streamlit re-runs the application on refresh
    st.session_state.categories = {
        "Uncategorized": []
    }

if os.path.exists(category_file):  # To save the categories if it already exists in json/database
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

def save_categories(): # Creating different Categories
    with open(category_file, "w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transactions(df):  # Creating New Column with value Uncategorized
    df["Category"] = "Uncategorized"
    
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        
        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lowered_keywords:
                df.at[idx, "Category"] = category
                
    return df

def load_transactions(file):
    try: # If there's any issue loading our file
        try:
            df = pd.read_csv(file, encoding="utf-8") # Using Pandas
        except UnicodeDecodeError:
            df = pd.read_csv(file, encoding="ISO-8859-1")
            
        df.columns = [col.strip() for col in df.columns] # Removing leading/trailing whitespaces of columns
        df["Amount"] = df["Amount"].str.replace(",", "").astype(float) # Amount(str) --> Amount(float) & removing ","
        df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%y")  # Date(28 Feb 2025) --> Date(2025-02-28) & time(00:00:00)

        return categorize_transactions(df)
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}") # Shows error on screen
        return None # To indicate there are no data frame that were able to load

def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    
    return False

def main(): # Inserting file, UI, & other functions for handling logics
    st.title("Simple Finance Dashboard")
    
    uploaded_file = st.file_uploader("Upload your transaction CSV File", type= ["csv", "pdf"]) # Component that allows to upload file
    
    if uploaded_file is not None: # If file is actually uploaded
        df = load_transactions(uploaded_file)
        
        if df is not None:
            debits_df = df[df["Debit/Credit"] == "Debit"].copy() # Gives new df that only contains debit/credit columns debit values
            credits_df = df[df["Debit/Credit"] == "Credit"].copy() # Gives new df that only contains debit/credit columns credit values
            
            st.session_state.debits_df = debits_df.copy()
            
            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"]) # Creating multiple tabs
            with tab1: # Displaying the tabs
                # Adding categories
                new_category = st.text_input("New Category Name")
                add_button = st.button("Add Category")
                
                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun() # Forces to refresh the page
                        
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debits_df[["Date", "Details", "Amount", "Category"]],
                    column_config = {
                        "Date": st.column_config.DateColumn("Date", format= "DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format = "%.2f USD"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options = list(st.session_state.categories.keys())
                        )
                    },
                    hide_index = True,
                    use_container_width = True,
                    key = "category_editor"
                )
                
                save_button = st.button("Apply Changes", type = "primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.debits_df.at[idx, "Category"]:
                            continue
                        
                        details = row["Details"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details) 
                        
                st.subheader('Expense Summary')
                category_totals = st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending= False)
                
                st.dataframe(
                    category_totals,
                    column_config= {
                      "Amount": st.column_config.NumberColumn("Amount", format= "%.2f USD" )  
                    },
                    use_container_width= True,
                    hide_index= True
                )
                
                # Showing Charts - Using Ploty Express
                fig = px.pie(
                    category_totals,
                    values = "Amount",
                    names = "Category",
                    title = "Expenses by Category"
                )
                st.plotly_chart(fig, use_container_width= True)
                
            with tab2:
                st.subheader("Payment Summary")
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Payments", f"{total_payments:,.2f} USD")
                st.write(credits_df)

main() # Used to render entire script(necessary)

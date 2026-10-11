import streamlit as st
import pandas as pd
import joblib
import sys
from supabase import create_client, Client


sys.path.append('./backend')
try:
    import preprocessing
except ImportError:
    pass

@st.cache_resource
def load_model():
    return joblib.load("backend/model_pipeline.pkl")

model = load_model()

st.title("Customer Spending Prediction Dashboard")
st.write("أدخل بيانات العميل للتنبؤ بإجمالي الإنفاق (Total Spent):")

year_birth = st.number_input("Year of Birth", min_value=1900, max_value=2005, value=1971)
education = st.selectbox("Education", ["Graduation", "Master", "PhD", "Basic"])
marital_status = st.selectbox("Marital Status", ["Single", "Married", "Together", "Divorced", "Widow"])
income = st.number_input("Income", value=33316.0)
kidhome = st.number_input("Kidhome", min_value=0, max_value=2, value=1)
teenhome = st.number_input("Teenhome", min_value=0, max_value=2, value=1)
dt_customer = st.text_input("Customer Date (DD-MM-YYYY)", value="04-10-2013")
recency = st.number_input("Recency", value=34)
num_deals = st.number_input("Num Deals Purchases", value=3)
num_web = st.number_input("Num Web Purchases", value=2)
num_catalog = st.number_input("Num Catalog Purchases", value=1)
num_store = st.number_input("Num Store Purchases", value=4)
num_web_visits = st.number_input("Num Web Visits Month", value=6)

accepted_cmp3 = st.selectbox("Accepted Cmp 3", [0, 1])
accepted_cmp4 = st.selectbox("Accepted Cmp 4", [0, 1])
accepted_cmp5 = st.selectbox("Accepted Cmp 5", [0, 1])
accepted_cmp1 = st.selectbox("Accepted Cmp 1", [0, 1])
accepted_cmp2 = st.selectbox("Accepted Cmp 2", [0, 1])
complain = st.selectbox("Complain", [0, 1])
response = st.selectbox("Response", [0, 1])

if st.button("Predict Spending"):
    payload = {
        "Year_Birth": year_birth,
        "Education": education,
        "Marital_Status": marital_status,
        "Income": income,
        "Kidhome": kidhome,
        "Teenhome": teenhome,
        "Dt_Customer": dt_customer,
        "Recency": recency,
        "NumDealsPurchases": num_deals,
        "NumWebPurchases": num_web,
        "NumCatalogPurchases": num_catalog,
        "NumStorePurchases": num_store,
        "NumWebVisitsMonth": num_web_visits,
        "AcceptedCmp3": accepted_cmp3,
        "AcceptedCmp4": accepted_cmp4,
        "AcceptedCmp5": accepted_cmp5,
        "AcceptedCmp1": accepted_cmp1,
        "AcceptedCmp2": accepted_cmp2,
        "Complain": complain,
        "Response": response
    }
    
    try:
        df = pd.DataFrame([payload])
        prediction = float(model.predict(df)[0])
        st.success(f"إجمالي الإنفاق المتوقع (Total Spent): ${prediction:.2f}")
        
        supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        supabase.table("predictions").insert({
            "features": payload,
            "predicted_spent": prediction
        }).execute()
        
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
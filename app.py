import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from google.cloud.firestore_v1.base_query import FieldFilter

def get_firestore_client():
    """
    Initializes and returns a Firestore client.
    Handles service account key loading and potential errors.
    """
    try:
        # Use serviceAccountKey.json for authentication
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        return db
    except Exception as e:
        st.error(f"An error occurred while connecting to Firestore: {e}")
        st.info("Please make sure the 'serviceAccountKey.json' file is in the root directory and is valid.")
        return None

def main():
    """
    The main function of the Sentinel Dashboard application.
    """
    st.title("🛡️ Sentinel Dashboard")

    db = get_firestore_client()

    if not db:
        st.warning("Firestore client is not available. Cannot fetch data.")
        return

    # 1. Sidebar Filter
    view_option = st.sidebar.radio("View Filter", ["Online Only", "All Discovered Hosts"])

    miners_ref = db.collection("miners")

    # 2. Filtering Logic (now on the server-side)
    if view_option == "Online Only":
        docs = miners_ref.where(filter=FieldFilter("status", "==", "Online")).stream()
    else:
        docs = miners_ref.stream()

    for doc in docs:
        data = doc.to_dict()
        status = data.get("status", "Offline")

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Host:** {doc.id}")
                if status == "Online":
                    hashrate = data.get("hashrate", 0)
                    st.success(f"Hashrate: {hashrate:.2f} H/s")
                else:
                    st.error("Offline")
            with col2:
                cpu_usage = data.get('cpu_usage', 'N/A')
                st.metric("CPU", f"{cpu_usage}%" if isinstance(cpu_usage, (int, float)) else cpu_usage)

if __name__ == "__main__":
    main()
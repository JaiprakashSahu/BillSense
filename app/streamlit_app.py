import streamlit as st
from src.generate import answer_query

st.set_page_config(page_title="BillSense", layout="wide")
st.title("BillSense — Indian Bill Q&A")

# Sidebar: select bill
bill = st.sidebar.selectbox("Choose a bill:", [
    "Personal Data Protection Bill 2019",
    "Digital Personal Data Protection Act 2023",
    "Bharatiya Nyaya Sanhita 2023"
])

# Two tabs
tab1, tab2 = st.tabs(["Summary", "Ask a Question"])

with tab1:
    st.header(f"Summary: {bill}")
    summary_path = f"data/summaries/{bill}.md"
    try:
        with open(summary_path) as f:
            st.markdown(f.read())
    except FileNotFoundError:
        st.info("Summary not yet generated for this bill. Run the summarization pipeline first.")

with tab2:
    st.header("Ask about this bill")
    query = st.text_input("Your question:", placeholder="What are the penalties for non-compliance?")

    if query:
        with st.spinner("Searching..."):
            result = answer_query(query, bill)

        st.markdown("### Answer")
        st.markdown(result['answer'])

        st.markdown("### Sources")
        for src in result['sources']:
            with st.expander(f"Section {src['section_id']} (distance: {src['distance']:.3f})"):
                st.text(src['content'][:1000] + "...")

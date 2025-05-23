import streamlit as st
import google.generativeai as genai



# Securely load the API key from Streamlit secrets
api_key = st.secrets["gcp"]["gemini_api_key"]
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash-lite")


body_parts = {
    "Chest": ["Upper Chest", "Lower Chest"],
    "Arm": ["Upper Arm", "Forearm"],
    "Leg": ["Thigh", "Calf", "Knee"],
    "Abdomen": ["Upper Abdomen", "Lower Abdomen"],
    "Head": ["Forehead", "Back of Head", "Sides"],
    "Back": ["Upper Back", "Lower Back"],
    "Neck": ["Front", "Back", "Sides"]
}


st.set_page_config(page_title="Medical Diagnosis App", layout="centered")

st.markdown("""
    <style>
    .stRadio > div { flex-direction: row; }
    .section-title { font-size: 20px; font-weight: bold; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

st.title("🩺 AI-Powered Medical Suggestion")


selected_part = st.selectbox("Select Body Part", ["-- Select --"] + list(body_parts.keys()))
subregion = None

if selected_part != "-- Select --":
    subregion = st.selectbox(f"Select Area of {selected_part}", ["-- Select --"] + body_parts[selected_part])


if subregion and subregion != "-- Select --":
    q_prompt = f"List 15 short yes/no medical diagnostic questions related to the {subregion.lower()} of the {selected_part.lower()}."

    if st.button("✅ Generate Diagnostic Questions"):
        try:
            raw = model.generate_content(q_prompt).text.strip().split("\n")
            questions = [
    q.lstrip("1234567890.- ").strip()
    for q in raw
    if q.strip() and "here are" not in q.lower()
][:15]

            st.session_state["questions_ready"] = True
            st.session_state["questions"] = questions
        except Exception as e:
            st.error("Error generating questions. Please try again.")
            st.stop()


if "questions_ready" in st.session_state and st.session_state["questions_ready"]:
    st.subheader("Answer the following questions:")
    st.markdown(f"Here are some yes/no diagnostic questions related to the **{subregion.lower()}**:")

    answers = {}
    with st.form("question_form"):
        for i, q in enumerate(st.session_state["questions"], 1):
            answers[q] = st.radio(f"**{i}. {q}**", ["Yes", "No"], key=f"q{i}")
        submitted = st.form_submit_button("🔍 Submit and Diagnose")

    if submitted:
        yes_responses = [q for q, a in answers.items() if a == "Yes"]
        response_prompt = f"""
        A user has symptoms in the {subregion.lower()} of the {selected_part.lower()}.
        They answered YES to the following diagnostic questions:\n
        {"; ".join(yes_responses)}\n
        Based on this, provide the following:
        1. Suggested medical tests or diagnosis procedures (bulleted)
        2. Possible medical conditions (bulleted)
        3. Severity Level (Mild, Moderate, Severe) with a short reason
        4. Type of doctor to consult

        Structure it like this (with spacing):

        🧪 Required Tests and Diagnosis:

        ⚠️ Possible Medical Conditions:

        📊 Severity Level:

        👨‍⚕️ Doctor to Consult:
        """
        with st.spinner("Analyzing symptoms..."):
            try:
                result = model.generate_content(response_prompt).text
                for section in ["🧪 Required Tests and Diagnosis:", "⚠️ Possible Medical Conditions:", "📊 Severity Level:", "👨‍⚕️ Doctor to Consult:"]:
                    result = result.replace(section, f"<div class='section-title'>{section}</div>")

                st.markdown(result, unsafe_allow_html=True)
            except Exception as e:
                st.error("Diagnosis failed. Please try again later.")


import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="CareerSense AI Pro", layout="wide")

# ---------------------------
# GEMINI CONFIG
# ---------------------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    st.error("Gemini API Key not configured.")

# ---------------------------
# LOAD DATA
# ---------------------------
salary_df = pd.read_csv("global_tech_salary.csv")
salary_df["salary_lpa"] = (salary_df["salary_in_usd"] * 83) / 100000
salary_df["job_title"] = salary_df["job_title"].str.strip()

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.title("CareerSense AI")

menu = st.sidebar.radio(
    "Navigation",
    ["Home", "Career Analysis", "Compare Careers", "About"]
)


# ---------------------------
# HOME
# ---------------------------
if menu == "Home":
    st.markdown("""
    <h1 style='text-align:center;color:#00f5c4;'>CareerSense AI Pro</h1>
    <p style='text-align:center;'>AI-powered Career Intelligence Platform using Real Global Salary Data</p>
    """, unsafe_allow_html=True)

    st.image("https://images.unsplash.com/photo-1521737604893-d14cc237f11d", use_container_width=True)

    st.markdown("### What We Do")
    st.write("""
    - Recommend best career based on your skills
    - Show real salary insights
    - Analyze market strength
    - Generate AI-powered explanation
    - Create personalized learning roadmap
    """)

# ---------------------------
# CAREER ANALYSIS
# ---------------------------
elif menu == "Career Analysis":

    st.header("Analyze Your Career Path")

    skills_input = st.text_area("Your Skills (comma separated)")
    interests_input = st.text_area("Your Interests (comma separated)")

    if st.button("Analyze Now"):

        user_skills = [s.strip().lower() for s in skills_input.split(",")]
        user_interests = [i.strip().lower() for i in interests_input.split(",")]

        career_scores = {}

        for title in salary_df["job_title"].unique():
            score = 0
            title_lower = title.lower()

            for skill in user_skills:
                if skill in title_lower:
                    score += 2

            for interest in user_interests:
                if interest in title_lower:
                    score += 1

            career_scores[title] = score

        sorted_careers = sorted(career_scores.items(), key=lambda x: x[1], reverse=True)
        top_career = sorted_careers[0][0]

        st.success(f"Recommended Career: {top_career}")

        career_data = salary_df[salary_df["job_title"] == top_career]

        avg_salary = round(career_data["salary_lpa"].mean(), 2)
        min_salary = round(career_data["salary_lpa"].min(), 2)
        max_salary = round(career_data["salary_lpa"].max(), 2)

        demand_count = salary_df["job_title"].value_counts()[top_career]

        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Salary (LPA)", avg_salary)
        col2.metric("Role Frequency", demand_count)
        col3.metric("Salary Range", f"{min_salary}-{max_salary}")

        fig = px.histogram(career_data, x="salary_lpa", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # Gemini Explanation
        with st.spinner("Generating AI Insight..."):
            prompt = f"""
            Skills: {user_skills}
            Interests: {user_interests}
            Career: {top_career}
            Explain why this is suitable.
            """
            response = model.generate_content(prompt)
            explanation = response.text

        st.info(explanation)

        # ---------------------------
        # PDF GENERATION
        # ---------------------------
        if st.button("Download Career Report"):
            file_path = "career_report.pdf"
            doc = SimpleDocTemplate(file_path)
            elements = []

            styles = getSampleStyleSheet()
            elements.append(Paragraph(f"Career Report: {top_career}", styles["Title"]))
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph(f"Average Salary: {avg_salary} LPA", styles["Normal"]))
            elements.append(Paragraph(f"Market Frequency: {demand_count}", styles["Normal"]))
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph("AI Insight:", styles["Heading2"]))
            elements.append(Paragraph(explanation, styles["Normal"]))

            doc.build(elements)

            with open(file_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="Career_Report.pdf")

# ---------------------------
# COMPARE CAREERS
# ---------------------------
elif menu == "Compare Careers":

    st.header("Compare Two Careers")

    careers = salary_df["job_title"].unique()

    col1, col2 = st.columns(2)
    career1 = col1.selectbox("Select Career 1", careers)
    career2 = col2.selectbox("Select Career 2", careers)

    if st.button("Compare"):

        data1 = salary_df[salary_df["job_title"] == career1]
        data2 = salary_df[salary_df["job_title"] == career2]

        avg1 = round(data1["salary_lpa"].mean(), 2)
        avg2 = round(data2["salary_lpa"].mean(), 2)

        comparison_df = pd.DataFrame({
            "Career": [career1, career2],
            "Average Salary (LPA)": [avg1, avg2]
        })

        fig = px.bar(comparison_df,
                     x="Career",
                     y="Average Salary (LPA)",
                     template="plotly_dark",
                     title="Salary Comparison")

        st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# ABOUT
# ---------------------------
elif menu == "About":
    st.header("About CareerSense AI")
    st.write("""
    CareerSense AI is an AI-powered career intelligence platform
    built using real global salary datasets and generative AI.
    Designed for students and professionals to make data-driven
    career decisions.
    """)

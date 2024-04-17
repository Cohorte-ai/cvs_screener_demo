import streamlit as st
import os
import PyPDF2
from openai import OpenAI
import base64
from streamlit_pdf_viewer import pdf_viewer
import json
# Set your OpenAI API key
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# Function to load CVs from the specified directory
def load_cvs(directory):
    cvs = []
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(directory, filename)
            cv_text = extract_text_from_pdf(pdf_path)
            cvs.append({"path":pdf_path,"text":cv_text})
    return cvs

# Function to match job description with CVs and assign scores
def match_and_score(job_description, cvs):
    scores = []
    reasons = []
    for cv_text in cvs:
        # Construct prompt for GPT
        prompt = [
            {"role": "system", "content": f"                Please assess the provided CV against the given job description with extreme scrutiny. Assign a score (High/Medium/Low) only if the CV is a near-perfect match; otherwise, assign a very low score. Consider the following criteria meticulously:                                1. **Skills Matching**: Determine if the CV explicitly mentions and demonstrates proficiency in the key skills outlined in the job description.                2. **Qualifications Evaluation**: Verify if the candidate possesses the exact educational requirements, certifications, or licenses specified in the job description.                3. **Experience Relevance**: Evaluate the candidate's work experience to ensure it closely aligns with the roles and responsibilities described in the job description, with no deviations.                4. **Achievements and Accomplishments**: Look for exceptional achievements or recognitions in the CV that unequivocally prove the candidate's ability to excel in the role specified in the job description.                5. **Additional Factors**: Scrutinize any additional criteria mentioned in the job description, such as cultural fit, adaptability, or leadership potential, and ensure the CV surpasses expectations in all aspects.                6. **Overall Fit**: Demand nothing short of perfection in the alignment between the CV and the job description, encompassing every facet of skills, qualifications, experiences, achievements, and additional factors.                                Job Description:                {job_description}                                CV:                {cv_text}                                Provide a score (High/Medium/Low) only if the CV is exceptionally close to perfection. If there are any shortcomings or deviations, assign a very low score with detailed justifications. Be relentless in your assessment, allowing only for the utmost precision in matching.                                Follow this pattern meticulously:                                Response Pattern:                score - reason:            "},
            {"role": "user", "content": "Get score and reason and be very short and consise and maintain the format score - reason"}
        ]
        # Request GPT to generate score and reason
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            temperature=0.5)
        generated_text = response.choices[0].message.content
        print(generated_text)
        # Extract score and reason from generated text
        score_reason = generated_text.split("score - reason:")
        score_reason = score_reason[0].split("-")
        score = score_reason[0]
        reason = score_reason[1]
        scores.append(score)
        reasons.append(reason)
    
    return scores, reasons

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

# Streamlit app
def main():
    st.set_page_config(layout="wide")
    st.title("CV Matching App")
    st.markdown(
        """
        <style>
        .reportview-container {
            background: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Input field for job description
    job_description = st.text_area("Job Description")

    # Button to load CVs
    cvs_directory_path = "./cv"
    if st.button("Review All CVs"):
        if os.path.isdir(cvs_directory_path):
            cvs = load_cvs(cvs_directory_path)
            st.success(f"Successfully loaded {len(cvs)} CVs from {cvs_directory_path}")
            
            # Match and score job description with CVs
            scores, reasons = match_and_score(job_description, cvs)
            
            # Display scores and reasons
            st.subheader("Scores and Reasons")
            for i, (cv, score, reason) in enumerate(zip(cvs, scores, reasons)):
                st.write(f"CV {i+1}")
                # Display PDF viewer and extracted text in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("PDF Viewer:")
                    pdf_viewer(cv["path"])             
                with col2:
                    st.write(f"Score: {score}")
                    st.write(f"Reason: {reason}")
                
                st.write(f"---")
        else:
            st.error("Invalid directory path")

if __name__ == "__main__":
    main()

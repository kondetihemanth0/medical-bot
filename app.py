from flask import Flask, render_template, request
import google.generativeai as genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

# ==========================
# GEMINI API CONFIGURATION
# ==========================


API_KEY = os.getenv("GEMINI_API_KEY")
print("API KEY FOUND:", API_KEY is not None)

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# ==========================
# UPLOAD FOLDER
# ==========================
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==========================
# EMERGENCY KEYWORDS
# ==========================
emergency_words = [
    "chest pain",
    "difficulty breathing",
    "stroke",
    "unconscious",
    "severe bleeding",
    "heart attack",
    "suicidal thoughts"
]


@app.route("/", methods=["GET", "POST"])
def home():

    result = ""

    if request.method == "POST":

        symptoms = request.form.get("symptoms", "").strip()

        # ==========================
        # EMERGENCY DETECTION
        # ==========================
        for word in emergency_words:

            if word in symptoms.lower():

                result = """
⚠️ EMERGENCY WARNING

Your symptoms may indicate a serious medical condition.

Please seek immediate medical attention or contact emergency services immediately.

This AI assistant cannot provide emergency care.
"""

                return render_template(
                    "index.html",
                    result=result
                )

        # ==========================
        # FILE UPLOAD
        # ==========================
        uploaded_file = request.files.get("report")

        if uploaded_file and uploaded_file.filename != "":

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                uploaded_file.filename
            )

            uploaded_file.save(filepath)

            try:

                report_text = ""

                if uploaded_file.filename.lower().endswith(".pdf"):

                    reader = PdfReader(filepath)

                    for page in reader.pages:

                        text = page.extract_text()

                        if text:
                            report_text += text

                    prompt = f"""
You are an AI Medical Report Assistant.

Summarize the following medical report in simple patient-friendly language.

Medical Report:

{report_text}

Important:
- Educational purposes only.
- Do not provide a final diagnosis.
- Suggest consulting a healthcare professional.
"""

                    response = model.generate_content(prompt)

                    result = response.text

                else:

                    result = """
Unsupported file type.

Please upload a PDF medical report.
"""

            except Exception as e:

                print("FULL ERROR:", e)

                result = f"Error: {str(e)}"

            finally:

                if os.path.exists(filepath):
                    os.remove(filepath)

        # ==========================
        # SYMPTOM ANALYSIS
        # ==========================
        elif symptoms:

            prompt = f"""
You are a responsible AI Medical Assistant.

Rules:
1. Educational purposes only.
2. Do not provide a final diagnosis.
3. Explain symptoms in simple language.
4. Recommend consulting a doctor.
5. Mention possible causes.
6. Mention emergency warning signs if relevant.

Symptoms:

{symptoms}
"""

            try:

                response = model.generate_content(prompt)

                result = response.text

            except Exception as e:

                print("FULL ERROR:", e)

                result = f"Error: {str(e)}"

    return render_template(
        "index.html",
        result=result
    )


if __name__ == "__main__":
    app.run(debug=True)
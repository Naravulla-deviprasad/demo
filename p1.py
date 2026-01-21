import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
from dotenv import load_dotenv

# Load .env (safe API key handling)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing GOOGLE_API_KEY in environment (.env)")

# Configure environment variable for newer client
os.environ["GOOGLE_API_KEY"] = api_key

# Import newer genai client
from google import genai

# Instantiate client
client = genai.Client()

# Preferred models in order
PREFERRED_MODELS = [
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-pro-latest",
]

def choose_best_model():
    try:
        available = client.models.list()  # returns iterable of model metadata
    except Exception as e:
        # fallback hard-coded if list fails
        return "models/gemini-2.5-pro"

    # Build a set of names that support generateContent
    valid = {}
    for m in available:
        # some model objects expose supported methods differently; defensively check
        methods = getattr(m, "supported_generation_methods", None)
        name = getattr(m, "name", None)
        if not name:
            continue
        if methods and "generateContent" in methods:
            valid[name] = True

    for pref in PREFERRED_MODELS:
        if pref in valid:
            return pref

    # if none of preferred found, pick first that has generateContent
    if valid:
        return next(iter(valid.keys()))
    # last resort
    return "models/gemini-2.5-pro"

# Cache chosen model once per run
CHOSEN_MODEL = choose_best_model()

def get_diagnosis(symptoms):
    prompt = f"""You are a medical assistant. A user reports the following symptoms: {symptoms}

Provide:
1. A likely diagnosis (mention uncertainty if not definitive).
2. Suggested treatment (non-prescription/general advice; recommend seeing a doctor for serious concerns).
3. Precautions to take.
Format the answer with clear headings like:
Diagnosis:
Treatment:
Precautions:
"""
    try:
        response = client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=prompt
        )
        # Newer SDK: response.text should exist
        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text.strip()
        # fallback: try candidates
        candidates = getattr(response, "candidates", None)
        if candidates and len(candidates) > 0:
            first = candidates[0]
            content = getattr(first, "content", None) or getattr(first, "text", None)
            if isinstance(content, str):
                return content.strip()
        return "Received unexpected response format from Gemini API."
    except Exception as e:
        return f"Error contacting Gemini API:\n{e}"

# === GUI ===
def get_diagnosis(symptoms):
    prompt = f"""
You are a medical assistant. The user reports the following symptoms: {symptoms}

Your response must follow this exact format and structure, with no markdown, no asterisks, and no bold text. Use only plain text labels. Do not add extra commentary before or after.

Main Advice:
<one short paragraph in plain English summarizing the advice>

Priority Assessment:
<Low / Medium / High Priority based on urgency>

#checking/ testing the activity logs by commits.

Medical Assessment:
<likely diagnosis or suspected cause>

Recommended Treatment:
Oral Medication: <name or "Not recommended">
  Dosage: <dosage or "-">
  Frequency: <frequency or "-">
  Duration: <duration or "-">

Inhaler: <name or "Not recommended">
  Dosage: <dosage or "-">
  Frequency: <frequency or "-">
  Duration: <duration or "-">

Ointment: <name or "Not recommended">
  Dosage: <dosage or "-">
  Frequency: <frequency or "-">
  Duration: <duration or "-">

Important Precautions:
- <precaution 1>
- <precaution 2>
- <precaution 3>
(Include at least 3)

Follow-up Care:
- <follow-up step 1>
- <follow-up step 2>
- <follow-up step 3>
(Include at least 3)

Medical Disclaimer:
This is not a substitute for professional medical advice.
    """
    try:
        response = client.models.generate_content(
            model=CHOSEN_MODEL,
            contents=prompt
        )
        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text.strip()
        candidates = getattr(response, "candidates", None)
        if candidates and len(candidates) > 0:
            first = candidates[0]
            content = getattr(first, "content", None) or getattr(first, "text", None)
            if isinstance(content, str):
                return content.strip()
        return "Received unexpected response format from Gemini API."
    except Exception as e:
        return f"Error contacting Gemini API:\n{e}"


# Build GUI
root = tk.Tk()
root.title("AI Medical Assistant")
root.geometry("600x550")
root.resizable(False, False)

# Title
tk.Label(root, text="Symptom-Based Medical Assistant", font=("Helvetica", 16, "bold")).pack(pady=12)

# Symptoms input
frame_in = tk.Frame(root)
frame_in.pack(pady=6, fill="x", padx=10)
tk.Label(frame_in, text="Enter your symptoms:", font=("Arial", 12)).pack(anchor="w")
symptom_input = scrolledtext.ScrolledText(frame_in, height=5, width=70, wrap="word")
symptom_input.pack(pady=4)

def diagnose():
    symptoms = symptom_input.get("1.0", tk.END).strip()

    if not symptoms:
        messagebox.showwarning("Input Required", "Please enter your symptoms.")
        return

    result = get_diagnosis(symptoms)

    output_box.config(state=tk.NORMAL)
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, result)
    output_box.config(state=tk.DISABLED)


# Diagnose button
btn = tk.Button(root, text="Diagnose", command=diagnose, bg="#0f62fe", fg="black", font=("Arial", 12), padx=10, pady=5)
btn.pack(pady=10)

# Output area
frame_out = tk.Frame(root)
frame_out.pack(pady=6, fill="both", expand=True, padx=10)
tk.Label(frame_out, text="Result:", font=("Arial", 12)).pack(anchor="w")
output_box = scrolledtext.ScrolledText(frame_out, height=15, width=70, wrap="word", state=tk.DISABLED)
output_box.pack(pady=4)

# Footer / Disclaimer
disclaimer = (
    "Disclaimer: This tool provides informational suggestions and is not a substitute for professional medical advice. "
    "If symptoms are severe, worsening, or persistent, please consult a licensed healthcare provider."
)
tk.Label(root, text=disclaimer, font=("Arial", 8), wraplength=580, justify="center", fg="gray").pack(pady=8)

root.mainloop()


from flask import Flask, request, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from docx import Document
from PyPDF2 import PdfReader

app = Flask(__name__)

# Set file upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Extract text from DOCX
def extract_text_from_docx(filepath):
    doc = Document(filepath)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

# Extract text from PDF
def extract_text_from_pdf(filepath):
    reader = PdfReader(filepath)
    return "\n".join([page.extract_text() for page in reader.pages])

# Process file content for learning
def process_file_content(content):
    detect_new_words(content)  # Reuse detect_new_words function
    return "File content processed successfully!"

# Detect new words
def detect_new_words(user_input):
    conn = sqlite3.connect("learning_ai.db")
    cursor = conn.cursor()

    # Get all existing words in the vocabulary table
    cursor.execute("SELECT word FROM vocabulary")
    known_words = {row[0] for row in cursor.fetchall()}

    # Extract new words from the user input
    words = user_input.split()
    new_words = [word for word in words if word not in known_words]

    # Insert only new words into the database
    for word in new_words:
        try:
            cursor.execute(
                "INSERT INTO vocabulary (word, context) VALUES (?, ?)", (word, user_input)
            )
        except sqlite3.IntegrityError:
            pass  # Ignore duplicate entries
    conn.commit()
    conn.close()

# Save conversation to the database
def save_conversation(user_input, ai_response):
    conn = sqlite3.connect("learning_ai.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_input, ai_response) VALUES (?, ?)",
                   (user_input, ai_response))
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return "Welcome to the AI Chatbot! Use the /upload endpoint to upload files."

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Extract and process file content
            if filename.endswith(".docx"):
                content = extract_text_from_docx(filepath)
            elif filename.endswith(".pdf"):
                content = extract_text_from_pdf(filepath)
            elif filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                return jsonify({"error": "Unsupported file type"}), 400

            # Process the content
            process_result = process_file_content(content)
            return jsonify({"message": process_result}), 200

        return jsonify({"error": "File not allowed"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

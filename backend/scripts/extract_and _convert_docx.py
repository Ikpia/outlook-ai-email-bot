import os
import json
import zipfile
from docx import Document
import pypandoc

# Define Paths – adjust these paths as needed
ZIP_PATH = "backend/database/datasets/Template Email.zip"   # Path to your uploaded ZIP file
EXTRACT_DIR = "backend/database/datasets/extracted_templates/Template Email/Template Email"
OUTPUT_JSON_PATH = "backend/database/datasets/template_emails.json"

def extract_zip(zip_path, extract_dir):
    """Extracts all files from the ZIP archive to the specified directory."""
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"✅ Extracted all files to: {extract_dir}")

def read_docx_file(doc_path):
    """Reads a DOCX file and returns its text content."""
    try:
        doc = Document(doc_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        text = "\n".join(paragraphs)
        return text.strip()
    except Exception as e:
        print(f"Error reading DOCX {doc_path}: {e}")
        return ""

def read_doc_file(doc_path):
    """Converts a DOC file to plain text using pypandoc."""
    try:
        # pypandoc.convert_file converts the file and returns plain text
        output = pypandoc.convert_file(doc_path, 'plain')
        return output.strip()
    except Exception as e:
        print(f"Error converting DOC {doc_path}: {e}")
        return ""

def convert_docs_to_json(extract_dir, output_json):
    """Processes all DOC/DOCX files in the extract_dir and saves them as a JSON file."""
    all_templates = []
    files_processed = 0
    for filename in os.listdir(extract_dir):
        file_path = os.path.join(extract_dir, filename)
        text = ""
        if filename.lower().endswith(".docx"):
            print(f"Processing DOCX file: {filename}")
            text = read_docx_file(file_path)
        elif filename.lower().endswith(".doc"):
            print(f"Processing DOC file: {filename}")
            text = read_doc_file(file_path)
        else:
            print(f"Skipping unsupported file: {filename}")
            continue
        
        files_processed += 1
        
        if not text:
            print(f"⚠ No content found in {filename}")
            continue
        
        # Split text into lines and extract expected fields
        lines = text.split("\n")
        category = lines[0] if len(lines) > 0 else "Unknown"
        subject = lines[1] if len(lines) > 1 else "No Subject"
        body = "\n".join(lines[2:]) if len(lines) > 2 else "No Body"
        
        template = {
            "Category": category.strip(),
            "Subject": subject.strip(),
            "Body": body.strip()
        }
        all_templates.append(template)
    
    if files_processed == 0:
        print("⚠ No DOC or DOCX files found in the extracted directory.")
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_templates, f, indent=4)
    
    print(f"✅ Converted {len(all_templates)} templates and saved to: {output_json}")

if __name__ == "__main__":
    #extract_zip(ZIP_PATH, EXTRACT_DIR)
    convert_docs_to_json(EXTRACT_DIR, OUTPUT_JSON_PATH)
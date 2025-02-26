import os
import csv
import fitz  # PyMuPDF
from transformers import pipeline

# Disable OneDNN optimizations (for TensorFlow performance issues)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Load Mistral model from local storage
MODEL_PATH = r"D:\HuggingFace_Models\mistral-7b-instruct-v0.2"  # Update this to your local model path

try:
    paraphrase_pipeline = pipeline("text2text-generation", model=MODEL_PATH)
    print("Mistral model loaded successfully from local storage!")
except Exception as e:
    print(f"Error loading Mistral model: {e}")
    exit(1)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def paraphrase_text(text):
    """Paraphrase the input text using the local model."""
    try:
        paraphrased = paraphrase_pipeline(text, max_length=512, do_sample=True, truncation=True)
        return paraphrased[0]['generated_text']
    except Exception as e:
        print(f"Error during paraphrasing: {e}")
        return text  # Fallback to original text

def write_to_csv(data, output_csv):
    """Writes data to a CSV file in the format: Section, Title, Description."""
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Section", "Title", "Description"])
            writer.writerows(data)
        print(f"CSV file created successfully: {output_csv}")
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def main(pdf_path, output_csv):
    print(f"Processing PDF: {pdf_path}")
    pdf_text = extract_text_from_pdf(pdf_path)
    if not pdf_text.strip():
        print("No text extracted from the PDF. Exiting.")
        return

    paraphrased_text = paraphrase_text(pdf_text)

    # Simple logic to create sections (can be improved with regex or structured patterns)
    lines = paraphrased_text.split("\n")
    data = []

    for i, line in enumerate(lines):
        if line.strip():
            section = f"Section {i + 1}"
            title = line[:50]  # First 50 characters as a title
            description = line
            data.append([section, title, description])

    write_to_csv(data, output_csv)

if __name__ == "__main__":
    pdf_path = r"C:\Users\HP\Downloads\BNS list_removed_removed.pdf"  # Change to your PDF path
    output_csv = "output.csv"
    main(pdf_path, output_csv)

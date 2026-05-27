import docx

file_path = r"C:\Users\21628\Downloads\Modele de redaction du rapport.docx"
try:
    doc = docx.Document(file_path)
    print("Document loaded successfully.")
    print("--- Document Content ---")
    for para in doc.paragraphs:
        if para.text.strip():
            style_name = para.style.name
            print(f"[{style_name}] {para.text}")
except Exception as e:
    print(f"Error reading docx: {e}")

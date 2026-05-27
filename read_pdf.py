import PyPDF2
import re

file_path = r"C:\Users\21628\Downloads\rapport-20pfe-2011-140215030148-phpapp01.pdf"
out_path = r"c:\Users\21628\Downloads\farm-ai-project-main (2)\farm-ai-project-main\toc_extracted.txt"

try:
    with open(file_path, "rb") as f, open(out_path, "w", encoding="utf-8") as out:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)
        
        # We will extract pages 1 to 20 as TOC is usually there
        text_content = ""
        for i in range(min(20, num_pages)):
            text_content += reader.pages[i].extract_text() + "\n"
        
        # Look for lines that might be TOC entries
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                out.write(line + "\n")
                
except Exception as e:
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(f"Error: {e}")

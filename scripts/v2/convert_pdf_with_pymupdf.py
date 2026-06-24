"""
Convert PDF to images using PyMuPDF (fitz)
"""
import os
import fitz  # PyMuPDF
from PIL import Image

# PDF path
pdf_path = r"src_v2\Reach Rate Calculator\ART Presentation (Jan - April) 2026.pdf"
output_dir = r"temp_pdf_images"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

print(f"Converting PDF: {pdf_path}")
print(f"Output directory: {output_dir}")

try:
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    print(f"\nPDF has {len(pdf_document)} pages")
    
    # Convert each page to an image
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # Render page to an image (matrix for higher resolution)
        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Save as PNG
        output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(output_path)
        
        print(f"Saved: page_{page_num + 1}.png ({pix.width}x{pix.height})")
    
    pdf_document.close()
    print(f"\nAll {len(pdf_document)} pages saved to: {output_dir}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Made with Bob

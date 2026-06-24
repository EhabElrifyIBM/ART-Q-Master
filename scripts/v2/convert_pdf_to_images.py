"""
Convert PDF to images for visual analysis
"""
import os
from pdf2image import convert_from_path
from pathlib import Path

# PDF path
pdf_path = r"src_v2\Reach Rate Calculator\ART Presentation (Jan - April) 2026.pdf"
output_dir = r"temp_pdf_images"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

print(f"Converting PDF: {pdf_path}")
print(f"Output directory: {output_dir}")

try:
    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=200)
    
    print(f"\nSuccessfully converted {len(images)} pages")
    
    # Save each page as an image
    for i, image in enumerate(images, start=1):
        output_path = os.path.join(output_dir, f"page_{i}.png")
        image.save(output_path, "PNG")
        print(f"Saved: {output_path}")
        
    print(f"\nAll pages saved to: {output_dir}")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nNote: pdf2image requires poppler. On Windows, you may need to:")
    print("1. Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
    print("2. Extract and add the 'bin' folder to your PATH")
    print("3. Or specify poppler_path in convert_from_path()")

# Made with Bob

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

def text_to_pdf(input_text_file, output_pdf_file=None):
    """
    Convert a text file to PDF
    
    Args:
        input_text_file (str): Path to input text file
        output_pdf_file (str, optional): Path to output PDF file. If None, will use same name as input with .pdf extension.
        
    Returns:
        str: Path to the created PDF file
    """
    if not os.path.exists(input_text_file):
        raise FileNotFoundError(f"Input file not found: {input_text_file}")
    
    # If output file not specified, use same name with .pdf extension
    if output_pdf_file is None:
        output_pdf_file = os.path.splitext(input_text_file)[0] + ".pdf"
    
    # Read the text file
    with open(input_text_file, 'r', encoding='utf-8') as file:
        text_content = file.read()
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_pdf_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Normal_LEFT',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontName='Courier',
        fontSize=11,
        leading=14
    ))
    
    title_style = styles['Title']
    normal_style = styles['Normal_LEFT']
    
    # Process the text content
    lines = text_content.split('\n')
    
    # Build the PDF content
    content = []
    
    # Add title (first line)
    if lines:
        content.append(Paragraph(lines[0], title_style))
        content.append(Spacer(1, 12))
    
    # Split the content into paragraphs
    current_paragraph = ""
    
    for line in lines[1:]:
        # If the line is empty, it's a paragraph break
        if line.strip() == "":
            if current_paragraph:
                content.append(Paragraph(current_paragraph, normal_style))
                content.append(Spacer(1, 10))
                current_paragraph = ""
        else:
            if current_paragraph:
                current_paragraph += " " + line
            else:
                current_paragraph = line
    
    # Add the last paragraph if any
    if current_paragraph:
        content.append(Paragraph(current_paragraph, normal_style))
    
    # Build the PDF
    doc.build(content)
    
    return output_pdf_file

if __name__ == "__main__":
    # If run directly, convert example_scheme.txt to PDF
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "example_scheme.txt")
    
    if os.path.exists(input_file):
        output_file = text_to_pdf(input_file)
        print(f"Successfully converted {input_file} to {output_file}")
    else:
        print(f"File not found: {input_file}")
        print("Please make sure example_scheme.txt exists in the same directory as this script.") 
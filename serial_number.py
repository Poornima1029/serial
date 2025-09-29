import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import pandas as pd
import io
import math
import os

# Register custom fonts if .ttf files are available
def register_custom_fonts():
    fonts = {}

    # 1. Register fonts from "fonts" folder (if exists)
    font_folder = "fonts"
    if os.path.exists(font_folder):
        for file in os.listdir(font_folder):
            if file.endswith(".ttf"):
                font_name = os.path.splitext(file)[0]
                pdfmetrics.registerFont(TTFont(font_name, os.path.join(font_folder, file)))
                fonts[font_name] = font_name

    # 2. Check if ArialNarrow.ttf is in the same folder as this script
    arial_local = "ArialNarrow.ttf"
    if os.path.exists(arial_local):
        pdfmetrics.registerFont(TTFont("Arial-Narrow", arial_local))
        fonts["Arial-Narrow"] = "Arial-Narrow"

    # 3. Add built-in fonts
    fonts.update({
        "Helvetica": "Helvetica",
        "Times-Roman": "Times-Roman",
        "Courier": "Courier"
    })

    return fonts

# Helper: draw text with letter spacing
def draw_text(c, x, y, text, font_name, font_size, letter_spacing=0):
    text_obj = c.beginText(x, y)
    text_obj.setFont(font_name, font_size)
    if letter_spacing != 0:
        text_obj.setCharSpace(letter_spacing)
    text_obj.textLine(text)
    c.drawText(text_obj)

# Generate PDF
def generate_pdf(prefix, start, end, batch_code, mfg_date, rows, cols, font_size, font_name, margin_x=50, margin_y=50, letter_spacing=0):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    usable_width = width - 2 * margin_x
    usable_height = height - 2 * margin_y

    x_spacing = usable_width / cols
    y_spacing = usable_height / rows

    total_serials = end - start + 1
    serial_number = start
    total_per_page = rows * cols
    total_pages = math.ceil(total_serials / total_per_page)

    for page in range(total_pages):
        for col in range(cols):
            for row in range(rows):
                if serial_number > end:
                    break
                x = margin_x + col * x_spacing
                y = height - margin_y - row * y_spacing + (y_spacing - font_size*3)/2

                # Draw 3 lines with letter spacing
                draw_text(c, x, y, batch_code, font_name, font_size, letter_spacing)
                draw_text(c, x, y - font_size - 2, f"{prefix}{serial_number}", font_name, font_size, letter_spacing)
                draw_text(c, x, y - 2*(font_size + 2), mfg_date, font_name, font_size, letter_spacing)

                serial_number += 1
            if serial_number > end:
                break
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# Generate preview for Streamlit
def generate_preview(prefix, start, end, batch_code, mfg_date, preview_start, preview_count):
    preview_list = []
    for i in range(preview_start, min(end + 1, preview_start + preview_count)):
        preview_list.append({
            "Batch Code": batch_code,
            "Serial Number": f"{prefix}{i}",
            "Manufacturing Date": mfg_date
        })
    return pd.DataFrame(preview_list)

# Streamlit UI
st.title("📄 Circuit Board Serial Number PDF Generator")

prefix = st.text_input("Prefix (e.g., A296/)", "A296/")
start = st.number_input("Starting number", min_value=0, value=12081)
end = st.number_input("Ending number", min_value=0, value=12090)
batch_code = st.text_input("Batch Code", "H03 8002")
mfg_date = st.text_input("Manufacturing Date", "Mfg: SEP - 2025")

rows = st.number_input("Rows per page", min_value=1, value=7)
cols = st.number_input("Columns per page", min_value=1, value=3)
font_size = st.number_input("Font size", min_value=6, value=12)

# Font selection
fonts = register_custom_fonts()
default_font = "Arial-Narrow" if "Arial-Narrow" in fonts else "Helvetica"

font_name = st.selectbox(
    "Font Style",
    options=list(fonts.keys()),
    index=list(fonts.keys()).index(default_font)
)

# Letter spacing
letter_spacing = st.number_input("Letter spacing (tracking)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

# Preview options
st.subheader("🔍 Preview Options")
preview_start = st.number_input("Preview starting number", min_value=start, max_value=end, value=start)
preview_count = st.number_input("How many numbers to preview?", min_value=1, value=3)

if st.button("Preview Serial Numbers"):
    preview_df = generate_preview(prefix, start, end, batch_code, mfg_date, preview_start, preview_count)
    st.subheader(f"Preview of Serial Numbers ({preview_start} → {preview_start + preview_count - 1}):")
    st.dataframe(preview_df, use_container_width=True)

if st.button("Generate PDF"):
    pdf_buffer = generate_pdf(prefix, start, end, batch_code, mfg_date, rows, cols, font_size, font_name, letter_spacing=letter_spacing)
    st.download_button(
        label="📥 Download PDF",
        data=pdf_buffer,
        file_name="serial_numbers.pdf",
        mime="application/pdf"
    )
    st.success(f"✅ Generated serial numbers from {start} to {end}")


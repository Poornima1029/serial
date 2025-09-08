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
    font_folder = "fonts"  # folder containing TTF files
    if os.path.exists(font_folder):
        for file in os.listdir(font_folder):
            if file.endswith(".ttf"):
                font_name = os.path.splitext(file)[0]
                pdfmetrics.registerFont(TTFont(font_name, os.path.join(font_folder, file)))
                fonts[font_name] = font_name
    # Add built-in fonts
    fonts.update({
        "Helvetica": "Helvetica",
        "Times-Roman": "Times-Roman",
        "Courier": "Courier"
    })
    return fonts

# Generate PDF
def generate_pdf(prefix, start, end, batch_code, mfg_date, rows, cols, font_size, font_name, margin_x=50, margin_y=50):
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

                # Draw 3 lines
                c.setFont(font_name, font_size)
                c.drawString(x, y, batch_code)
                c.drawString(x, y - font_size - 2, f"{prefix}{serial_number}")
                c.drawString(x, y - 2*(font_size + 2), mfg_date)

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
font_name = st.selectbox("Font Style", options=list(fonts.keys()), index=list(fonts.keys()).index("Helvetica"))

# Preview options
st.subheader("🔍 Preview Options")
preview_start = st.number_input("Preview starting number", min_value=start, max_value=end, value=start)
preview_count = st.number_input("How many numbers to preview?", min_value=1, value=3)

if st.button("Preview Serial Numbers"):
    preview_df = generate_preview(prefix, start, end, batch_code, mfg_date, preview_start, preview_count)
    st.subheader(f"Preview of Serial Numbers ({preview_start} → {preview_start + preview_count - 1}):")
    st.dataframe(preview_df, use_container_width=True)

if st.button("Generate PDF"):
    pdf_buffer = generate_pdf(prefix, start, end, batch_code, mfg_date, rows, cols, font_size, font_name)
    st.download_button(
        label="📥 Download PDF",
        data=pdf_buffer,
        file_name="serial_numbers.pdf",
        mime="application/pdf"
    )
    st.success(f"✅ Generated serial numbers from {start} to {end}")

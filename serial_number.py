import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import pandas as pd
import io
import math

# Register custom fonts if .ttf files are available
def register_custom_fonts():
    fonts = {}

    # 1. Register fonts from "fonts" folder (if exists)
    font_folder = "fonts"
    if os.path.exists(font_folder):
        for file in os.listdir(font_folder):
            if file.endswith(".ttf"):
                font_name = os.path.splitext(file)[0]
                try:
                    pdfmetrics.registerFont(TTFont(font_name, os.path.join(font_folder, file)))
                    fonts[font_name] = font_name
                except:
                    pass

    # 2. Check if ArialNarrow.ttf is in the same folder as this script
    arial_local = "ArialNarrow.ttf"
    if os.path.exists(arial_local):
        try:
            pdfmetrics.registerFont(TTFont("Arial-Narrow", arial_local))
            fonts["Arial-Narrow"] = "Arial-Narrow"
        except:
            pass

    # 3. Add built-in fonts
    fonts.update({
        "Helvetica": "Helvetica",
        "Times-Roman": "Times-Roman",
        "Courier": "Courier"
    })

    return fonts

# Helper: draw text with safe fallback
def draw_text(c, x, y, text, font_name, font_size, letter_spacing=0):
    text_obj = c.beginText(x, y)
    try:
        text_obj.setFont(font_name, font_size)
    except:
        # fallback if font fails
        text_obj.setFont("Helvetica", font_size)

    if letter_spacing != 0:
        text_obj.setCharSpace(letter_spacing)

    text_obj.textLine(text)
    c.drawText(text_obj)

# Generate PDF
def generate_pdf_special_pattern(prefix, start, end, batch_code, mfg_date,
                                 rows, cols, font_size, font_name,
                                 margin_x=40, margin_y=40, letter_spacing=0):

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    usable_width = width - 2 * margin_x
    usable_height = height - 2 * margin_y

    x_spacing = usable_width / cols
    y_spacing = usable_height / rows

    total_per_page = rows * cols
    total_numbers = end - start + 1
    total_pages = math.ceil(total_numbers / total_per_page)

    current_start = start

    for page in range(total_pages):

        for col in range(cols):
            for row in range(rows):

                number = current_start + (row * cols) + col

                if number > end:
                    break

                x = margin_x + col * x_spacing
                y = height - margin_y - row * y_spacing + (y_spacing - font_size*3)/2

                draw_text(c, x, y, batch_code, font_name, font_size, letter_spacing)
                draw_text(c, x, y - font_size - 2,
                          f"{prefix}{number}",
                          font_name, font_size, letter_spacing)
                draw_text(c, x, y - 2*(font_size + 2),
                          mfg_date,
                          font_name, font_size, letter_spacing)

        current_start += total_per_page
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

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("📄 Circuit Board Serial Number PDF Generator")

prefix = st.text_input("Prefix (e.g., A296/)", "SL.NO : ")
start = st.number_input("Starting number", min_value=0, value=0)
end = st.number_input("Ending number", min_value=0, value=0)
batch_code = st.text_input("Batch Code", "")
mfg_date = st.text_input("Manufacturing Date", "MFG : SEP - 2025")

rows = st.number_input("Rows per page", min_value=1, value=7)
cols = st.number_input("Columns per page", min_value=1, value=3)
font_size = st.number_input("Font size", min_value=6, value=12)

# Font selection
fonts = register_custom_fonts()

# Always include Arial-Narrow in dropdown
if "Arial-Narrow" not in fonts:
    fonts["Arial-Narrow"] = "Arial-Narrow"

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
    pdf_buffer = generate_pdf_special_pattern(prefix, start, end, batch_code, mfg_date, rows, cols, font_size, font_name, letter_spacing=letter_spacing)
    st.download_button(
        label="📥 Download PDF",
        data=pdf_buffer,
        file_name="serial_numbers.pdf",
        mime="application/pdf"
    )
    st.success(f"✅ Generated serial numbers from {start} to {end}")

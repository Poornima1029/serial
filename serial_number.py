import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# ------------------------------
# Register custom fonts
# ------------------------------
def register_custom_fonts():
    font_path = os.path.join(os.path.dirname(__file__), "ArialNarrow.ttf")
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("ArialNarrow", font_path))
            print("✅ Arial Narrow registered successfully")
        except Exception as e:
            print("⚠️ Could not register Arial Narrow:", e)
    else:
        print("⚠️ ArialNarrow.ttf not found in project folder")

# Call registration
register_custom_fonts()

# ------------------------------
# Streamlit App
# ------------------------------
st.title("PDF Generator with Custom Fonts")

# Font dropdown
font_styles = ["Helvetica", "Times-Roman", "Courier"]
registered_fonts = pdfmetrics.getRegisteredFontNames()

if "ArialNarrow" in registered_fonts:
    font_styles.append("ArialNarrow")

selected_font = st.selectbox("Select Font Style", font_styles, index=0)

# Text input
text_input = st.text_input("Enter text to add in PDF", "Hello World!")

# Button
if st.button("Generate PDF"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    # Apply selected font
    try:
        c.setFont(selected_font, 14)
    except:
        st.warning(f"⚠️ Font '{selected_font}' could not be applied. Falling back to Helvetica.")
        c.setFont("Helvetica", 14)

    # Draw text
    c.drawString(100, 750, text_input)
    c.save()

    buffer.seek(0)

    st.download_button(
        label="📥 Download PDF",
        data=buffer,
        file_name="output.pdf",
        mime="application/pdf"
    )



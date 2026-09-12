import streamlit as st
import csv
import io
import os
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 🎨 ID CARD DESIGN FUNCTION
# ==========================================
def generate_id_card(name, roll, course):
    # 1. Blank Card Canvas (Size: 400x600)
    card = Image.new("RGB", (400, 600), "#FFFFFF")
    draw = ImageDraw.Draw(card)
    
    primary_color = "#0052cc"  # Blue Header
    text_color = "#333333"     # Dark Text
    
    # 2. Header
    draw.rectangle([(0, 0), (400, 100)], fill=primary_color)
    
    # 3. Fonts Load
    try:
        font_header = ImageFont.truetype("arial.ttf", 26)
        font_name = ImageFont.truetype("arial.ttf", 28)
        font_text = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_header = font_name = font_text = ImageFont.load_default()

    # 4. Text and Shapes
    draw.text((200, 50), "UNIVERSAL INSTITUTE", fill="#FFFFFF", font=font_header, anchor="mm")
    draw.ellipse([(140, 140), (260, 260)], fill="#E1E4E8", outline=primary_color, width=3)
    draw.text((200, 200), "👤", fill="#586069", font=font_name, anchor="mm")
    
    draw.text((200, 310), name.upper(), fill=text_color, font=font_name, anchor="mm")
    draw.text((60, 380), f"Roll No:  {roll}", fill=text_color, font=font_text)
    draw.text((60, 420), f"Course:   {course}", fill=text_color, font=font_text)
    draw.text((60, 460), f"Validity: 2026 - 2027", fill=text_color, font=font_text)
    
    # 5. Footer
    draw.rectangle([(0, 550), (400, 600)], fill="#333333")
    draw.text((200, 575), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    # Image ko memory me save karke return karna
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# ==========================================
# 🌐 STREAMLIT ADMIN PANEL WEB UI
# ==========================================
st.set_page_config(page_title="Admin Panel - ID Generator", page_icon="🛡️")

st.title("🛡️ Admin Panel - Batch ID Card Generator")
st.write("GitHub/Streamlit ke zariye automatic ID card banayein.")

# 1. File Upload Component
uploaded_file = st.file_uploader("Apni Student Data CSV File Upload Karein", type=["csv"])

if uploaded_file is not None:
    # CSV file read karna
    file_contents = uploaded_file.getvalue().decode("utf-8").splitlines()
    reader = csv.DictReader(file_contents)
    
    st.success("File upload ho gayi! Niche aapke ID cards generate ho rahe hain:")
    
    # Har ek student ke liye card process karna
    for row in reader:
        name = row.get('Name', row.get('name', 'Unknown'))
        roll = row.get('Roll', row.get('roll', '000'))
        course = row.get('Course', row.get('course', 'N/A'))
        
        # ID Card ka photo generate karna memory me
        card_image_bytes = generate_id_card(name, roll, course)
        
        # Web page par live dikhane ke liye box
        with st.container():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader(f"👤 {name}")
                st.write(f"**Roll:** {roll} | **Course:** {course}")
            with col2:
                # Download Button aur Preview
                st.image(card_image_bytes, width=150)
                st.download_button(
                    label="📥 Download Card",
                    data=card_image_bytes,
                    file_name=f"{roll}_{name.replace(' ', '_')}.png",
                    mime="image/png"
                )
            st.markdown("---")

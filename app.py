import streamlit as st
import csv
import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🎨 HIGH-QUALITY DYNAMIC ID CARD ENGINE
# ==========================================
def generate_id_card(name, roll, course, photo_file, bg_color, text_color, header_title):
    # Blank White Card Canvas (Standard Size: 400x600)
    card = Image.new("RGB", (400, 600), "#FFFFFF")
    draw = ImageDraw.Draw(card)
    
    # 1. Custom Background Header
    draw.rectangle([(0, 0), (400, 110)], fill=bg_color)
    
    # Fonts load karna (Fallback to default if arial is missing)
    try:
        font_header = ImageFont.truetype("arial.ttf", 24)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_header = font_name = font_text = ImageFont.load_default()

    # 2. Dynamic Header Text
    draw.text((200, 55), header_title.upper(), fill="#FFFFFF", font=font_header, anchor="mm")
    
    # 3. Student Photo Process (Agar student ne upload ki hai)
    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            # Photo ko passport size (120x140) me resize aur crop karna
            student_img = ImageOps.fit(student_img, (120, 140), Image.Resampling.LANCZOS)
            # Photo ko card ke center me paste karna
            card.paste(student_img, (140, 140))
            # Border draw karna photo ke charo taraf
            draw.rectangle([(140, 140), (260, 280)], outline=bg_color, width=3)
        except Exception:
            # Dropback to default avatar if image fails
            draw.rectangle([(140, 140), (260, 280)], fill="#E1E4E8", outline=bg_color, width=2)
            draw.text((200, 210), "PHOTO ERROR", fill="#586069", font=font_text, anchor="mm")
    else:
        # Default placeholder icon agar photo nahi hai
        draw.rectangle([(140, 140), (260, 280)], fill="#E1E4E8", outline=bg_color, width=2)
        draw.text((200, 210), "[ PHOTO ]", fill="#586069", font=font_text, anchor="mm")
    
    # 4. Student Text Details
    draw.text((200, 320), name.upper(), fill=text_color, font=font_name, anchor="mm")
    
    # Info Labels
    draw.text((60, 380), f"Roll No:", fill=bg_color, font=font_text)
    draw.text((160, 380), f"{roll}", fill=text_color, font=font_text)
    
    draw.text((60, 420), f"Course:", fill=bg_color, font=font_text)
    draw.text((160, 420), f"{course}", fill=text_color, font=font_text)
    
    draw.text((60, 460), f"Validity:", fill=bg_color, font=font_text)
    draw.text((160, 460), f"2026 - 2027", fill=text_color, font=font_text)
    
    # 5. Dark Footer
    draw.rectangle([(0, 540), (400, 600)], fill="#222222")
    draw.text((200, 570), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    # Save Image to byte buffer
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 💾 APP STATE MANAGEMENT (DATABASE PRESERVER)
# ==========================================
if 'student_db' not in st.session_state:
    st.session_state['student_db'] = []  # Excel/CSV ka data store karne ke liye

# Default Design Configuration Settings
if 'bg_color' not in st.session_state:
    st.session_state['bg_color'] = "#0052cc"
if 'text_color' not in st.session_state:
    st.session_state['text_color'] = "#333333"
if 'header_title' not in st.session_state:
    st.session_state['header_title'] = "UNIVERSAL INSTITUTE"


# ==========================================
# 🌐 MAIN ROUTER NAVIGATION UI
# ==========================================
st.set_page_config(page_title="Smart ID Generator", page_icon="🪪", layout="centered")

# Top Navigation Tabs
app_mode = st.sidebar.radio("Navigation Menu", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ MODE 1: ADMIN PANEL (WITH PASSWORD & DESIGNER)
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.title("🛡️ Admin Security Control Center")
    
    # Password Input Mask
    password_input = st.text_input("Admin Password Likhein", type="password")
    
    if password_input == "daminimylove":
        st.success("🔓 Access Granted! Welcome Admin.")
        
        st.markdown("---")
        st.subheader("🎨 Live Card Design Settings")
        
        # Design configuration tools
        col1, col2 = st.columns(2)
        with col1:
            st.session_state['header_title'] = st.text_input("Institute / School Name", st.session_state['header_title'])
            st.session_state['bg_color'] = st.color_picker("Header Theme Color (Primary)", st.session_state['bg_color'])
        with col2:
            st.session_state['text_color'] = st.color_picker("Text Color (Secondary)", st.session_state['text_color'])
            st.write("\n")
            st.info("💡 Jo color aap yahan chunenge, wahi same look student ko unke portal par dikhega.")

        st.markdown("---")
        st.subheader("📊 Bulk Student Data Importer")
        uploaded_csv = st.file_uploader("Students ki Data CSV File Upload Karein", type=["csv"])
        
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8").splitlines()
            reader = csv.DictReader(file_contents)
            
            # Reset and fill the state database
            st.session_state['student_db'] = []
            for row in reader:
                st.session_state['student_db'].append({
                    "name": row.get('Name', row.get('name', 'Unknown')),
                    "roll": row.get('Roll', row.get('roll', '000')).strip(),
                    "course": row.get('Course', row.get('course', 'N/A'))
                })
            st.success(f"📦 Database updated successfully! Total {len(st.session_state['student_db'])} students records loaded.")
            
    elif password_input != "":
        st.error("❌ Galat Password! Access Denied.")

# ------------------------------------------
# 🎓 MODE 2: STUDENT PORTAL (SELF-SERVICE GENERATOR)
# ------------------------------------------
else:
    st.title("🎓 Student Smart Self-Service Portal")
    st.write("Apna Roll Number dalein, Photo upload karein aur ID Card download karein.")
    
    if not st.session_state['student_db']:
        st.warning("⚠️ Abhi Admin ne koi data upload nahi kiya hai. Kripya pehle Admin Panel me jaakar CSV parse karein.")
    else:
        # Student Roll Number Verify Field
        search_roll = st.text_input("Apna Roll Number Type Karein:", placeholder="Eg. 101, 102...").strip()
        
        if search_roll:
            # Database search query logic
            student_match = next((s for s in st.session_state['student_db'] if s['roll'] == search_roll), None)
            
            if student_match:
                st.success(f"🎯 Record Found! Hello, {student_match['name']}")
                
                # Render profile fields info
                st.info(f"📋 **Verified Course Details:** {student_match['course']}")
                
                # Student photo upload handler trigger
                student_photo = st.file_uploader("Apni Passport Size Photo Upload Karein (JPG/PNG)", type=["jpg", "jpeg", "png"])
                
                if student_photo is not None:
                    st.write("### 🪪 Aapka Generated ID Card View:")
                    
                    # Call generator using synced Admin variables
                    final_card_bytes = generate_id_card(
                        name=student_match['name'],
                        roll=student_match['roll'],
                        course=student_match['course'],
                        photo_file=student_photo,
                        bg_color=st.session_state['bg_color'],
                        text_color=st.session_state['text_color'],
                        header_title=st.session_state['header_title']
                    )
                    
                    # Split grid layout structure for preview and action
                    col_preview, col_action = st.columns([2, 1])
                    with col_preview:
                        st.image(final_card_bytes, width=280)
                    with col_action:
                        st.write("")
                        st.write("")
                        st.download_button(
                            label="📥 Download ID Card",
                            data=final_card_bytes,
                            file_name=f"ID_{student_match['roll']}_{student_match['name'].replace(' ', '_')}.png",
                            mime="image/png"
                        )
                        st.balloons()
            else:
                st.error("🔍 Yeh Roll Number server records me nahi mila. Kripya apna sahi Roll Number dalein.")

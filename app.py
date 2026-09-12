import streamlit as st
import csv
import io
import sqlite3
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🗄️ LOCAL DATABASE SETUP (SQLITE)
# ==========================================
# Yeh function database aur table banata hai agar pehle se na bani ho
def init_db():
    conn = sqlite3.connect('students_database.db')
    cursor = conn.cursor()
    # Student records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            name TEXT,
            course TEXT
        )
    ''')
    # Admin layout settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Database se settings load karne ke liye helper function
def get_setting(key, default):
    conn = sqlite3.connect('students_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

# Settings ko save/update karne ke liye function
def save_setting(key, value):
    conn = sqlite3.connect('students_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

# Database initialize karein
init_db()

# ==========================================
# 🎨 ID CARD DESIGN SYSTEM
# ==========================================
def generate_id_card(name, roll, course, photo_file, bg_color, text_color, header_title):
    card = Image.new("RGB", (400, 600), "#FFFFFF")
    draw = ImageDraw.Draw(card)
    
    # Header Layout Area
    draw.rectangle([(0, 0), (400, 110)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 24)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_header = font_name = font_text = ImageFont.load_default()

    draw.text((200, 55), header_title.upper(), fill="#FFFFFF", font=font_header, anchor="mm")
    
    # Photo Frame Process
    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.fit(student_img, (120, 140), Image.Resampling.LANCZOS)
            card.paste(student_img, (140, 140))
            draw.rectangle([(140, 140), (260, 280)], outline=bg_color, width=3)
        except Exception:
            draw.rectangle([(140, 140), (260, 280)], fill="#E1E4E8", outline=bg_color, width=2)
            draw.text((200, 210), "IMAGE ERROR", fill="#586069", font=font_text, anchor="mm")
    else:
        draw.rectangle([(140, 140), (260, 280)], fill="#E1E4E8", outline=bg_color, width=2)
        draw.text((200, 210), "[ PHOTO ]", fill="#586069", font=font_text, anchor="mm")
    
    # Profile Text Fields
    draw.text((200, 320), str(name).upper(), fill=text_color, font=font_name, anchor="mm")
    draw.text((60, 380), "Roll No:", fill=bg_color, font=font_text)
    draw.text((160, 380), f"{roll}", fill=text_color, font=font_text)
    draw.text((60, 420), "Course:", fill=bg_color, font=font_text)
    draw.text((160, 420), f"{course}", fill=text_color, font=font_text)
    draw.text((60, 460), "Validity:", fill=bg_color, font=font_text)
    draw.text((160, 460), "2026 - 2027", fill=text_color, font=font_text)
    
    # Card Footer Section
    draw.rectangle([(0, 540), (400, 600)], fill="#222222")
    draw.text((200, 570), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 🌐 MAIN WEB INTERFACE UI
# ==========================================
st.set_page_config(page_title="Permanent Local DB ID System", page_icon="🪪")

# Persistent state configurations loading dynamically from DB
db_title = get_setting('header_title', 'UNIVERSAL INSTITUTE')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#333333')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ SYSTEM SECTION 1: ADMIN CONTROL PANEL
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")
    
    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved!")
        
        st.subheader("🎨 Custom Design Control")
        new_title = st.text_input("Institute Name", db_title)
        new_bg = st.color_picker("Theme Color", db_bg)
        new_text = st.color_picker("Text Color", db_text)
        
        # Agar admin layout settings badalta hai toh DB me update karein
        if new_title != db_title or new_bg != db_bg or new_text != db_text:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            st.rerun()

        st.markdown("---")
        st.subheader("📦 Database Management Tracker")
        
        uploaded_csv = st.file_uploader("Upload Student Database (CSV File)", type=["csv"])
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8").splitlines()
            reader = csv.DictReader(file_contents)
            
            # Database connection open karke data push karna
            conn = sqlite3.connect('students_database.db')
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                r_roll = row.get('Roll', row.get('roll', '000')).strip()
                r_name = row.get('Name', row.get('name', 'Unknown'))
                r_course = row.get('Course', row.get('course', 'N/A'))
                
                # INSERT OR REPLACE taaki duplicate roll no par data overwrite/update ho jaye
                cursor.execute('INSERT OR REPLACE INTO students (roll, name, course) VALUES (?, ?, ?)', (r_roll, r_name, r_course))
                count += 1
                
            conn.commit()
            conn.close()
            st.success(f"✅ Database updated successfully! Total {count} records added/updated permanently.")

        # Data Delete karne ka manual control option
        st.write("")
        if st.button("🗑️ Clear Entire Database Records"):
            conn = sqlite3.connect('students_database.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM students')
            conn.commit()
            conn.close()
            st.warning("🚨 Saara student data permanent database se delete kar diya gaya hai!")
            
    elif admin_pass != "":
        st.error("❌ Galat Password!")

# ------------------------------------------
# 🎓 SYSTEM SECTION 2: STUDENT LIVE PORTAL
# ------------------------------------------
else:
    st.header("🎓 Student Card Download Counter")
    
    # Check karein ki database me data maujood hai ya nahi
    conn = sqlite3.connect('students_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    db_count = cursor.fetchone()[0]
    conn.close()
    
    if db_count == 0:
        st.warning("⚠️ Configuration Missing! Admin ne abhi tak database me koi student record upload nahi kiya hai.")
    else:
        search_roll = st.text_input("Apna Roll Number Type Karein:").strip()
        
        if search_roll:
            # Local Database querying execution
            conn = sqlite3.connect('students_database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, course FROM students WHERE roll = ?', (search_roll,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                st.success(f"🎯 Record Found! Hello, {result[0]}")
                student_photo = st.file_uploader("Apni Passport Size Image Upload Karein:", type=["jpg", "jpeg", "png"])
                
                if student_photo is not None:
                    card_bytes = generate_id_card(
                        name=result[0],
                        roll=search_roll,
                        course=result[1],
                        photo_file=student_photo,
                        bg_color=db_bg,
                        text_color=db_text,
                        header_title=db_title
                    )
                    st.image(card_bytes, width=250)
                    st.download_button("📥 Download ID Card Now", data=card_bytes, file_name=f"ID_{search_roll}.png", mime="image/png")
            else:
                st.error("🔍 Yeh Roll Number database me nahi mila. Kripya sahi Roll Number enter karein.")
                

import streamlit as st
import csv
import io
import sqlite3
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🗄️ DATABASE ENGINE (FIXED FOR EXACT COLUMNS)
# ==========================================
def init_db():
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            app_no TEXT PRIMARY KEY,
            name TEXT,
            extra_data TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_setting(key, default):
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def save_setting(key, value):
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🎨 ID CARD DESIGN GENERATOR ENGINE
# ==========================================
def generate_dynamic_card(name, app_no, extra_fields_dict, photo_file, bg_color, text_color, header_title):
    total_fields = 2 + len(extra_fields_dict)
    card_height = 420 + (total_fields * 35)
    
    card = Image.new("RGB", (400, card_height), "#FFFFFF")
    draw = ImageDraw.Draw(card)
    
    # Top Header Accent
    draw.rectangle([(0, 0), (400, 110)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_label = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_header = font_name = font_text = font_label = ImageFont.load_default()

    draw.text((200, 55), header_title.upper(), fill="#FFFFFF", font=font_header, anchor="mm")
    
    # Photo Holder box logic
    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.fit(student_img, (120, 140), Image.Resampling.LANCZOS)
            card.paste(student_img, (140, 140))
            draw.rectangle([(140, 140), (260, 280)], outline=bg_color, width=3)
        except Exception:
            draw.rectangle([(140, 140), (260, 280)], fill="#E1E4E8", outline=bg_color, width=2)
    else:
        draw.rectangle([(140, 140), (260, 280)], fill="#E1E4E8", outline=bg_color, width=2)
        draw.text((200, 210), "[ PHOTO ]", fill="#586069", font=font_text, anchor="mm")
    
    # Name placement
    draw.text((200, 315), str(name).upper(), fill=text_color, font=font_name, anchor="mm")
    
    current_y = 360
    # Fixed Application Number Line rendering
    draw.text((50, current_y), "Application No:", fill=bg_color, font=font_label)
    draw.text((180, current_y), f"{app_no}", fill=text_color, font=font_text)
    current_y += 35
    
    # Loop over extra labels safely mapped
    for label, val in extra_fields_dict.items():
        display_label = label.strip().title() + ":"
        draw.text((50, current_y), display_label, fill=bg_color, font=font_label)
        draw.text((180, current_y), f"{val}", fill=text_color, font=font_text)
        current_y += 35
        
    draw.text((50, current_y), "Validity:", fill=bg_color, font=font_label)
    draw.text((180, current_y), "2026 - 2027", fill=text_color, font=font_text)
    
    # Signatory Bottom footer panel
    draw.rectangle([(0, card_height - 55), (400, card_height)], fill="#222222")
    draw.text((200, card_height - 28), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 🌐 ROUTER CORE WEB UI
# ==========================================
db_title = get_setting('header_title', 'UNIVERSAL INSTITUTE')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#333333')
db_fields = get_setting('custom_fields', 'Father Name, Dob, Trade Name, Trainee Mobile')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ SECTION 1: ADMIN CONTROL CENTER
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")
    
    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved!")
        
        st.subheader("🎨 Custom Design & Field Controller")
        new_title = st.text_input("Institute Name", db_title)
        new_bg = st.color_picker("Theme Color", db_bg)
        new_text = st.color_picker("Text Color", db_text)
        
        st.write("")
        st.markdown("##### ⚙️ ID Card Par Kya Details Aayengi?")
        st.caption("Aapke 25 columns me se jo bhi aapko card par print karna hai unka naam comma (,) laga kar exact likhein:")
        new_fields = st.text_input("Custom Layout Fields (Comma Separated):", db_fields)
        
        if new_title != db_title or new_bg != db_bg or new_text != db_text or new_fields != db_fields:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            save_setting('custom_fields', new_fields)
            st.rerun()

        st.markdown("---")
        st.subheader("📦 Bulk CSV Importer Dashboard")
        
        active_fields = [f.strip() for f in new_fields.split(",") if f.strip()]
        
        uploaded_csv = st.file_uploader("Upload Student Database (CSV)", type=["csv"])
        if uploaded_csv is not None:
            # Safe encoding handles standard excel configurations sheets cleanly
            file_contents = uploaded_csv.getvalue().decode("utf-8-sig").splitlines()
            reader = csv.DictReader(file_contents)
            
            # Clean headers to eliminate invisible trailing spaces from text
            reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
            
            conn = sqlite3.connect('dynamic_students_db.db')
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                # FIXED: Case-insensitive extraction for exact headings matching pattern
                r_app = row.get('Application Number', row.get('ApplicationNo', row.get('app_no', ''))).strip()
                r_name = row.get('Name', row.get('name', 'Unknown')).strip()
                
                if not r_app or r_app == "":
                    continue
                    
                student_extra_map = {}
                for field in active_fields:
                    student_extra_map[field] = row.get(field, 'N/A').strip()
                
                json_data_str = json.dumps(student_extra_map)
                
                cursor.execute('INSERT OR REPLACE INTO students (app_no, name, extra_data) VALUES (?, ?, ?)', (r_app, r_name, json_data_str))
                count += 1
                
            conn.commit()
            conn.close()
            st.success(f"✅ Data Synchronized! {count} records saved cleanly.")
            st.rerun()

        st.markdown("---")
        st.subheader("📋 Live Database Viewer")
        
        conn = sqlite3.connect('dynamic_students_db.db')
        cursor = conn.cursor()
        cursor.execute('SELECT app_no, name, extra_data FROM students')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            table_data = []
            for r in rows:
                row_dict = {"Application Number": r[0], "Student Name": r[1]}
                try:
                    extra_meta = json.loads(r[2])
                    row_dict.update(extra_meta)
                except:
                    pass
                table_data.append(row_dict)
                
            import pandas as pd
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
            
            if st.button("🗑️ Clear All Records"):
                conn = sqlite3.connect('dynamic_students_db.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM students')
                conn.commit()
                conn.close()
                st.warning("Database cleared successfully!")
                st.rerun()
        else:
            st.info("📂 Database is currently empty.")

    elif admin_pass != "":
        st.error("❌ Galat Password!")

# ==========================================
# 🎓 SECTION 2: STUDENT PORTAL (FIXED)
# ==========================================
st.header("🎓 Student Self-Service Hub")

# 1. Check karein ki database me data maujood hai ya nahi
conn = sqlite3.connect('dynamic_students_db.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM students')
db_count = cursor.fetchone()[0]
conn.close()

if db_count == 0:
    st.warning("⚠️ Admin ne abhi tak koi records database me upload nahi kiye hain.")
else:
    # 2. Student se Application Number input lena
    search_app = st.text_input("Apna Application Number Type Karein:").strip()
    
    if search_app:
        # 3. Database se Application Number search karna
        conn = sqlite3.connect('dynamic_students_db.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, extra_data FROM students WHERE app_no = ?', (search_app,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            s_name = result[0]
            s_json = result[1]
            extra_fields_loaded = json.loads(s_json)
            
            st.success(f"🎯 Record Found! Hello, {s_name}")
            
            st.write("### 📋 Aapki Verified Details:")
            for lbl, vl in extra_fields_loaded.items():
                st.write(f"🔹 **{lbl.title()}:** {vl}")
                
            # 4. Photo upload field
            student_photo = st.file_uploader("Apni Passport Photo Upload Karein (JPG/PNG):", type=["jpg","png","jpeg"])
            if student_photo is not None:
                # 5. ID Card image generate karna (Admin settings ke mutabik)
                card_bytes = generate_dynamic_card(
                    name=s_name,
                    app_no=search_app,
                    extra_fields_dict=extra_fields_loaded,
                    photo_file=student_photo,
                    bg_color=db_bg,
                    text_color=db_text,
                    header_title=db_title
                )
                
                # Live Preview aur Download Button
                st.image(card_bytes, width=260)
                st.download_button(
                    label="📥 Download My ID Card", 
                    data=card_bytes, 
                    file_name=f"ID_{search_app}.png", 
                    mime="image/png"
                )
        else:
            st.error("🔍 Yeh Application Number records me nahi mila. Kripya sahi input enter karein.")

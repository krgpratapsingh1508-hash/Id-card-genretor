import streamlit as st
import csv
import io
import sqlite3
import json
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🗄️ PERMANENT DATABASE ENGINE (25 COLUMNS FIXED)
# ==========================================
def init_db():
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    # Table columns updated according to your exact sheet structure
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            app_no TEXT PRIMARY KEY,
            name TEXT,
            samagra_id TEXT,
            father_name TEXT,
            mother_name TEXT,
            dob TEXT,
            gender TEXT,
            admission_year TEXT,
            trade_name TEXT,
            trade_type TEXT,
            mobile TEXT,
            email TEXT,
            category TEXT,
            ews TEXT,
            minority TEXT,
            passing_year TEXT,
            board_name TEXT,
            domicile TEXT,
            date_of_admission TEXT,
            trade_duration TEXT,
            round TEXT,
            disability TEXT,
            pwd_category TEXT,
            e_district TEXT
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
# 🎨 PREMIUM CIRCULAR ID CARD ENGINE WITH LOGO
# ==========================================
def generate_dynamic_card(student_dict, photo_file, bg_color, text_color, header_title, logo_base64=None):
    # Fixed proportional height logic
    card_height = 580 
    card = Image.new("RGB", (420, card_height), "#F8FAFC") 
    draw = ImageDraw.Draw(card)
    
    # Top Header Banner
    draw.rectangle([(0, 0), (420, 140)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_label = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font_header = font_sub = font_name = font_text = font_label = ImageFont.load_default()

    # Image logo placement handler
    header_text_x = 210
    if logo_base64 and logo_base64 != "None":
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_img = logo_img.resize((55, 55), Image.Resampling.LANCZOS)
            card.paste(logo_img, (30, 42), logo_img)
            header_text_x = 245
        except Exception:
            pass

    # Header Titles Text Render
    draw.text((header_text_x, 55), header_title.upper(), fill="#FFFFFF", font=font_header, anchor="mm" if header_text_x==210 else "lm")
    draw.text((header_text_x, 90), "STUDENT IDENTITY CARD", fill="#E2E8F0", font=font_sub, anchor="mm" if header_text_x==210 else "lm")
    
    # Circular Profile Photo Frame Canvas Masking
    cx, cy, r = 210, 215, 65
    draw.ellipse([(cx - r - 4, cy - r - 4), (cx + r + 4, cy + r + 4)], fill="#FFFFFF", outline=bg_color, width=4)
    
    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.fit(student_img, (r*2, r*2), Image.Resampling.LANCZOS)
            mask = Image.new("L", (r*2, r*2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (r*2, r*2)], fill=255)
            card.paste(student_img, (cx - r, cy - r), mask=mask)
        except Exception:
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
    else:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
        draw.text((cx, cy), "PHOTO", fill="#64748B", font=font_label, anchor="mm")
    
    # Student Full Name Text Header
    draw.text((210, 310), str(student_dict['name']).upper(), fill=text_color, font=font_name, anchor="mm")
    draw.line([(50, 335), (370, 335)], fill="#CBD5E1", width=2)
    
    # Core Fields Selection mapping grid array for display layout
    display_fields = [
        ("Application No :", student_dict['app_no']),
        ("Father Name :", student_dict['father_name']),
        ("Date of Birth :", student_dict['dob']),
        ("Trade Name :", student_dict['trade_name']),
        ("Mobile No :", student_dict['mobile']),
    ]
    
    current_y = 355
    for label, val in display_fields:
        draw.text((50, current_y), label, fill="#64748B", font=font_label)
        draw.text((185, current_y), f"{val}", fill="#0F172A", font=font_text)
        current_y += 36
        
    # Signatory Strip Footer Bar
    draw.rectangle([(0, card_height - 60), (420, card_height)], fill="#1E293B")
    draw.text((210, card_height - 30), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 🌐 ROUTER MAIN FRAMEWORK
# ==========================================
db_title = get_setting('header_title', 'GLOBAL TECHNOLOGIES')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#1E293B')
db_logo = get_setting('saved_logo_b64', 'None')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ MODE 1: ADMIN CONTROL CENTER (COMPLETE FIXED)
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")
    
    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved! Welcome Admin.")
        
        # --- SUBSECTION 1: LAYOUT & LOGO DESIGNER ---
        st.subheader("🎨 Custom Design & Brand Assets")
        new_title = st.text_input("Institute / School Name:", db_title)
        new_bg = st.color_picker("Header Top Theme Color:", db_bg)
        new_text = st.color_picker("Student Name Text Color:", db_text)
        
        # Permanent Logo Display & File Handler Trigger
        st.write("")
        st.markdown("##### 🏢 Permanent Institute Logo Status")
        if db_logo != "None":
            try:
                st.image(io.BytesIO(base64.b64decode(db_logo)), width=80, caption="Saved Current Logo")
            except Exception:
                pass
            
        logo_file = st.file_uploader("Naya Logo Upload/Change Karein (PNG/JPG):", type=["png", "jpg", "jpeg"])
        
        if logo_file is not None:
            logo_b64_str = base64.b64encode(logo_file.getvalue()).decode('utf-8')
            save_setting('saved_logo_b64', logo_b64_str)
            st.success("🎉 Logo permanently locked in SQLite database!")
            st.rerun()

        # Design configuration state sync checker
        if new_title != db_title or new_bg != db_bg or new_text != db_text:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            st.rerun()

        # --- SUBSECTION 2: BATCH CSV IMPORTER ---
        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer Dashboard")
        st.caption("💡 Apni 25 columns wali standard sheet upload karein. Sabhi details (Mobile, Father Name, Trade) auto-fetch ho jayengi.")
        
        uploaded_csv = st.file_uploader("Select Database Spreadsheet (.CSV File Only)", type=["csv"])
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8-sig").splitlines()
            reader = csv.DictReader(file_contents)
            
            # Standardization loop to safely clear blank keys spaces from Excel outputs
            reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
            
            conn = sqlite3.connect('dynamic_students_db.db')
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                r_app = row.get('Application Number', row.get('ApplicationNo', '')).strip()
                r_name = row.get('Name', 'Unknown').strip()
                
                if not r_app or r_app == "":
                    continue
                
                # Fetching parameters safely from row index keys arrays for all 25 columns
                cursor.execute('''
                    INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    r_app, r_name,
                    row.get('Samagra ID', 'N/A').strip(),
                    row.get('Father Name', 'N/A').strip(),
                    row.get('Mother Name', 'N/A').strip(),
                    row.get('Dob', 'N/A').strip(),
                    row.get('Gender', 'N/A').strip(),
                    row.get('Admission Year', 'N/A').strip(),
                    row.get('Trade Name', 'N/A').strip(),
                    row.get('Trade Type NCVT/SCVT', 'N/A').strip(),
                    row.get('Trainee Mobile', 'N/A').strip(),
                    row.get('Trainee Email', 'N/A').strip(),
                    row.get('Category', 'N/A').strip(),
                    row.get('EWS', 'N/A').strip(),
                    row.get('Minority Category', 'N/A').strip(),
                    row.get('Passing Year', 'N/A').strip(),
                    row.get('Board Name', 'N/A').strip(),
                    row.get('Domicile', 'N/A').strip(),
                    row.get('Date of Admission', 'N/A').strip(),
                    row.get('Trade Duration', 'N/A').strip(),
                    row.get('Round', 'N/A').strip(),
                    row.get('Disability', 'N/A').strip(),
                    row.get('PWD category', 'N/A').strip(),
                    row.get('Trainee E-District', 'N/A').strip()
                ))
                count += 1
                
            conn.commit()
            conn.close()
            st.success(f"✅ Data Synchronized! Total {count} records saved cleanly.")
            st.rerun()

        # --- SUBSECTION 3: DATA GRID LIST VIEWER ---
        st.markdown("---")
        st.subheader("📋 Live Database Uploaded List")
        
        conn = sqlite3.connect('dynamic_students_db.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            import pandas as pd
            # Structured full list formatting map layout parameters array
            columns_list = [
                "Application Number", "Student Name", "Samagra ID", "Father Name", "Mother Name",
                "DOB", "Gender", "Admission Year", "Trade Name", "Trade Type", "Mobile No",
                "Email", "Category", "EWS", "Minority", "Passing Year", "Board Name", "Domicile",
                "Date of Admission", "Trade Duration", "Round", "Disability", "PWD Category", "E-District"
            ]
            df_full = pd.DataFrame(rows, columns=columns_list)
            
            # Displays all 25 columns including mobile number seamlessly with horizontal scroll
            st.dataframe(df_full, use_container_width=False)
            st.write(f"Total Permanent Strength: **{len(rows)}** Students found in local database.")
            
            st.write("")
            if st.button("🗑️ Clear All Permanent Records", key="clear_db_btn"):
                conn = sqlite3.connect('dynamic_students_db.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM students')
                conn.commit()
                conn.close()
                st.warning("🚨 Complete student dataset deleted from server storage!")
                st.rerun()
        else:
            st.info("📂 Database is currently empty. Upload a clean CSV file above to populate data.")

    elif admin_pass != "":
        st.error("❌ Galat Password! Access Denied.")

# ------------------------------------------
# 🎓 MODE 2: STUDENT PORTAL SECTION (COMPLETE FIXED)
# ------------------------------------------
else:
    st.header("🎓 Student Self-Service Hub")
    
    # 1. Check karein ki database me data maujood hai ya nahi
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    db_count = cursor.fetchone()
    conn.close()
    
    if db_count[0] == 0:
        st.warning("⚠️ Admin ne abhi tak koi records database me upload nahi kiye hain.")
    else:
        # 2. Student se Application Number input lena
        search_app = st.text_input("Apna Application Number Type Karein:", placeholder="Eg. APP202601, 54321...").strip()
        
        if search_app:
            # 3. Database se Student ki details extract karna
            conn = sqlite3.connect('dynamic_students_db.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE app_no = ?', (search_app,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # 4. Database ke saare columns ko fixed array index se map karna
                student_data_map = {
                    'app_no': result[0],
                    'name': result[1],
                    'samagra_id': result[2],
                    'father_name': result[3],
                    'mother_name': result[4],
                    'dob': result[5],
                    'gender': result[6],
                    'admission_year': result[7],
                    'trade_name': result[8],
                    'trade_type': result[9],
                    'mobile': result[10],
                    'email': result[11]
                }
                
                st.success(f"🎯 Record Found! Hello, {student_data_map['name']}")
                
                # Screen par verified profile values show karna
                st.write("### 📋 Aapki Verified Details:")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"🔹 **Father Name:** {student_data_map['father_name']}")
                    st.write(f"🔹 **DOB (Birth Date):** {student_data_map['dob']}")
                with col_b:
                    st.write(f"🔹 **Trade/Course:** {student_data_map['trade_name']}")
                    st.write(f"🔹 **Mobile No:** {student_data_map['mobile']}")
                    
                # 5. Student ki Photo upload karne ka slot trigger
                student_photo = st.file_uploader("Apni Passport Photo Upload Karein (JPG/PNG):", type=["jpg","png","jpeg"])
                
                if student_photo is not None:
                    # ID card image bytes generate karna
                    card_bytes = generate_dynamic_card(
                        student_dict=student_data_map,
                        photo_file=student_photo,
                        bg_color=db_bg,
                        text_color=db_text,
                        header_title=db_title,
                        logo_base64=db_logo
                    )
                    
                    st.write("### 🪪 Aapka Live ID Card Preview:")
                    # Screen par premium card output render karna
                    st.image(card_bytes, width=270)
                    
                    # Instant Action Download Button
                    st.download_button(
                        label="📥 Download My ID Card", 
                        data=card_bytes, 
                        file_name=f"ID_{search_app}.png", 
                        mime="image/png"
                    )
                    st.balloons() # Visual celebration graphic animation trigger
            else:
                st.error("🔍 Yeh Application Number records me nahi mila. Kripya apna sahi Number enter karein.")
                

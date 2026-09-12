import streamlit as st
import csv
import io
import sqlite3
import pandas as pd
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🗄️ MASTER DATABASE ENGINE (CENTRALIZED)
# ==========================================
def get_db_connection():
    return sqlite3.connect('students_database.db')

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        val = row[0]
        if val.startswith("('") and (val.endswith("',)") or val.endswith(",)")):
            val = val.replace("('", "").replace("',)", "").replace(",)", "").strip("'")
        return val
    return default

def save_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🎨 PREMIUM CIRCULAR ID CARD ENGINE
# ==========================================
def generate_dynamic_card(student_dict, photo_file, bg_color, text_color, header_title, logo_base64=None):
    card_height = 580 
    card = Image.new("RGB", (420, card_height), "#F8FAFC") 
    draw = ImageDraw.Draw(card)
    
    draw.rectangle([(0, 0), (420, 140)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_label = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font_header = font_sub = font_name = font_text = font_label = ImageFont.load_default()

    header_text_x = 210
    if logo_base64 and logo_base64 != "None" and logo_base64 != "":
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_img = logo_img.resize((55, 55), Image.Resampling.LANCZOS)
            card.paste(logo_img, (30, 42), logo_img)
            header_text_x = 245
        except Exception:
            pass

    draw.text((header_text_x, 55), str(header_title).upper(), fill="#FFFFFF", font=font_header, anchor="mm" if header_text_x==210 else "lm")
    draw.text((header_text_x, 90), "STUDENT IDENTITY CARD", fill="#E2E8F0", font=font_sub, anchor="mm" if header_text_x==210 else "lm")
    
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
    
    draw.text((210, 310), str(student_dict['name']).upper(), fill=text_color, font=font_name, anchor="mm")
    draw.line([(50, 335), (370, 335)], fill="#CBD5E1", width=2)
    
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
        
    draw.rectangle([(0, card_height - 60), (420, card_height)], fill="#1E293B")
    draw.text((210, card_height - 30), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# ==========================================
# 🌐 MAIN ROUTER LAYOUT CONTROLLER
# ==========================================
db_title = get_setting('header_title', 'LOVE INSTITUTE')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#1E293B')
db_logo = get_setting('saved_logo_b64', 'None')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ MODE 1: ADMIN SECURE CONTROL PANEL (WITH ROW-SELECT DELETE)
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
        
        st.write("")
        st.markdown("##### 🏢 Permanent Institute Logo Status")
        if db_logo != "None" and db_logo != "":
            try:
                st.image(io.BytesIO(base64.b64decode(db_logo)), width=80, caption="Saved Current Logo")
            except Exception:
                pass
            
        logo_file = st.file_uploader("Naya Logo Upload/Change Karein (PNG/JPG):", type=["png", "jpg", "jpeg"])
        if logo_file is not None:
            logo_b64_str = base64.b64encode(logo_file.getvalue()).decode('utf-8')
            save_setting('saved_logo_b64', logo_b64_str)
            st.success("🎉 Logo permanently locked in SQLite!")
            st.rerun()

        if new_title != db_title or new_bg != db_bg or new_text != db_text:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            st.rerun()

        # --- SUBSECTION 2: BATCH CSV IMPORTER ---
        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer Dashboard")
        st.caption("💡 Apni 25 columns wali standard sheet upload karein. Sabhi details auto-fetch ho jayengi.")
        
        uploaded_csv = st.file_uploader("Select Database Spreadsheet (.CSV)", type=["csv"])
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8-sig").splitlines()
            reader = csv.DictReader(file_contents)
            reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                r_app = row.get('Application Number', row.get('ApplicationNo', '')).strip()
                r_name = row.get('Name', 'Unknown').strip()
                
                if not r_app or r_app == "":
                    continue
                
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

        # --- SUBSECTION 3: DATA GRID LIST VIEWER WITH MANUALLY ROW SELECTION ---
        st.markdown("---")
        st.subheader("📋 Live Database Uploaded List")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            columns_list = [
                "Application Number", "Student Name", "Samagra ID", "Father Name", "Mother Name",
                "DOB", "Gender", "Admission Year", "Trade Name", "Trade Type", "Mobile No",
                "Email", "Category", "EWS", "Minority", "Passing Year", "Board Name", "Domicile",
                "Date of Admission", "Trade Duration", "Round", "Disability", "PWD Category", "Trainee E-District"
            ]
            df_full = pd.DataFrame(rows, columns=columns_list)
            
            # Table me click selection column insert karna toggle control ke liye
            df_full.insert(0, "Select Row to Delete", False)
            
            # Data Editor block implementation for checkbox controls
            edited_df = st.data_editor(
                df_full,
                hide_index=True,
                disabled=[c for c in columns_list], # Baaki fields locked rahenge
                use_container_width=False
            )
            
            # Selected checked rows filter layout
            selected_rows = edited_df[edited_df["Select Row to Delete"] == True]
            st.write(f"Total Permanent Strength: **{len(rows)}** Students found in database.")
            
            # Action Controls Buttons Layout structure
            col_del1, col_del2 = st.columns(2)
            
            with col_del1:
                # SINGLE SELECT DELETION TRIGGER
                if st.button("🗑️ Delete Selected Student(s)", key="del_selected"):
                    if not selected_rows.empty:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        for app_no in selected_rows["Application Number"]:
                            cursor.execute('DELETE FROM students WHERE app_no = ?', (str(app_no),))
                        conn.commit()
                        conn.close()
                        st.success(f"🚨 Selected ({len(selected_rows)}) records permanently removed!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Kripya delete karne ke liye pehle list me kisi row ke aage check-box par click karein.")
                        
            with col_del2:
                # BATCH PURGE CONTROL
                if st.button("🚨 Clear Entire Database Records", key="clear_db_btn"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM students')
                    conn.commit()
                    conn.close()
                    st.warning("🚨 Complete student database deleted!")
                    st.rerun()
        else:
            st.info("📂 Database is currently empty. Upload your clean CSV file above to populate data.")

    elif admin_pass != "":
        st.error("❌ Galat Password! Access Denied.")

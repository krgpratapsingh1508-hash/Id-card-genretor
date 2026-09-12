import streamlit as st
import csv
import io
import sqlite3
import json
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🗄️ ADVANCED SQLITE DATABASE ENGINE
# ==========================================
def init_db():
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    # Student Data Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            app_no TEXT PRIMARY KEY,
            name TEXT,
            extra_data TEXT
        )
    ''')
    # Settings & Permanent Logo Table
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
# 🎨 PREMIUM ID CARD DESIGN ENGINE WITH LOGO
# ==========================================
def generate_dynamic_card(name, app_no, extra_fields_dict, photo_file, bg_color, text_color, header_title, logo_base64=None):
    total_fields = 2 + len(extra_fields_dict) 
    card_height = 450 + (total_fields * 38) 
    
    # Base Canvas
    card = Image.new("RGB", (420, card_height), "#F8FAFC") 
    draw = ImageDraw.Draw(card)
    
    # Top Header Background
    draw.rectangle([(0, 0), (420, 140)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_label = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font_header = font_sub = font_name = font_text = font_label = ImageFont.load_default()

    # Dynamic Permanent Logo Rendering inside Header
    header_text_x = 210
    if logo_base64 and logo_base64 != "None":
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data))
            # Logo ko square thumb shape me resize karna
            logo_img = logo_img.resize((50, 50), Image.Resampling.LANCZOS)
            card.paste(logo_img, (30, 45), logo_img.convert("RGBA") if logo_img.mode == "RGBA" else None)
            header_text_x = 240 # Text shift left if logo available
        except Exception as e:
            pass

    # Header Titles Text Placement
    draw.text((header_text_x, 55), header_title.upper(), fill="#FFFFFF", font=font_header, anchor="mm" if header_text_x==210 else "lm")
    draw.text((header_text_x, 90), "STUDENT IDENTITY CARD", fill="#E2E8F0", font=font_sub, anchor="mm" if header_text_x==210 else "lm")
    
    # Circular Profile Photo Frame Canvas
    cx, cy, r = 210, 210, 65
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
    
    # Bold Student Name Heading
    draw.text((210, 305), str(name).upper(), fill=text_color, font=font_name, anchor="mm")
    draw.line([(50, 330), (370, 330)], fill="#CBD5E1", width=2)
    
    # Profile Metadata Form Grid Loop Layout
    current_y = 350
    draw.text((50, current_y), "Application No :", fill="#64748B", font=font_label)
    draw.text((185, current_y), f"{app_no}", fill="#0F172A", font=font_text)
    current_y += 38
    
    for label, val in extra_fields_dict.items():
        display_label = label.strip().title() + " :"
        draw.text((50, current_y), display_label, fill="#64748B", font=font_label)
        draw.text((185, current_y), f"{val}", fill="#0F172A", font=font_text)
        current_y += 38
        
    draw.text((50, current_y), "Validity :", fill="#64748B", font=font_label)
    draw.text((185, current_y), "2026 - 2027", fill="#0F172A", font=font_text)
    
    # Bottom Strip Signatory Footer
    draw.rectangle([(0, card_height - 60), (420, card_height)], fill="#1E293B")
    draw.text((210, card_height - 30), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# ==========================================
# 🌐 ROUTER CORE WEB INTERFACE UI
# ==========================================
st.set_page_config(page_title="Dynamic Persistent ID System", page_icon="🪪")

# Initialize global layout state variables from DB
db_title = get_setting('header_title', 'UNIVERSAL INSTITUTE')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#333333')
db_fields = get_setting('custom_fields', 'Father Name, Dob, Trade Name, Trainee Mobile')
db_logo = get_setting('saved_logo_b64', 'None')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ MODE 1: ADMIN CONTROL CENTER
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")
    
    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved!")
        
        st.subheader("🎨 Custom Design & Brand Assets")
        new_title = st.text_input("Institute / School Name", db_title)
        new_bg = st.color_picker("Header Theme Color", db_bg)
        new_text = st.color_picker("Name Font Color", db_text)
        
        # PERMANENT LOGO UPLOADER HANDLER
        st.write("")
        st.markdown("##### 🏢 Permanent Institute Logo")
        if db_logo != "None":
            try:
                st.image(io.BytesIO(base64.b64decode(db_logo)), width=70, caption="Saved Current Logo")
            except Exception:
                pass
            
        logo_file = st.file_uploader("Naya Logo Upload/Change Karein (PNG/JPG):", type=["png", "jpg", "jpeg"])
        
        if logo_file is not None:
            logo_b64_str = base64.b64encode(logo_file.getvalue()).decode('utf-8')
            save_setting('saved_logo_b64', logo_b64_str)
            st.success("🎉 Logo permanently saved in database!")
            st.rerun()

        st.markdown("---")
        st.markdown("##### ⚙️ ID Card Layout Setup Fields")
        new_fields = st.text_input("Custom Layout Fields (Comma Separated):", db_fields)
        
        if new_title != db_title or new_bg != db_bg or new_text != db_text or new_fields != db_fields:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            save_setting('custom_fields', new_fields)
            st.rerun()

        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer Dashboard")
        active_fields = [f.strip() for f in new_fields.split(",") if f.strip()]
        
        uploaded_csv = st.file_uploader("Upload Student Database (CSV File)", type=["csv"])
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8-sig").splitlines()
            reader = csv.DictReader(file_contents)
            reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
            
            conn = sqlite3.connect('dynamic_students_db.db')
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                r_app = row.get('Application Number', row.get('ApplicationNo', row.get('app_no', ''))).strip()
                r_name = row.get('Name', row.get('name', 'Unknown')).strip()
                
                if not r_app:
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
        st.subheader("📋 Live Database Uploaded List")
        
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
                    row_dict.update(json.loads(r[2]))
                except: pass
                table_data.append(row_dict)
                
            import pandas as pd
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
            st.write(f"Total Database Strength: **{len(rows)}** Students.")
            
            if st.button("🗑️ Clear All Permanent Records"):
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

# ------------------------------------------
# 🎓 MODE 2: STUDENT PORTAL SECTION
# ------------------------------------------
else:
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
            # 3. Database se Student ka details search karna
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
                
                # Screen par verified details list show karna
                st.write("### 📋 Aapki Verified Details:")
                for lbl, vl in extra_fields_loaded.items():
                    st.write(f"🔹 **{lbl.title()}:** {vl}")
                    
                # 4. Student ki Photo upload karne ka slot trigger
                student_photo = st.file_uploader("Apni Passport Photo Upload Karein (JPG/PNG):", type=["jpg","png","jpeg"])
                
                if student_photo is not None:
                    # 5. Dynamic premium card generate karna text aur saved logo ke sath
                    card_bytes = generate_dynamic_card(
                        name=s_name,
                        app_no=search_app,
                        extra_fields_dict=extra_fields_loaded,
                        photo_file=student_photo,
                        bg_color=db_bg,
                        text_color=db_text,
                        header_title=db_title,
                        logo_base64=db_logo
                    )
                    
                    st.write("### 🪪 Aapka Live ID Card Preview:")
                    # Screen par live card show karna
                    st.image(card_bytes, width=260)
                    
                    # Instant Action Download Button
                    st.download_button(
                        label="📥 Download My ID Card", 
                        data=card_bytes, 
                        file_name=f"ID_{search_app}.png", 
                        mime="image/png"
                    )
                    st.balloons() # Success celebration graphics trigger
            else:
                st.error("🔍 Yeh Application Number records me nahi mila. Kripya sahi input enter karein.")

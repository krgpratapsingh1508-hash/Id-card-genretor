import streamlit as st
import csv
import io
import sqlite3
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# 🗄️ LOCAL ADVANCED SQLITE DATABASE ENGINE
# ==========================================
def init_db():
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    # Dynamic fields ko handle karne ke liye hum data ko JSON string format me save karenge
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
# 🎨 DYNAMIC ID CARD DESIGN SYSTEM
# ==========================================
def generate_dynamic_card(name, app_no, extra_fields_dict, photo_file, bg_color, text_color, header_title):
    # Total fields count ke hisab se height dynamic calculate karna
    total_fields = 2 + len(extra_fields_dict) # Name + AppNo + Extra Fields
    card_height = 420 + (total_fields * 35) # Height auto-adjust logic
    
    card = Image.new("RGB", (400, card_height), "#FFFFFF")
    draw = ImageDraw.Draw(card)
    
    # Header Background Accent
    draw.rectangle([(0, 0), (400, 110)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_label = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_header = font_name = font_text = font_label = ImageFont.load_default()

    # Institute Name
    draw.text((200, 55), header_title.upper(), fill="#FFFFFF", font=font_header, anchor="mm")
    
    # Passport Photo Frame Loader
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
    
    # Student Full Name Text
    draw.text((200, 315), str(name).upper(), fill=text_color, font=font_name, anchor="mm")
    
    # --- Dynamic Fields Drawing Layout Loop ---
    current_y = 360
    
    # Fixed Application No Field
    draw.text((50, current_y), "Application No:", fill=bg_color, font=font_label)
    draw.text((180, current_y), f"{app_no}", fill=text_color, font=font_text)
    current_y += 35
    
    # Extra Dynamic Admin Defined Fields Loop execution
    for label, val in extra_fields_dict.items():
        # Title case format spacing adjust
        display_label = label.strip().title() + ":"
        draw.text((50, current_y), display_label, fill=bg_color, font=font_label)
        draw.text((180, current_y), f"{val}", fill=text_color, font=font_text)
        current_y += 35
        
    # Standard Validation stamp placement
    draw.text((50, current_y), "Validity:", fill=bg_color, font=font_label)
    draw.text((180, current_y), "2026 - 2027", fill=text_color, font=font_text)
    
    # Bottom Fixed Signatory Stamp Footer
    draw.rectangle([(0, card_height - 55), (400, card_height)], fill="#222222")
    draw.text((200, card_height - 28), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 🌐 MAIN ROUTER LAYOUT CONTROLLER
# ==========================================
st.set_page_config(page_title="Dynamic Setup ID Engine", page_icon="🪪")

# Initialize global layout state variables from persistence layers
db_title = get_setting('header_title', 'UNIVERSAL INSTITUTE')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#333333')
# Default tags placeholder strings configuration
db_fields = get_setting('custom_fields', 'Course, Father Name, Mobile No')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ SYSTEM SECTION 1: ADMIN ARCHITECT
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
        st.markdown("##### ⚙️ ID Card Par Kya Kya Details Aayengi?")
        st.caption("Jo fields aapko chahiye unhe comma (,) lagakar likhein. System automatic unka layout aur database bana dega.")
        new_fields = st.text_input("Custom Layout Fields (Comma Separated):", db_fields)
        
        # State syncing trigger conditions checking block
        if new_title != db_title or new_bg != db_bg or new_text != db_text or new_fields != db_fields:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            save_setting('custom_fields', new_fields)
            st.rerun()

        st.markdown("---")
        st.subheader("📦 Bulk CSV Importer Dashboard")
        
        # Parse fields structured breakdown lists
        active_fields = [f.strip() for f in new_fields.split(",") if f.strip()]
        
        st.info(f"💡 **Aapki CSV file me yeh headings hona jaroori hai:**\n`AppNo`, `Name`, {', '.join([f'`{x}`' for x in active_fields])}")
        
        uploaded_csv = st.file_uploader("Upload Student Database (CSV)", type=["csv"])
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8").splitlines()
            reader = csv.DictReader(file_contents)
            
            conn = sqlite3.connect('dynamic_students_db.db')
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                # Primary headers verification matching sequence
                r_app = row.get('AppNo', row.get('appno', '')).strip()
                r_name = row.get('Name', row.get('name', 'Unknown'))
                
                if not r_app:
                    continue
                    
                # Dynamic subfields gathering from row inside json map packing
                student_extra_map = {}
                for field in active_fields:
                    student_extra_map[field] = row.get(field, row.get(field.lower(), 'N/A'))
                
                json_data_str = json.dumps(student_extra_map)
                
                cursor.execute('INSERT OR REPLACE INTO students (app_no, name, extra_data) VALUES (?, ?, ?)', (r_app, r_name, json_data_str))
                count += 1
                
            conn.commit()
            conn.close()
            st.success(f"✅ Data Synchronized! {count} records saved with dynamic layouts.")

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
                row_dict = {"Application No": r[0], "Student Name": r[1]}
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
                st.warning("Database cleared!")
                st.rerun()
        else:
            st.write("📂 Database is currently empty.")

# ==========================================
# 🎓 SYSTEM SECTION 2: STUDENT LIVE PORTAL (FIXED FOR YOUR COLUMNS)
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
            s_name = result[0]   # Student ka Name tuple se nikala
            s_json = result[1]   # Extra data JSON tuple se nikala
            
            # Admin dwara upload kiye gaye dynamic fields ko decode karna
            extra_fields_loaded = json.loads(s_json)
            
            st.success(f"🎯 Record Found! Hello, {s_name}")
            
            # Screen par details show karna
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
            st.error("🔍 Yeh Application Number records me nahi mila. Kripya sahi Number dalein.")

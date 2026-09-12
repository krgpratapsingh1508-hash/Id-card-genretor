import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 🎨 ID CARD DESIGN FUNCTION
# ==========================================
def generate_id_card(name, roll, course, output_path):
    # 1. Blank Card Canvas Create Karein (Size: 400x600, Color: White)
    card = Image.new("RGB", (400, 600), "#FFFFFF")
    draw = ImageDraw.Draw(card)
    
    # 2. Colors Design Colors
    primary_color = "#0052cc"  # Blue Header
    text_color = "#333333"     # Dark Gray Text
    
    # 3. Header Shape Draw Karein
    draw.rectangle([(0, 0), (400, 100)], fill=primary_color)
    
    # 4. Standard Default Font Load Karein
    try:
        # Agar computer me Arial font hai toh use karein
        font_header = ImageFont.truetype("arial.ttf", 26)
        font_name = ImageFont.truetype("arial.ttf", 28)
        font_text = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        # Nahi toh default basic font use karein
        font_header = font_name = font_text = ImageFont.load_default()

    # 5. Header Text Likhein
    draw.text((200, 50), "UNIVERSAL INSTITUTE", fill="#FFFFFF", font=font_header, anchor="mm")
    
    # 6. Dummy Profile Photo Box Draw Karein (Circle)
    draw.ellipse([(140, 140), (260, 260)], fill="#E1E4E8", outline=primary_color, width=3)
    draw.text((200, 200), "👤", fill="#586069", font=font_name, anchor="mm")
    
    # 7. Student Name Likhein
    draw.text((200, 310), name.upper(), fill=text_color, font=font_name, anchor="mm")
    
    # 8. Student Details (Roll, Course) Likhein
    draw.text((60, 380), f"Roll No:  {roll}", fill=text_color, font=font_text)
    draw.text((60, 420), f"Course:   {course}", fill=text_color, font=font_text)
    draw.text((60, 460), f"Validity: 2026 - 2027", fill=text_color, font=font_text)
    
    # 9. Footer Shape Draw Karein
    draw.rectangle([(0, 550), (400, 600)], fill="#333333")
    draw.text((200, 575), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    # 10. Image Save Karein
    card.save(output_path, "PNG")

# ==========================================
# 💻 ADMIN PANEL UI (FILE UPLOADER)
# ==========================================
def upload_and_process():
    # Admin Panel se CSV file select karne ka popup
    csv_file_path = filedialog.askopenfilename(
        title="Apni Student Data CSV File Select Karein",
        filetypes=[("CSV Files", "*.csv")]
    )
    
    if not csv_file_path:
        return

    # Output folder banana jahan saare ID cards save honge
    output_dir = "generated_id_cards"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        count = 0
        # CSV file open karke data read karna
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # CSV columns se data uthana (Name, Roll, Course)
                name = row.get('Name', 'Unknown')
                roll = row.get('Roll', '000')
                course = row.get('Course', 'N/A')
                
                # File name design karna
                filename = f"{output_dir}/{roll}_{name.replace(' ', '_')}.png"
                
                # ID card generate karna
                generate_id_card(name, roll, course, filename)
                count += 1
                
        messagebox.showinfo("Success", f"✅ Badhai Ho! Total {count} ID Cards 'generated_id_cards' folder me ban gaye hain!")
    except Exception as e:
        messagebox.showerror("Error", f"Kuch gadbad hui: {str(e)}")

# Tkinter window setup (Admin Panel Dashboard Interface)
root = tk.Tk()
root.title("Admin Panel - ID Card Generator")
root.geometry("450x250")
root.config(bg="#f0f2f5")

label = tk.Label(root, text="🛡️ Admin Panel - Batch ID Generator", font=("Arial", 16, "bold"), bg="#f0f2f5", fg="#333")
label.pack(pady=20)

desc = tk.Label(root, text="CSV File upload karein jisme Name, Roll, Course headings ho.", font=("Arial", 10), bg="#f0f2f5", fg="#666")
desc.pack(pady=5)

upload_btn = tk.Button(root, text="Upload CSV & Generate Cards", font=("Arial", 12, "bold"), bg="#0052cc", fg="white", padx=10, pady=10, command=upload_and_process)
upload_btn.pack(pady=25)

root.mainloop()

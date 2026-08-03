import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'

# নিশ্চিত করা যেন ফোল্ডারগুলো বিদ্যমান থাকে
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Google Sheets API কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
SPREADSHEET_ID = "1F-cqmUlWO12uMzgerlfP5izhh3cYL-rJ9FflbePtyDI"
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# পেছনের জার্সিতে নাম ও নম্বর বসানোর ফাংশন
def generate_custom_jersey(name, number):
    base_back_path = "static/base_back.png"
    output_path = os.path.join(app.config['GENERATED_FOLDER'], f"jersey_{number}_{name}.png")
    
    if os.path.exists(base_back_path):
        img = Image.open(base_back_path)
        draw = ImageDraw.Draw(img)
        
        font_path = "static/custom_font.ttf"
        
        # ফন্ট সাইজ সামঞ্জস্য
        try:
            name_font = ImageFont.truetype(font_path, size=75)     # নাম বড় করার জন্য
            number_font = ImageFont.truetype(font_path, size=350)  # নম্বর বড় করার জন্য
        except:
            name_font = ImageFont.load_default()
            number_font = ImageFont.load_default()

        width, height = img.size

        # সোনালি কালার কোড (Gold Hex Code: #D4AF37 বা RGB: 212, 175, 55)
        gold_color = (179, 136, 67)

        # ১. নাম বসানো (পজিশন: উপর থেকে প্রায় ৩৩% নিচে)
        draw.text((width / 2, height * 0.28), name.upper(), fill=gold_color, font=name_font, anchor="mm")
        
        # ২. জার্সি নম্বর বসানো (পজিশন: নাম থেকে কিছুটা নিচে, প্রায় ৫৪% নিচে)
        draw.text((width / 2, height * 0.49), str(number), fill=gold_color, font=number_font, anchor="mm")
        
        img.save(output_path)
        return output_path
    return base_back_path

# বুক করা জার্সি নাম্বারগুলো বের করা
def get_booked_numbers():
    try:
        records = sheet.get_all_records()
        booked = [int(row['Jersey Number']) for row in records if 'Jersey Number' in row and str(row['Jersey Number']).isdigit()]
        return booked
    except Exception as e:
        print("Sheet Read Error:", e)
        return []

@app.route('/')
def index():
    booked_numbers = get_booked_numbers()
    # ১ থেকে ৯৯ পর্যন্ত ফাঁকা নাম্বার নির্ধারণ
    available_numbers = [i for i in range(1, 100) if i not in booked_numbers]
    return render_template('index.html', numbers=available_numbers)

@app.route('/submit', methods=['POST'])
def submit():
    full_name = request.form.get('full_name')
    roll = request.form.get('roll')
    session = request.form.get('session')
    mobile = request.form.get('mobile')
    size = request.form.get('size')
    jersey_number = request.form.get('jersey_number')
    jersey_name = request.form.get('jersey_name')
    payment_method = request.form.get('payment_method')
    trx_id = request.form.get('trx_id')
    
    # স্ক্রিনশট ছাড়া সরাসরি Google Sheet-এ তথ্য পাঠানো হচ্ছে
    sheet.append_row([full_name, roll, session, mobile, size, jersey_number, jersey_name, payment_method, trx_id])

    # ডাইনামিক কাস্টম জার্সি তৈরি
    generated_back_image = generate_custom_jersey(jersey_name, jersey_number)

    return render_template('confirmation.html', 
                           name=full_name, 
                           jersey_number=jersey_number, 
                           jersey_name=jersey_name,
                           back_image=generated_back_image)

if __name__ == '__main__':
    app.run(debug=True)
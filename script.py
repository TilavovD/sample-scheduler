import requests
from bs4 import BeautifulSoup
import re
import csv
import pandas as pd
from datetime import datetime
import smtplib
import os
from email.message import EmailMessage

# Headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "david.stylemix@gmail.com"
SENDER_PASSWORD = "snrn laxn fwcz pntr"  # Use an App Password if using Gmail
RECEIVER_EMAIL = "jrahmonov1906@gmail.com"

def scrape_and_send_email():
    # Generate filenames with timestamp
    timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    csv_filename = f"mihome_products_{timestamp}.csv"
    xlsx_filename = f"mihome_products_{timestamp}.xlsx"

    # Open CSV file for writing
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Post ID", "Link", "Product Name", "Price"])

        # Loop through pages
        i = 1
        while True:
            url = f"https://mihome.uz/page/{i}/?s=+&post_type=product"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                list_items = soup.find_all("li", class_=re.compile(r"post-\d+"))

                for li in list_items:
                    post_id = None
                    class_list = li.get("class", [])
                    for cls in class_list:
                        match = re.search(r"post-(\d+)", cls)
                        if match:
                            post_id = match.group(1)
                            break

                    header_div = li.find("div", class_="product-loop-header product-item__header")
                    first_a_tag = header_div.find("a") if header_div else None
                    first_link = first_a_tag["href"] if first_a_tag else None

                    product_name = li.find("h2", class_="woocommerce-loop-product__title")
                    product_name = product_name.text.strip() if product_name else "N/A"

                    price_tag = li.find("span", class_="woocommerce-Price-amount")
                    price = price_tag.text.strip() if price_tag else "N/A"

                    if post_id and first_link:
                        writer.writerow([post_id, first_link, product_name, price])
            else:
                break

            i += 1

    # Convert CSV to XLSX
    csv_data = pd.read_csv(csv_filename)
    csv_data.to_excel(xlsx_filename, index=False)

    # Create email message
    msg = EmailMessage()
    msg["Subject"] = "Scraped Data File"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content("Please find the attached file containing the scraped data.")

    # Attach file
    if os.path.exists(xlsx_filename):
        with open(xlsx_filename, "rb") as file:
            file_data = file.read()
            file_name = os.path.basename(xlsx_filename)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    # Send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        # Remove files after successful email sending
        os.remove(csv_filename)
        os.remove(xlsx_filename)

        # Print only the datetime of email delivery
        print("Email sent at:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))

    except Exception as e:
        print("Error sending email:", e)

# Run the function immediately when script starts
scrape_and_send_email()

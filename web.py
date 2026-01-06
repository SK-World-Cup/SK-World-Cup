from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "1v1 Gaming Stats Bot"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

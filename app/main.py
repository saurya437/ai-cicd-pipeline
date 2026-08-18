import fake_missing_package

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {"message": "AI Self-Healing CI/CD Pipeline is running!"}

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
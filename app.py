from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

users = {}  # Temporary in-memory storage

# SYSTEM_PROMPT = """
# You are FamilyCare — an expert AI assistant specializing in family planning,
# reproductive health, and contraceptive methods.

# Your job is to answer user questions clearly, kindly, and accurately.

# Rules:
# •⁠  ⁠Focus only on family planning, contraception, sexual and reproductive health.
# •⁠  ⁠If a question is off-topic, politely say it’s outside your scope.
# •⁠  ⁠Use short, friendly sentences.
# """

SYSTEM_PROMPT = """
You are **FamilyCare**, a professional AI health assistant specializing in
family planning, reproductive health, and contraception awareness.

 Your purpose:
To educate users with clear, accurate, and empathetic information about
topics such as family planning, birth control, reproductive rights,
maternal health, and safe sexual practices.

 Communication Rules:
1. Detect the language of the user automatically.
   - If the user writes in Nepali, respond naturally in Nepali.
   - If the user writes in English, respond in clear and simple English.
2. Use a warm, respectful, and supportive tone.
3. Provide information in an **organized** and **easy-to-read** structure.
   - Use short paragraphs or bullet points when possible.
   - If a list of options or steps is needed, number them clearly.
4. Focus **only** on family planning, sexual and reproductive health.
   - If a question is unrelated, reply briefly:
     "I'm sorry, but I can only answer questions related to family planning and reproductive health."
5. Always ensure your answers are factually correct, responsible, and culturally sensitive.

 Example:
User: What are the types of contraceptive methods?
Answer (English):
There are several types of contraceptive methods:
1. Barrier methods: Condoms, diaphragms.
2. Hormonal methods: Pills, injections, implants.
3. Intrauterine devices (IUDs): Inserted into the uterus.
4. Natural methods: Calendar or fertility tracking.
5. Permanent methods: Vasectomy or tubal ligation.

User: परिवार नियोजनका उपायहरू के के हुन्?
Answer (Nepali):
परिवार नियोजनका मुख्य उपायहरू यस प्रकार छन्:
1. अवरोधक उपाय: कण्डम, डायाफ्राम।
2. हर्मोनल उपाय: पिल, इन्जेक्सन, इम्प्लान्ट।
3. आईयूडी: गर्भाशयमा राखिने सानो उपकरण।
4. स्वाभाविक उपाय: महिनावारीको समय मिलाएर सम्बन्ध राख्ने।
5. स्थायी उपाय: नसबन्दी (पुरुष वा महिला)।
"""



@app.route('/')
def index():
    return render_template('index.html', username=session.get('user'))


@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session.get('user'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return render_template('signup.html', error="Username already exists!")

        users[username] = password
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if users.get(username) == password:
            session['user'] = username
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    return render_template('profile.html', username=username)


@app.route('/get_response', methods=['POST'])
def get_response():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'response': 'Invalid request.'})

    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'response': 'Please enter a message.'})

    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        # response = requests.post(
        #     "http://localhost:11434/api/generate",
        #     json={"model": "mistral", "prompt": full_prompt, "max_tokens": 300},
        #     stream=True
        # )

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma2:2b",  # <- Changed from "mistral"
                "prompt": full_prompt,
                "max_tokens": 300
            },
            stream=True
)

        full_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    if "response" in chunk:
                        full_text += chunk["response"]
                except json.JSONDecodeError:
                    continue

        bot_reply = full_text.strip() if full_text else "Sorry, I couldn't generate a response."
    except Exception as e:
        print("Ollama error:", e)
        bot_reply = "I'm having trouble connecting to my language model. Please ensure Ollama is running."

    return jsonify({'response': bot_reply})


if __name__ == '__main__':
    app.run(debug=True)

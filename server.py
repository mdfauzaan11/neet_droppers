from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import pymysql
import os

app = Flask(__name__)

# -------------------
# Database connection helper
# -------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "neetdb")
    )

# -------------------
# Routes
# -------------------

# Home page
@app.route("/")
def home():
    return render_template("home.html")

# Form page
@app.route("/form")
def form_page():
    return render_template("form.html")

# Study page
@app.route("/study")
def study_page():
    return render_template("study.html")

# Chat page
@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_message = request.json.get("message", "").lower()
    if "hello" in user_message or "hi" in user_message:
        reply = "Hello! How can I help you with your NEET preparation?"
    elif "study material" in user_message:
        reply = "You can find study materials in the 'Study Materials' section of our site."
    elif "community" in user_message:
        reply = "Join our NEET droppers community for support and motivation!"
    elif "form" in user_message or "join" in user_message:
        reply = "You can fill out the form here: /form"
    elif "resources" in user_message:
        reply = "We provide various resources including notes, videos, and mock tests."
    elif "help" in user_message:
        reply = "Sure! Ask me anything about study materials, community, or the form."
    elif "bye" in user_message or "goodbye" in user_message:
        reply = "Goodbye! Best of luck with your studies."
    elif "thank you" in user_message or "thanks" in user_message:
        reply = "You're welcome! Feel free to ask if you have more questions." 
    else:
        reply = "Sorry, I didn’t understand that. Please try asking about study materials, community, or form."
    return jsonify({"reply": reply})

@app.route("/community")
def community_page():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)  # Use mysql.connector.DictCursor equivalent

    # Fetch community members
    cursor.execute("SELECT name FROM students")
    members = [row['name'] for row in cursor.fetchall()]

    # Fetch user stories
    cursor.execute("SELECT name, age, attempts, story FROM stories ORDER BY created_at DESC")
    stories = cursor.fetchall()  # list of dicts

    db.close()
    return render_template("community.html", members=members, stories=stories)


#community stories
@app.route("/share_your_story", methods=["GET"])
def share_your_story():
    return render_template("share_your_story.html")

@app.route("/submit_story", methods=["POST"])
def submit_story():
    name = request.form.get("name")
    age = request.form.get("age")
    attempts = request.form.get("attempts")
    story = request.form.get("story")

    db = get_db_connection()
    cursor = db.cursor()
    sql = "INSERT INTO stories (name, age, attempts, story) VALUES (%s, %s, %s, %s)"
    values = (name, age, attempts, story)
    cursor.execute(sql, values)
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("community_page"))

# Form submission
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    student_class = request.form.get("class")
    city = request.form.get("city")
    state = request.form.get("state")
    source = request.form.get("source")
    comments = request.form.get("comments")

    db = get_db_connection()
    cursor = db.cursor()
    sql = """
        INSERT INTO students
        (name, email, phone, class, city, state, source, comments)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (name, email, phone, student_class, city, state, source, comments)
    cursor.execute(sql, values)
    db.commit()
    db.close()

    return f"Thanks {name}, your form has been submitted successfully!"

# -------------------
# Mock Tests
# -------------------

@app.route("/mocktests", methods=["GET", "POST"])
def mocktests():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    subjects = ["Physics", "Chemistry", "Biology"]

    # Use request.args.get() to read query parameters from URL
    selected_subject = request.args.get("subject")
    selected_chapter = request.args.get("chapter")

    chapters = []
    questions = []

    if selected_subject:
        cursor.execute("SELECT DISTINCT chapter FROM mock_tests WHERE subject=%s", (selected_subject,))
        chapters = [row['chapter'] for row in cursor.fetchall()]

    if selected_subject and selected_chapter:
        cursor.execute(
            "SELECT * FROM mock_tests WHERE subject=%s AND chapter=%s",
            (selected_subject, selected_chapter)
        )
        questions = cursor.fetchall()

    db.close()
    return render_template(
        "mocktests.html",
        subjects=subjects,
        selected_subject=selected_subject,
        chapters=chapters,
        selected_chapter=selected_chapter,
        questions=questions
    )

# Update the /mocktest/<subject>/<chapter> route to handle only POST (submission)
@app.route("/mocktest/<subject>/<chapter>", methods=["POST"])
def mocktest_chapter(subject, chapter):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch all questions for the subject & chapter
    cursor.execute(
        "SELECT id, question, correct_option FROM mock_tests WHERE subject=%s AND chapter=%s",
        (subject, chapter)
    )
    questions = cursor.fetchall()

    # Get submitted answers
    user_answers = request.form.to_dict()

    total_questions = len(questions)
    correct = 0
    attempted = 0
    detailed_answers = []

    for q in questions:
        qid = str(q['id'])
        user_ans = user_answers.get(f"q{qid}")

        if user_ans:  # user attempted this question
            attempted += 1
            if user_ans.upper() == q['correct_option'].upper():
                correct += 1
        else:
            user_ans = "Skipped"  # mark skipped

        detailed_answers.append({
            "question": q['question'],
            "user_answer": user_ans,
            "correct_answer": q['correct_option']
        })

    wrong = attempted - correct
    skipped = total_questions - attempted
    percentage = round((correct / total_questions) * 100, 2)

    db.close()
    return render_template(
        "mocktest_result.html",
        total=total_questions,
        attempted=attempted,
        correct=correct,
        wrong=wrong,
        skipped=skipped,
        percentage=percentage,
        detailed_answers=detailed_answers,
        subject=subject,
        chapter=chapter
    )

# -------------------
# Admin Page to Add Mock Test Questions
# -------------------
@app.route("/admin/mocktest", methods=["GET", "POST"])
def admin_mocktest():
    if request.method == "POST":
        subject = request.form.get("subject")
        chapter = request.form.get("chapter")
        question = request.form.get("question")
        option_a = request.form.get("option_a")
        option_b = request.form.get("option_b")
        option_c = request.form.get("option_c")
        option_d = request.form.get("option_d")
        correct_option = request.form.get("correct_option").upper()

        db = get_db_connection()
        cursor = db.cursor()
        sql = """
            INSERT INTO mock_tests
            (subject, chapter, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (subject, chapter, question, option_a, option_b, option_c, option_d, correct_option)
        cursor.execute(sql, values)
        db.commit()
        db.close()

        return "Question added successfully! <a href='/admin/mocktest'>Add another</a>"

    return render_template("admin_mocktest.html")


# -------------------
# Run the app
# -------------------
if __name__ == "__main__":
    app.run(debug=True)

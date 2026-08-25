from flask import Flask, render_template, request, session, redirect, url_for, make_response
import sqlite3
import secrets
import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key") 
app.jinja_env.add_extension("jinja2.ext.loopcontrols")

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("entery"))

@app.route("/", methods=["POST", "GET"])
def entery():
    if session.get("first"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        session["name"] = name
        session["password"] = password
        session["first"] = True
        session['show_hello'] = True
        return redirect(url_for("dashboard"))
    return render_template("entery.html")

@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():
    show_hello = session.pop('show_hello', False)
    name = session.get("name")
    db = sqlite3.connect("study.db")
    cursor = db.cursor()
    delete_mission = request.form.get("delete_mission")
    if delete_mission:
        cursor.execute("DELETE FROM owners WHERE name = ? and mission = ?",(name, delete_mission))
    db.commit()
    db.close()

    db = sqlite3.connect("study.db")
    cursor = db.cursor()
    delete_subject = request.form.get("delete_subject")
    if delete_subject:
        cursor.execute("DELETE FROM owners WHERE name = ? and subject = ?",(name, delete_subject))
    db.commit()
    db.close()

    db = sqlite3.connect("study.db")
    cursor = db.cursor()
    day = request.form.get("day")
    select_day = request.form.get("select_day")
    mission = request.form.get("mission")
    select_fav = request.form.get("select_fav")
    if mission and select_day:
        cursor.execute("INSERT INTO owners VALUES (?, ?, ?, ?, ?)",( name, "", mission, select_day, select_fav or ""))
    missions = cursor.execute(
    "SELECT mission, day FROM owners WHERE name = ? AND mission != ''",
    (name,)
    ).fetchall()
    db.commit()
    db.close()

    db = sqlite3.connect("study.db")
    cursor = db.cursor()
    if day:
        session["day"] = day
    day = session.get("day")
    new_subject = request.form.get("add_subject")
    subjects = cursor.execute(
        "SELECT subject FROM owners WHERE name = ? AND subject != '' AND mission = ''",
        (name,)
        ).fetchall()
    subject_names = [subject[0] for subject in subjects]
    if request.method == "POST":
            if new_subject and new_subject not in subject_names:
                cursor.execute("INSERT INTO owners VALUES (?, ?, ?, ?, ?)",(name, "", "", "", new_subject))
                db.commit()
    subjects = cursor.execute(
    "SELECT subject FROM owners WHERE name = ? AND subject != '' AND mission = ''",
    (name,)
    ).fetchall()

    subject_counts = {}
    for s in subjects:
        count = cursor.execute(
            "SELECT COUNT(*) FROM owners WHERE name = ? AND subject = ? AND mission != ''",
            (name, s[0])
        ).fetchone()[0]
        subject_counts[s[0]] = count

    db.close()

    print(mission)
    print(select_day)
    return render_template("index.html",
    day=day,
    subjects=subjects,
    subject_count=len(subjects),
    mission_count=len(missions),
    missions=missions,
    name=name,
    show_hello=show_hello,
    subject_counts=subject_counts
    )
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

from flask import Flask, render_template, request, session, redirect, url_for, make_response
import psycopg2
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key")
app.jinja_env.add_extension("jinja2.ext.loopcontrols")


def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))


def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS owners (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            subject TEXT DEFAULT '',
            mission TEXT DEFAULT '',
            day TEXT DEFAULT '',
            favorite TEXT DEFAULT ''
        )
    """)

    db.commit()
    cursor.close()
    db.close()


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
        session["show_hello"] = True

        return redirect(url_for("dashboard"))

    return render_template("entery.html")


@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():

    show_hello = session.pop("show_hello", False)
    name = session.get("name")

    db = get_db()
    cursor = db.cursor()

    delete_mission = request.form.get("delete_mission")

    if delete_mission:
        cursor.execute(
            "DELETE FROM owners WHERE name = %s AND mission = %s",
            (name, delete_mission)
        )

    db.commit()
    cursor.close()
    db.close()


    db = get_db()
    cursor = db.cursor()

    delete_subject = request.form.get("delete_subject")

    if delete_subject:
        cursor.execute(
            "DELETE FROM owners WHERE name = %s AND subject = %s",
            (name, delete_subject)
        )

    db.commit()
    cursor.close()
    db.close()


    db = get_db()
    cursor = db.cursor()

    day = request.form.get("day")
    select_day = request.form.get("select_day")
    mission = request.form.get("mission")
    select_fav = request.form.get("select_fav")

    if mission and select_day:
        cursor.execute(
            """
            INSERT INTO owners (name, subject, mission, day, favorite)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, "", mission, select_day, select_fav or "")
        )

    missions = cursor.execute(
        "SELECT mission, day FROM owners WHERE name = %s AND mission != ''",
        (name,)
    )

    missions = cursor.fetchall()

    db.commit()
    cursor.close()
    db.close()


    db = get_db()
    cursor = db.cursor()

    if day:
        session["day"] = day

    day = session.get("day")

    new_subject = request.form.get("add_subject")

    subjects = cursor.execute(
        """
        SELECT subject
        FROM owners
        WHERE name = %s
        AND subject != ''
        AND mission = ''
        """,
        (name,)
    )

    subjects = cursor.fetchall()

    subject_names = [subject[0] for subject in subjects]

    if request.method == "POST":

        if new_subject and new_subject not in subject_names:

            cursor.execute(
                """
                INSERT INTO owners (name, subject, mission, day, favorite)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, new_subject, "", "", "")
            )

            db.commit()

    subjects = cursor.execute(
        """
        SELECT subject
        FROM owners
        WHERE name = %s
        AND subject != ''
        AND mission = ''
        """,
        (name,)
    )

    subjects = cursor.fetchall()


    subject_counts = {}

    for s in subjects:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM owners
            WHERE name = %s
            AND subject = %s
            AND mission != ''
            """,
            (name, s[0])
        )

        count = cursor.fetchone()[0]

        subject_counts[s[0]] = count

    cursor.close()
    db.close()


    print(mission)
    print(select_day)

    return render_template(
        "index.html",
        day=day,
        subjects=subjects,
        subject_count=len(subjects),
        mission_count=len(missions),
        missions=missions,
        name=name,
        show_hello=show_hello,
        subject_counts=subject_counts
    )

init_db()
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )

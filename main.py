import os, requests
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, render_template, session
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms import validators, SubmitField

app = Flask(__name__)
load_dotenv()
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")


class InfoForm(FlaskForm):
    startdate = DateField(
        "Start Date", format="%Y-%m-%d", validators=(validators.DataRequired(),)
    )
    enddate = DateField(
        "End Date", format="%Y-%m-%d", validators=(validators.DataRequired(),)
    )
    submit = SubmitField("Submit ")


@app.route("/", methods=["GET", "POST"])
def index():
    form = InfoForm()
    startdate = session.get("startdate")
    enddate = session.get("enddate")

    if form.validate_on_submit():
        delta = form.enddate.data - form.startdate.data
        if delta.days < 0:
            form.enddate.errors.append("End date must be after start date.")

        elif delta.days > 7:
            form.enddate.errors.append("Date range cannot exceed 7 days.")
        else:
            session["startdate"] = form.startdate.data.strftime("%Y-%m-%d")
            session["enddate"] = form.enddate.data.strftime("%Y-%m-%d")
            return redirect(url_for("date"))
    return render_template(
        "index.html", form=form, startdate=startdate, enddate=enddate
    )


@app.route("/date", methods=["GET", "POST"])
def date():
    startdate = session.get("startdate")
    enddate = session.get("enddate")

    if not startdate or not enddate:
        return "No Dates selected"

    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={startdate}&end_date={enddate}&api_key={API_KEY}"
    response = requests.get(url)
    asteroid_info = response.json()
    print(asteroid_info)
    asteroids_by_date = {}

    for date, data in asteroid_info["near_earth_objects"].items():
        asteroids_by_date[date] = []
        for asteroid in data:
            approach = asteroid["close_approach_data"][0]
            asteroids_by_date[date].append(
                {
                    "name": asteroid["name"],
                    "diameter": asteroid["estimated_diameter"]["meters"][
                        "estimated_diameter_max"
                    ],
                    "hazardous": asteroid["is_potentially_hazardous_asteroid"],
                    "speed": float(
                        approach["relative_velocity"]["kilometers_per_hour"]
                    ),
                    "miss_distance": float(approach["miss_distance"]["kilometers"]),
                }
            )

    return render_template(
        "date.html",
        startdate=startdate,
        enddate=enddate,
        asteroids_by_date=asteroids_by_date,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
import sqlite3
import random

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from config import DATABASE_PATH, SECRET_KEY
from data.airports import AIRPORTS


app = Flask(__name__)
app.secret_key = SECRET_KEY


# ==========================
# DATABASE
# ==========================

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DATABASE_PATH):

        os.makedirs("database", exist_ok=True)

        conn = sqlite3.connect(DATABASE_PATH)

        with open(
            "database/schema.sql",
            "r",
            encoding="utf-8"
        ) as f:
            conn.executescript(f.read())

        conn.commit()
        conn.close()


init_db()


# ==========================
# FLIGHT DATA GENERATOR
# ==========================

AIRLINES = [
    "Air India",
    "IndiGo",
    "Akasa Air",
    "SpiceJet",
    "Vistara"
]

CITIES = [
    "Chennai",
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Kolkata",
    "Kochi",
    "Goa",
    "Pune",
    "Ahmedabad",
    "Jaipur",
    "Lucknow"
]


def generate_flights(airport_code, count=25):

    flights = []

    for i in range(count):

        flight_no = f"{random.choice(['AI','6E','UK','SG','QP'])}{random.randint(100,999)}"

        flights.append({
            "flight_no": flight_no,
            "airline": random.choice(AIRLINES),
            "source": random.choice(CITIES),
            "destination": random.choice(CITIES),
            "departure_time": f"{random.randint(1,12)}:{random.choice(['00','15','30','45'])} {'AM' if random.randint(0,1)==0 else 'PM'}",
            "arrival_time": f"{random.randint(1,12)}:{random.choice(['00','15','30','45'])} {'AM' if random.randint(0,1)==0 else 'PM'}",
            "gate": f"A{random.randint(1,20)}",
            "status": random.choice([
                "On Time",
                "Boarding",
                "Scheduled",
                "Delayed"
            ])
        })

    return flights


# ==========================
# AUTHENTICATION
# ==========================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing_user:
            flash("Email already registered.")
            conn.close()
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn.execute(
            """
            INSERT INTO users(name,email,password)
            VALUES(?,?,?)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("map_page"))

        flash("Invalid Email or Password")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================
# MAP PAGE
# ==========================

@app.route("/map")
def map_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "map.html",
        airports=AIRPORTS
    )


# ==========================
# AIRPORT DETAILS
# ==========================

@app.route("/airport/<airport_code>")
def airport_details(airport_code):

    if "user_id" not in session:
        return redirect(url_for("login"))

    airport = AIRPORTS.get(airport_code)

    if not airport:
        return redirect(url_for("map_page"))

    return render_template(
        "airport_details.html",
        airport=airport
    )


# ==========================
# ARRIVALS
# ==========================

@app.route("/airport/<airport_code>/arrivals")
def arrivals(airport_code):

    airport = AIRPORTS.get(airport_code)

    flights = generate_flights(
        airport_code,
        25
    )

    return render_template(
        "arrivals.html",
        airport=airport,
        flights=flights
    )


# ==========================
# DEPARTURES
# ==========================

@app.route("/airport/<airport_code>/departures")
def departures(airport_code):

    airport = AIRPORTS.get(airport_code)

    flights = generate_flights(
        airport_code,
        25
    )

    return render_template(
        "departures.html",
        airport=airport,
        flights=flights
    )


# ==========================
# FLIGHT DETAILS
# ==========================

@app.route("/airport/<airport_code>/flight-details")
def flight_details(airport_code):

    airport = AIRPORTS.get(airport_code)

    flights = generate_flights(
        airport_code,
        25
    )

    return render_template(
        "flight_details.html",
        airport=airport,
        flights=flights
    )


# ==========================
# CURRENT FLIGHTS
# ==========================

@app.route("/airport/<airport_code>/current-flights")
def current_flights(airport_code):

    airport = AIRPORTS.get(airport_code)

    flights = generate_flights(
        airport_code,
        20
    )

    return render_template(
        "current_flights.html",
        airport=airport,
        flights=flights
    )


# ==========================
# DELAYED FLIGHTS
# ==========================

@app.route("/airport/<airport_code>/delayed-flights")
def delayed_flights(airport_code):

    airport = AIRPORTS.get(airport_code)

    flights = []

    for flight in generate_flights(
        airport_code,
        25
    ):
        if flight["status"] == "Delayed":
            flights.append(flight)

    return render_template(
        "delayed_flights.html",
        airport=airport,
        flights=flights
    )


# ==========================
# TICKET AVAILABILITY
# ==========================

@app.route(
    "/airport/<airport_code>/tickets/<flight_no>"
)
def ticket_availability(
    airport_code,
    flight_no
):

    airport = AIRPORTS.get(airport_code)

    ticket_data = [
        {
            "class": "Economy",
            "seats": random.randint(20, 100),
            "price": random.randint(3500, 7000)
        },
        {
            "class": "Premium Economy",
            "seats": random.randint(10, 40),
            "price": random.randint(7000, 12000)
        },
        {
            "class": "Business",
            "seats": random.randint(2, 20),
            "price": random.randint(12000, 25000)
        }
    ]

    return render_template(
        "ticket_availability.html",
        airport=airport,
        flight_no=flight_no,
        tickets=ticket_data
    )

@app.route(
    "/airport/<airport_code>/book-ticket/<flight_no>",
    methods=["POST"]
)
def book_ticket(airport_code, flight_no):

    airport = AIRPORTS.get(airport_code)

    ticket_class = request.form["ticket_class"]
    quantity = int(request.form["quantity"])
    price = int(request.form["price"])

    total_price = quantity * price

    return render_template(
        "booking_confirmation.html",
        airport=airport,
        flight_no=flight_no,
        ticket_class=ticket_class,
        quantity=quantity,
        total_price=total_price
    )
# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    app.run(
        debug=True
    )
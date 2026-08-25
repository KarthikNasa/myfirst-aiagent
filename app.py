import os
import requests

from flask import Flask, render_template, request, jsonify
from google import genai


app = Flask(__name__)


# ============================================================
# GEMINI CLIENT
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    gemini_client = None


# ============================================================
# WEATHER TOOL
# ============================================================

def get_weather_data(city):
    """
    Weather Tool

    1. Finds the city coordinates.
    2. Gets current weather.
    3. Gets today's and tomorrow's forecast.
    """

    # --------------------------------------------------------
    # TOOL 1: Geocoding
    # --------------------------------------------------------

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}"
        "&count=1"
        "&language=en"
        "&format=json"
    )

    geo_response = requests.get(
        geo_url,
        timeout=10
    )

    geo_response.raise_for_status()

    geo_data = geo_response.json()

    if "results" not in geo_data:
        raise ValueError(
            f"City '{city}' was not found."
        )

    location = geo_data["results"][0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    city_name = location["name"]
    country = location.get("country", "")

    # --------------------------------------------------------
    # TOOL 2: Weather forecast
    # --------------------------------------------------------

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current="
        "temperature_2m,"
        "relative_humidity_2m,"
        "apparent_temperature,"
        "precipitation,"
        "weather_code,"
        "wind_speed_10m"
        "&daily="
        "weather_code,"
        "temperature_2m_max,"
        "temperature_2m_min,"
        "precipitation_probability_max,"
        "sunrise,"
        "sunset"
        "&forecast_days=7"
        "&timezone=auto"
    )

    weather_response = requests.get(
        weather_url,
        timeout=10
    )

    weather_response.raise_for_status()

    weather = weather_response.json()

    current = weather["current"]
    daily = weather["daily"]

    # --------------------------------------------------------
    # Return structured weather information
    # --------------------------------------------------------

    return {

        "location": {
            "city": city_name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude
        },

        "current": {
            "temperature":
                current["temperature_2m"],

            "humidity":
                current["relative_humidity_2m"],

            "feelsLike":
                current["apparent_temperature"],

            "precipitation":
                current["precipitation"],

            "weatherCode":
                current["weather_code"],

            "windSpeed":
                current["wind_speed_10m"]
        },

        "daily": {

            "date":
                daily["time"],

            "maxTemperature":
                daily["temperature_2m_max"],

            "minTemperature":
                daily["temperature_2m_min"],

            "rainProbability":
                daily["precipitation_probability_max"],

            "weatherCode":
                daily["weather_code"],

            "sunrise":
                daily["sunrise"],

            "sunset":
                daily["sunset"]
        }
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# NORMAL WEATHER API
# ============================================================

@app.route("/api/weather")
def weather_api():

    city = request.args.get("city")

    if not city:

        return jsonify({
            "error": "Please enter a city."
        }), 400

    try:

        weather = get_weather_data(city)

        return jsonify(weather)

    except Exception as e:

        print("Weather error:", e)

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# AI WEATHER AGENT
# ============================================================

@app.route("/api/agent", methods=["POST"])
def weather_agent():

    try:

        # ----------------------------------------------------
        # Check Gemini API key
        # ----------------------------------------------------

        if gemini_client is None:

            return jsonify({
                "error":
                    "Gemini API key is not configured."
            }), 500


        # ----------------------------------------------------
        # Get user request
        # ----------------------------------------------------

        data = request.get_json()

        city = data.get("city", "").strip()

        question = data.get(
            "question",
            ""
        ).strip()


        if not city:

            return jsonify({
                "error": "Please enter a city."
            }), 400


        if not question:

            return jsonify({
                "error": "Please enter a question."
            }), 400


        # ----------------------------------------------------
        # AGENT TOOL CALL
        #
        # The agent gets REAL weather data.
        # ----------------------------------------------------

        weather = get_weather_data(city)


        location = weather["location"]

        current = weather["current"]

        daily = weather["daily"]


        # ----------------------------------------------------
        # Prepare forecast information
        # ----------------------------------------------------

        forecast_lines = []

        for i in range(
            min(7, len(daily["date"]))
        ):

            forecast_lines.append(
                f"""
Date: {daily["date"][i]}
Minimum temperature: {daily["minTemperature"][i]}°C
Maximum temperature: {daily["maxTemperature"][i]}°C
Rain probability: {daily["rainProbability"][i]}%
Weather code: {daily["weatherCode"][i]}
"""
            )


        forecast_text = "\n".join(
            forecast_lines
        )


        # ----------------------------------------------------
        # AGENT PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are an intelligent Weather AI Agent.

Your job is to answer weather-related questions
using ONLY the real weather information supplied
by the weather tool below.

Do NOT invent weather information.

If the user asks about tomorrow, use the second
forecast day.

If the user asks about the next few days,
use the appropriate forecast days.

Give practical and easy-to-understand advice.

You can give recommendations about:

- outdoor activities
- travel
- clothing
- umbrellas
- heat
- rain
- wind
- morning/evening activities
- general weather planning

Always mention when your recommendation is based
on rain probability, temperature, wind, or another
weather factor.

Keep answers concise but useful.

------------------------------------------------
LOCATION
------------------------------------------------

City: {location["city"]}
Country: {location["country"]}

------------------------------------------------
CURRENT WEATHER
------------------------------------------------

Temperature:
{current["temperature"]}°C

Feels like:
{current["feelsLike"]}°C

Humidity:
{current["humidity"]}%

Wind speed:
{current["windSpeed"]} km/h

Precipitation:
{current["precipitation"]} mm

Weather code:
{current["weatherCode"]}

------------------------------------------------
7 DAY FORECAST
------------------------------------------------

{forecast_text}

------------------------------------------------
USER QUESTION
------------------------------------------------

{question}

------------------------------------------------

Answer the user's question based on
the weather information above.
"""


        # ----------------------------------------------------
        # CALL GEMINI
        # ----------------------------------------------------

        response = gemini_client.interactions.create(

            model="gemini-3.7-flash",

            input=prompt
        )


        # ----------------------------------------------------
        # Return AI answer
        # ----------------------------------------------------

        answer = response.output_text


        return jsonify({

            "answer": answer,

            "weather": weather

        })


    except Exception as e:

        print(
            "Agent error:",
            repr(e)
        )

        return jsonify({

            "error":
                "The Weather AI Agent failed: "
                + str(e)

        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=True

    )

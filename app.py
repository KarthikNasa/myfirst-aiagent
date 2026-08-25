from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/weather")
def weather():

    city = request.args.get("city")

    if not city:
        return jsonify({
            "error": "Please enter a city name"
        }), 400

    try:

        # -----------------------------------
        # 1. Find city coordinates
        # -----------------------------------

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}"
            "&count=1"
            "&language=en"
            "&format=json"
        )

        geo_response = requests.get(geo_url)

        geo_data = geo_response.json()

        if "results" not in geo_data:
            return jsonify({
                "error": "City not found"
            }), 404

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        # -----------------------------------
        # 2. Get weather
        # -----------------------------------

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
            "&timezone=auto"
        )

        weather_response = requests.get(weather_url)

        weather_data = weather_response.json()

        # -----------------------------------
        # 3. Return weather information
        # -----------------------------------

        result = {

            "location": {
                "city": location["name"],
                "country": location["country"],
                "latitude": latitude,
                "longitude": longitude
            },

            "current": {
                "temperature":
                    weather_data["current"]["temperature_2m"],

                "humidity":
                    weather_data["current"]["relative_humidity_2m"],

                "feelsLike":
                    weather_data["current"]["apparent_temperature"],

                "precipitation":
                    weather_data["current"]["precipitation"],

                "windSpeed":
                    weather_data["current"]["wind_speed_10m"],

                "weatherCode":
                    weather_data["current"]["weather_code"]
            },

            "daily": {
                "maxTemperature":
                    weather_data["daily"]["temperature_2m_max"][0],

                "minTemperature":
                    weather_data["daily"]["temperature_2m_min"][0],

                "rainProbability":
                    weather_data["daily"]
                    ["precipitation_probability_max"][0],

                "sunrise":
                    weather_data["daily"]["sunrise"][0],

                "sunset":
                    weather_data["daily"]["sunset"][0]
            }
        }

        return jsonify(result)

    except Exception as e:

        print(e)

        return jsonify({
            "error": "Unable to retrieve weather"
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

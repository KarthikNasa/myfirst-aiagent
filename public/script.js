const cityInput = document.getElementById("cityInput");
const weatherButton = document.getElementById("weatherButton");

const loading = document.getElementById("loading");
const error = document.getElementById("error");
const weatherResult = document.getElementById("weatherResult");


// Weather condition converter
function getWeatherCondition(code) {

    const conditions = {

        0: "Clear Sky",

        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Depositing Rime Fog",

        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",

        61: "Light Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",

        71: "Light Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",

        80: "Light Rain Showers",
        81: "Moderate Rain Showers",
        82: "Heavy Rain Showers",

        95: "Thunderstorm",

        96: "Thunderstorm with Hail",
        99: "Thunderstorm with Heavy Hail"
    };

    return conditions[code] || "Unknown";
}


// Format time
function formatTime(dateTime) {

    const date = new Date(dateTime);

    return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}


// Get weather
async function getWeather() {

    const city = cityInput.value.trim();

    if (!city) {

        showError("Please enter a city name.");

        return;
    }

    loading.classList.remove("hidden");

    error.classList.add("hidden");

    weatherResult.classList.add("hidden");

    try {

        const response = await fetch(
            `/api/weather?city=${encodeURIComponent(city)}`
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error || "Something went wrong"
            );
        }

        displayWeather(data);

    } catch (err) {

        console.error(err);

        showError(
            err.message ||
            "Unable to retrieve weather information."
        );

    } finally {

        loading.classList.add("hidden");
    }
}


// Display weather
function displayWeather(data) {

    document.getElementById("location").textContent =
        `${data.location.city}, ${data.location.country}`;

    document.getElementById("temperature").textContent =
        Math.round(data.current.temperature);

    document.getElementById("feelsLike").textContent =
        Math.round(data.current.feelsLike);

    document.getElementById("condition").textContent =
        getWeatherCondition(data.current.weatherCode);

    document.getElementById("humidity").textContent =
        `${data.current.humidity}%`;

    document.getElementById("wind").textContent =
        `${data.current.windSpeed} km/h`;

    document.getElementById("rain").textContent =
        `${data.daily.rainProbability}%`;

    document.getElementById("precipitation").textContent =
        `${data.current.precipitation} mm`;

    document.getElementById("sunrise").textContent =
        formatTime(data.daily.sunrise);

    document.getElementById("sunset").textContent =
        formatTime(data.daily.sunset);

    document.getElementById("minTemperature").textContent =
        Math.round(data.daily.minTemperature);

    document.getElementById("maxTemperature").textContent =
        Math.round(data.daily.maxTemperature);

    weatherResult.classList.remove("hidden");
}


// Display error
function showError(message) {

    error.textContent = message;

    error.classList.remove("hidden");

    weatherResult.classList.add("hidden");
}


// Button click
weatherButton.addEventListener(
    "click",
    getWeather
);


// Press Enter
cityInput.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            getWeather();
        }
    }
);


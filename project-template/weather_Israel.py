import tempfile
import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from mcp.server.fastmcp import FastMCP
from playwright.sync_api import sync_playwright

mcp = FastMCP("weather-Israel")

FORECAST_URL = "https://www.weather2day.co.il/forecast"

# File used to persist state between separate tool invocations
STATE_FILE = os.path.join(tempfile.gettempdir(), "weather_israel_state.json")

_executor = ThreadPoolExecutor(max_workers=1)

# Temporary browser instance - kept open only between select and get_content
_temp_browser = None
_temp_page = None

# English to Hebrew city name mapping
CITY_TRANSLATIONS = {
    "tel aviv": "תל אביב",
    "jerusalem": "ירושלים",
    "haifa": "חיפה",
    "beer sheva": "באר שבע",
    "beersheba": "באר שבע",
    "rishon lezion": "ראשון לציון",
    "petah tikva": "פתח תקווה",
    "ashdod": "אשדוד",
    "netanya": "נתניה",
    "bnei brak": "בני ברק",
    "holon": "חולון",
    "ramat gan": "רמת גן",
    "ashkelon": "אשקלון",
    "rehovot": "רחובות",
    "bat yam": "בת ים",
    "herzliya": "הרצליה",
    "kfar saba": "כפר סבא",
    "hadera": "חדרה",
    "modiin": "מודיעין",
    "nazareth": "נצרת",
    "lod": "לוד",
    "ramla": "רמלה",
    "nahariya": "נהריה",
    "raanana": "רעננה",
    "givatayim": "גבעתיים",
    "acre": "עכו",
    "akko": "עכו",
    "afula": "עפולה",
    "eilat": "אילת",
    "tiberias": "טבריה",
    "safed": "צפת",
    "zefat": "צפת",
    "dimona": "דימונה",
    "karmiel": "כרמיאל",
    "yavne": "יבנה",
    "sderot": "שדרות",
}


def _translate_city(city: str) -> str:
    """Translate English city name to Hebrew if needed"""
    city_lower = city.lower().strip()
    return CITY_TRANSLATIONS.get(city_lower, city)


def _save_state(data: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def _load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def _select_city_sync(city: str) -> str:
    """Runs in a thread — opens browser, searches city, selects first result"""
    global _temp_browser, _temp_page
    
    hebrew_city = _translate_city(city)
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(60000)
        page.goto(FORECAST_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        page.locator("#favorites").click()
        page.wait_for_timeout(1000)

        page.locator("#city_search").fill(hebrew_city)
        page.wait_for_selector("#city_searchautocomplete-list div", timeout=10000)
        page.locator("#city_searchautocomplete-list div").first.click()
        page.wait_for_timeout(3000)

        url = page.url
        
        # Keep browser open for get_content to use
        _temp_browser = browser
        _temp_page = page
        
        return url


def _get_content_sync(url: str) -> str:
    """Runs in a thread — opens browser, navigates to URL, returns page text"""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(60000)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        content = page.locator("body").inner_text()
        browser.close()
        return content


@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Opens a browser and navigates to the Israeli weather forecast site"""
    _save_state({"url": FORECAST_URL, "city": None})
    return f"Ready to fetch forecast from: {FORECAST_URL}"


@mcp.tool()
async def enter_weather_forecast_city_israel(city: str) -> str:
    """Types a city name into the search field on the forecast page.
    IMPORTANT: If the city name is in English, it will be automatically translated to Hebrew.
    Supported cities: Tel Aviv, Jerusalem, Haifa, Beer Sheva, Bnei Brak, and many more Israeli cities.

    Args:
        city: City name in Hebrew or English (e.g., 'Tel Aviv', 'Jerusalem', 'Haifa')
    """
    _save_state({"url": FORECAST_URL, "city": city})
    hebrew_city = _translate_city(city)
    return f"City '{city}' (Hebrew: '{hebrew_city}') saved"


@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Searches for the saved city and selects it from the suggestions dropdown"""
    state = _load_state()
    city = state.get("city")
    if not city:
        return "Error: no city entered yet. Call enter_weather_forecast_city_israel first."

    # Run Playwright in a thread to avoid event loop conflicts with MCP
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(_executor, _select_city_sync, city)

    _save_state({"url": url, "city": city})
    return f"City '{city}' selected, forecast page loaded"


@mcp.tool()
async def get_weather_forecast_content_israel() -> str:
    """Extracts the forecast page content as clean text for the LLM"""
    state = _load_state()
    url = state.get("url")
    if not url or url == FORECAST_URL:
        return "Error: no city selected yet. Call select_weather_forecast_city_israel first."

    # Run Playwright in a thread to avoid event loop conflicts with MCP
    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(_executor, _get_content_sync, url)

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return "\n".join(lines)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

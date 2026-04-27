from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, Browser, Page

mcp = FastMCP("weather-Israel")

FORECAST_URL = "https://www.weather2day.co.il/forecast"

# Global state — keeps the browser and page alive between tool calls,
# since each tool is a separate invocation and we need to resume from the same state
_browser: Browser | None = None
_page: Page | None = None


@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Opens a browser and navigates to the Israeli weather forecast site"""
    global _browser, _page

    # Launch playwright and open a visible browser window (headless=False)
    playwright = await async_playwright().start()
    _browser = await playwright.chromium.launch(headless=False)
    _page = await _browser.new_page()

    await _page.goto(FORECAST_URL)
    return f"הדפדפן נפתח בהצלחה: {FORECAST_URL}"


@mcp.tool()
async def enter_weather_forecast_city_israel(city: str) -> str:
    """Types a city name into the search field on the forecast page

    Args:
        city: City name in Hebrew or English
    """
    if _page is None:
        return "שגיאה: הדפדפן לא פתוח. יש להפעיל קודם את open_weather_forecast_israel"

    # Locate the search input by its placeholder and type the city name
    search_input = _page.get_by_placeholder("חפש עיר...")
    await search_input.fill(city)

    # Wait for the suggestions dropdown to appear
    await _page.wait_for_selector("ul.suggestions li", timeout=5000)
    return f"העיר '{city}' הוזנה בשדה החיפוש"


@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Clicks the first city in the suggestions dropdown"""
    if _page is None:
        return "שגיאה: הדפדפן לא פתוח. יש להפעיל קודם את open_weather_forecast_israel"

    # Click the first item in the suggestions dropdown
    first_result = _page.locator("ul.suggestions li").first
    await first_result.click()

    # Wait for the forecast page to fully load after selection
    await _page.wait_for_load_state("networkidle")
    return "העיר נבחרה, דף התחזית נטען"


@mcp.tool()
async def get_weather_forecast_content_israel() -> str:
    """Extracts the forecast page content as clean text for the LLM"""
    if _page is None:
        return "שגיאה: הדפדפן לא פתוח. יש להפעיל קודם את open_weather_forecast_israel"

    # inner_text() returns only the visible text, stripped of all HTML tags —
    # exactly what the LLM needs to understand the page content
    content = await _page.locator("body").inner_text()

    # Basic cleanup — remove blank lines
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return "\n".join(lines)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

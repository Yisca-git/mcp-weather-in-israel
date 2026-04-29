# 🌤️ MCP Weather Israel

MCP Server for Israeli weather forecasts with browser automation using Playwright.

## 📋 Project Purpose

This project implements an **MCP (Model Context Protocol) Server** that enables LLMs to fetch weather forecasts from Israeli websites using browser automation.

**What makes it special?**
- 🦚 Fetches data directly from browser (not a boring API)
- 🇮🇱 Support for Israeli cities
- 🔄 Automatic translation from English to Hebrew
- 🤖 Full LLM integration via MCP

## 🛠️ Tech Stack

- **MCP SDK** - Anthropic's communication protocol
- **Playwright** - Browser automation (Chrome)
- **Groq** - LLM API (llama-3.1-8b-instant)
- **Python 3.13** - Programming language

## 📦 Installation

### Prerequisites
- Python 3.13+
- uv (package manager)

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd mcp-weather-israel/project-template
```

2. **Install dependencies**
```bash
uv sync
```

3. **Install Chromium browser**
```bash
uv run playwright install chromium
```

4. **Configure API Key**
Edit the `.env` file and add your API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

## 🚀 Running

Start the Host:
```bash
uv run host.py
```

You'll see:
```
MCP Client Started!
Type your queries or 'quit' to exit.

Query: 
```

## 💬 Example Queries

### Basic Questions
```
what the weather for Tel Aviv?
what the weather for Jerusalem?
what the weather for Haifa?
```

### Additional Supported Cities
```
what the weather for Bnei Brak?
what the weather for Beer Sheva?
what the weather for Eilat?
what the weather for Netanya?
what the weather for Ashdod?
```

### Complex Questions
```
Compare the weather in Tel Aviv and Jerusalem
Is it going to rain in Haifa today?
What's the temperature in Beer Sheva?
```

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  host.py (ChatHost)             │
│  - Manages chat                 │
│  - Connects to LLM (Groq)       │
│  - Routes tool calls            │
└──────┬──────────────────────────┘
       │
       ├──────────────┬─────────────────┐
       ▼              ▼                 ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ client.py   │ │ client.py    │ │ client.py    │
│ (USA MCP)   │ │ (Israel MCP) │ │ (Future MCP) │
└──────┬──────┘ └──────┬───────┘ └──────────────┘
       │                │
       ▼                ▼
┌──────────────┐ ┌──────────────────────────────┐
│weather_USA.py│ │weather_Israel.py             │
│- API based   │ │- Playwright based            │
│- 2 tools     │ │- 4 tools                     │
└──────────────┘ │- English→Hebrew translation  │
                 │- Content extraction          │
                 └──────────────────────────────┘
```

## 🔧 Available Tools

### MCP Israel (weather_Israel.py)

1. **open_weather_forecast_israel()**
   - Initializes the forecast fetching process

2. **enter_weather_forecast_city_israel(city: str)**
   - Receives city name (English or Hebrew)
   - Automatically translates to Hebrew

3. **select_weather_forecast_city_israel()**
   - Opens browser
   - Searches for the city on the website
   - Selects the first result

4. **get_weather_forecast_content_israel()**
   - Extracts forecast page content
   - Cleans and returns text to LLM

### MCP USA (weather_USA.py)

1. **get_forecast_in_USA(latitude, longitude)**
   - Forecast by coordinates

2. **get_alerts_in_USA(state)**
   - Weather alerts for a state

## 📝 Project Files

| File | Description |
|------|-------------|
| `host.py` | Central host - manages chat and connects LLM to MCPs |
| `client.py` | Generic MCP Client - connects to MCP Server |
| `weather_Israel.py` | MCP Server for Israel with Playwright |
| `weather_USA.py` | MCP Server for USA with API |
| `pyproject.toml` | Project configuration and dependencies |
| `.env` | Environment variables (API keys) |

## 🌍 City Translation

The project supports automatic translation of 40+ Israeli cities:

```python
"tel aviv" → "תל אביב"
"jerusalem" → "ירושלים"
"haifa" → "חיפה"
"beer sheva" → "באר שבע"
"bnei brak" → "בני ברק"
# and more...
```

## 🐛 Troubleshooting

### Browser doesn't open
```bash
uv run playwright install chromium
```

### Rate Limit Error
Wait 24 hours or upgrade your Groq plan.

### City not found
Ensure the English name is correct or use Hebrew directly.

## 🎯 Learning & Extension

**What you learned in this project:**
- ✅ Develop MCP Server from scratch
- ✅ Browser automation with Playwright
- ✅ LLM integration with tools
- ✅ State management between tool calls
- ✅ Translation and text processing

**Ideas for extension:**
- 🔮 Add support for more cities
- 📊 Extract charts and images from pages
- 🌐 Add MCP servers for other countries
- 🤖 Improve content analysis with RAG

## 📄 License

Educational project - free to use and learn.

## 🙏 Credits

- [Anthropic](https://www.anthropic.com/) - MCP Protocol
- [Microsoft Playwright](https://playwright.dev/) - Browser Automation
- [Groq](https://groq.com/) - Fast LLM API
- [weather2day.co.il](https://www.weather2day.co.il/) - Data source

---

**Created as part of AI Engineer course** 🎓

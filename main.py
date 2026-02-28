from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY", "")
if (not openai_api_key) or ("placeholder" in openai_api_key.lower()):
    if os.getenv("DEEPSEEK_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["DEEPSEEK_API_KEY"]
    elif os.getenv("OPENROUTER_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["backend_url"] = "https://api.deepseek.com/v1"
config["deep_think_llm"] = "deepseek-chat"
config["quick_think_llm"] = "deepseek-chat"
config["max_debate_rounds"] = 1

# Configure data vendors
config["data_vendors"] = {
    "core_stock_apis": "akshare,yfinance",
    "technical_indicators": "akshare,yfinance",
    "fundamental_data": "akshare",
    "news_data": "akshare",
}
config["tool_vendors"] = {
    "get_global_news": "google",
}

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("600519.SH", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns

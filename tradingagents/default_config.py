import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", "./data"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": os.getenv("TRADINGAGENTS_LLM_PROVIDER", "openai"),
    "deep_think_llm": os.getenv("TRADINGAGENTS_DEEP_THINK_LLM", "deepseek-chat"),
    "quick_think_llm": os.getenv("TRADINGAGENTS_QUICK_THINK_LLM", "deepseek-chat"),
    "backend_url": os.getenv("TRADINGAGENTS_BACKEND_URL", "https://api.deepseek.com/v1"),
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": os.getenv(
            "TRADINGAGENTS_CORE_STOCK_APIS_VENDOR", "akshare,yfinance"
        ),
        "technical_indicators": os.getenv(
            "TRADINGAGENTS_TECHNICAL_INDICATORS_VENDOR", "akshare,yfinance"
        ),
        "fundamental_data": os.getenv(
            "TRADINGAGENTS_FUNDAMENTAL_DATA_VENDOR", "akshare"
        ),
        "news_data": os.getenv("TRADINGAGENTS_NEWS_DATA_VENDOR", "akshare"),
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        "get_global_news": os.getenv("TRADINGAGENTS_GET_GLOBAL_NEWS_VENDOR", "google"),
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
    },
}

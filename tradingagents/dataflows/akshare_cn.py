from datetime import datetime, date

import pandas as pd
import os


def _to_yyyymmdd(d: str) -> str:
    datetime.strptime(d, "%Y-%m-%d")
    return d.replace("-", "")


def _normalize_symbol_6digits(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.endswith((".SZ", ".SH", ".SS")):
        s = s.split(".")[0]
    if s.startswith(("SH", "SZ")) and len(s) == 8 and s[2:].isdigit():
        return s[2:]
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) != 6:
        raise ValueError(f"Unsupported ticker format: {symbol}")
    return digits


def _resolve_symbol_6digits(symbol: str) -> str:
    try:
        return _normalize_symbol_6digits(symbol)
    except Exception:
        pass

    import akshare as ak
    from .config import get_config

    query = symbol.strip()
    if not query:
        raise ValueError(f"Unsupported ticker format: {symbol}")

    config = get_config()
    cache_dir = config.get("data_cache_dir") or config.get("data_dir") or "./data"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "akshare_a_code_name.csv")

    df = None
    if os.path.exists(cache_path):
        try:
            df = pd.read_csv(cache_path, dtype=str)
        except Exception:
            df = None

    if df is None or df.empty:
        if hasattr(ak, "stock_info_a_code_name"):
            try:
                df = ak.stock_info_a_code_name()
            except Exception:
                df = None

    if df is None or df.empty:
        raise ValueError(f"Unsupported ticker format: {symbol}")

    code_col = next((c for c in ["code", "代码"] if c in df.columns), None)
    name_col = next((c for c in ["name", "名称"] if c in df.columns), None)
    if code_col is None or name_col is None:
        raise ValueError(f"Unsupported ticker format: {symbol}")

    df = df[[code_col, name_col]].copy()
    df[code_col] = df[code_col].astype(str).str.zfill(6)
    df[name_col] = df[name_col].astype(str)

    if not os.path.exists(cache_path):
        try:
            df.to_csv(cache_path, index=False)
        except Exception:
            pass

    exact = df[df[name_col] == query]
    if len(exact) == 1:
        return str(exact.iloc[0][code_col])

    contains = df[df[name_col].str.contains(query, na=False)]
    if len(contains) == 1:
        return str(contains.iloc[0][code_col])

    raise ValueError(f"Unsupported ticker format: {symbol}")


def get_stock_data_akshare(symbol: str, start_date: str, end_date: str) -> str:
    import akshare as ak

    code = _resolve_symbol_6digits(symbol)
    df = ak.stock_zh_a_hist(
        symbol=code, period="daily", start_date=_to_yyyymmdd(start_date), end_date=_to_yyyymmdd(end_date), adjust=""
    )
    if df is None or df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    df = df.copy()
    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期")
        df["Date"] = df["日期"].dt.strftime("%Y-%m-%d")
    else:
        df["Date"] = ""

    rename_map = {
        "开盘": "Open",
        "最高": "High",
        "最低": "Low",
        "收盘": "Close",
        "成交量": "Volume",
        "成交额": "Amount",
    }
    for src, dst in rename_map.items():
        if src in df.columns:
            df[dst] = df[src]

    out_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Amount"]
    out_cols = [c for c in out_cols if c in df.columns]
    out_df = df[out_cols]

    header = f"# Stock data for {code} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(out_df)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + out_df.to_csv(index=False)


def _try_call_df(func, kwargs_list: list[dict]) -> pd.DataFrame | None:
    for kwargs in kwargs_list:
        try:
            df = func(**kwargs)
        except Exception:
            continue
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return None


def _try_call_df_by_names(module, func_names: list[str], kwargs_list: list[dict]) -> pd.DataFrame | None:
    for name in func_names:
        if not hasattr(module, name):
            continue
        func = getattr(module, name)
        df = _try_call_df(func, kwargs_list)
        if df is not None and not df.empty:
            return df
    return None


def get_fundamentals_akshare(ticker: str, curr_date: str) -> str:
    import akshare as ak

    code = _resolve_symbol_6digits(ticker)

    parts: list[str] = [f"## AkShare fundamentals for {code} (as of {curr_date})\n"]

    if hasattr(ak, "stock_financial_analysis_indicator_em"):
        df = _try_call_df(
            ak.stock_financial_analysis_indicator_em,
            [{"symbol": code}],
        )
        if df is not None and not df.empty:
            parts.append("### Financial Analysis Indicators\n")
            parts.append(df.head(20).to_csv(index=False))

    if hasattr(ak, "stock_financial_abstract"):
        df = _try_call_df(ak.stock_financial_abstract, [{"symbol": code}])
        if df is not None and not df.empty:
            parts.append("### Financial Abstract\n")
            parts.append(df.head(20).to_csv(index=False))

    if len(parts) == 1:
        raise RuntimeError("AkShare fundamentals fetch failed")
    return "\n".join(parts)


def get_balance_sheet_akshare(ticker: str, freq: str = "quarterly", curr_date: str | None = None) -> str:
    import akshare as ak

    code = _resolve_symbol_6digits(ticker)
    as_of = curr_date or date.today().strftime("%Y-%m-%d")
    parts: list[str] = [f"## AkShare balance sheet for {code} (as of {as_of})\n"]

    df = _try_call_df_by_names(
        ak,
        [
            "stock_balance_sheet_by_report_em",
            "stock_balance_sheet_by_quarterly_em",
            "stock_balance_sheet_by_yearly_em",
            "stock_zcfz_em",
        ],
        [{"symbol": code}],
    )
    if df is not None and not df.empty:
        return "\n".join(parts) + "\n" + df.head(30).to_csv(index=False)
    raise RuntimeError("AkShare balance sheet fetch failed")


def get_income_statement_akshare(ticker: str, freq: str = "quarterly", curr_date: str | None = None) -> str:
    import akshare as ak

    code = _resolve_symbol_6digits(ticker)
    as_of = curr_date or date.today().strftime("%Y-%m-%d")
    parts: list[str] = [f"## AkShare income statement for {code} (as of {as_of})\n"]

    df = _try_call_df_by_names(
        ak,
        [
            "stock_profit_sheet_by_report_em",
            "stock_profit_sheet_by_quarterly_em",
            "stock_profit_sheet_by_yearly_em",
            "stock_lrb_em",
        ],
        [{"symbol": code}],
    )
    if df is not None and not df.empty:
        return "\n".join(parts) + "\n" + df.head(30).to_csv(index=False)
    raise RuntimeError("AkShare income statement fetch failed")


def get_cashflow_akshare(ticker: str, freq: str = "quarterly", curr_date: str | None = None) -> str:
    import akshare as ak

    code = _resolve_symbol_6digits(ticker)
    as_of = curr_date or date.today().strftime("%Y-%m-%d")
    parts: list[str] = [f"## AkShare cashflow for {code} (as of {as_of})\n"]

    df = _try_call_df_by_names(
        ak,
        [
            "stock_cash_flow_sheet_by_report_em",
            "stock_cash_flow_sheet_by_quarterly_em",
            "stock_cash_flow_sheet_by_yearly_em",
            "stock_xjll_em",
        ],
        [{"symbol": code}],
    )
    if df is not None and not df.empty:
        return "\n".join(parts) + "\n" + df.head(30).to_csv(index=False)
    raise RuntimeError("AkShare cashflow fetch failed")


def get_news_akshare(ticker: str, start_date: str, end_date: str) -> str:
    import akshare as ak

    code = _resolve_symbol_6digits(ticker)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    if not hasattr(ak, "stock_news_em"):
        raise RuntimeError("AkShare news function stock_news_em not available")

    df = _try_call_df(ak.stock_news_em, [{"symbol": code}])
    if df is None or df.empty:
        return ""

    df = df.copy()
    time_col = None
    for c in ["发布时间", "时间", "日期", "publish_time", "datetime", "date"]:
        if c in df.columns:
            time_col = c
            break

    if time_col:
        dt_series = pd.to_datetime(df[time_col], errors="coerce").dt.date
        df = df[(dt_series >= start_dt) & (dt_series <= end_dt)]

    if df.empty:
        return ""

    cols = df.columns.tolist()
    title_col = next((c for c in cols if c in ["标题", "title", "新闻标题"]), None)
    url_col = next((c for c in cols if c in ["链接", "url", "新闻链接"]), None)

    items: list[str] = [f"## {code} News (AkShare) from {start_date} to {end_date}\n"]
    for _, row in df.head(50).iterrows():
        title = str(row[title_col]) if title_col else ""
        link = str(row[url_col]) if url_col else ""
        ts = str(row[time_col]) if time_col else ""
        line = " - ".join([p for p in [ts, title, link] if p and p != "nan"])
        if line:
            items.append(line)
    return "\n".join(items)


# ============================================================================
# Technical Indicators (based on AkShare stock data + stockstats)
# ============================================================================

INDICATOR_DESCRIPTIONS = {
    "close_50_sma": (
        "50 SMA: A medium-term trend indicator. "
        "Usage: Identify trend direction and serve as dynamic support/resistance. "
        "Tips: It lags price; combine with faster indicators for timely signals."
    ),
    "close_200_sma": (
        "200 SMA: A long-term trend benchmark. "
        "Usage: Confirm overall market trend and identify golden/death cross setups. "
        "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
    ),
    "close_10_ema": (
        "10 EMA: A responsive short-term average. "
        "Usage: Capture quick shifts in momentum and potential entry points. "
        "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
    ),
    "macd": (
        "MACD: Computes momentum via differences of EMAs. "
        "Usage: Look for crossovers and divergence as signals of trend changes. "
        "Tips: Confirm with other indicators in low-volatility or sideways markets."
    ),
    "macds": (
        "MACD Signal: An EMA smoothing of the MACD line. "
        "Usage: Use crossovers with the MACD line to trigger trades. "
        "Tips: Should be part of a broader strategy to avoid false positives."
    ),
    "macdh": (
        "MACD Histogram: Shows the gap between the MACD line and its signal. "
        "Usage: Visualize momentum strength and spot divergence early. "
        "Tips: Can be volatile; complement with additional filters in fast-moving markets."
    ),
    "rsi": (
        "RSI: Measures momentum to flag overbought/oversold conditions. "
        "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
        "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
    ),
    "boll": (
        "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
        "Usage: Acts as a dynamic benchmark for price movement. "
        "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
    ),
    "boll_ub": (
        "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
        "Usage: Signals potential overbought conditions and breakout zones. "
        "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
    ),
    "boll_lb": (
        "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
        "Usage: Indicates potential oversold conditions. "
        "Tips: Use additional analysis to avoid false reversal signals."
    ),
    "atr": (
        "ATR: Averages true range to measure volatility. "
        "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
        "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
    ),
    "vwma": (
        "VWMA: A moving average weighted by volume. "
        "Usage: Confirm trends by integrating price action with volume data. "
        "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
    ),
    "mfi": (
        "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
        "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
        "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
    ),
}


def _get_akshare_ohlcv_df(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch OHLCV data from AkShare and return a DataFrame ready for stockstats."""
    import akshare as ak

    code = _resolve_symbol_6digits(symbol)
    df = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=_to_yyyymmdd(start_date),
        end_date=_to_yyyymmdd(end_date),
        adjust="qfq",  # 前复权 for technical analysis
    )
    if df is None or df.empty:
        raise RuntimeError(f"No data found for symbol '{symbol}' between {start_date} and {end_date}")

    df = df.copy()
    # Rename Chinese columns to English for stockstats compatibility
    rename_map = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
    }
    df = df.rename(columns=rename_map)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def get_indicators_akshare(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int,
) -> str:
    """
    Calculate technical indicators for A-share stocks using AkShare data + stockstats.
    
    Args:
        symbol: A-share ticker (e.g., '600519.SH', '600519', '贵州茅台')
        indicator: Technical indicator name (e.g., 'rsi', 'macd', 'close_50_sma')
        curr_date: Current date in YYYY-MM-DD format
        look_back_days: Number of days to display in the result
    
    Returns:
        Formatted string with indicator values for the date range
    """
    from stockstats import wrap
    from dateutil.relativedelta import relativedelta

    if indicator not in INDICATOR_DESCRIPTIONS:
        raise ValueError(
            f"Indicator '{indicator}' is not supported. Please choose from: {list(INDICATOR_DESCRIPTIONS.keys())}"
        )

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    display_start = curr_date_dt - relativedelta(days=look_back_days)

    # Fetch enough historical data for indicator calculation (need more data for longer SMAs)
    # For 200 SMA we need at least 200+ trading days, so fetch ~2 years of data
    data_start = curr_date_dt - relativedelta(years=2)
    data_start_str = data_start.strftime("%Y-%m-%d")

    try:
        df = _get_akshare_ohlcv_df(symbol, data_start_str, curr_date)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch AkShare data: {e}")

    if df.empty:
        raise RuntimeError(f"No data available for {symbol}")

    # Save date column before wrapping with stockstats
    date_series = df["date"].dt.strftime("%Y-%m-%d").tolist()
    
    # Use stockstats to calculate the indicator
    stock_df = wrap(df)
    try:
        indicator_values = stock_df[indicator].tolist()  # Trigger stockstats calculation and get values
    except Exception as e:
        raise RuntimeError(f"Failed to calculate indicator '{indicator}': {e}")

    # Create indicator dictionary mapping date strings to values
    indicator_dict = dict(zip(date_series, indicator_values))

    # Generate results for the display range
    date_values = []
    current_dt = curr_date_dt
    while current_dt >= display_start:
        date_str = current_dt.strftime("%Y-%m-%d")
        if date_str in indicator_dict:
            value = indicator_dict[date_str]
            if pd.isna(value):
                date_values.append((date_str, "N/A"))
            else:
                date_values.append((date_str, f"{value:.4f}"))
        else:
            date_values.append((date_str, "N/A: Not a trading day (weekend or holiday)"))
        current_dt = current_dt - relativedelta(days=1)

    # Build result string
    ind_string = "\n".join(f"{d}: {v}" for d, v in date_values)
    description = INDICATOR_DESCRIPTIONS.get(indicator, "No description available.")

    result_str = (
        f"## {indicator} values from {display_start.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        f"{ind_string}\n\n"
        f"{description}"
    )
    return result_str

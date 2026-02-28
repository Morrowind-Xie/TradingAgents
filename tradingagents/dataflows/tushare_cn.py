import os
from datetime import datetime, date, timedelta

import pandas as pd


def _to_yyyymmdd(d: str) -> str:
    datetime.strptime(d, "%Y-%m-%d")
    return d.replace("-", "")


def _normalize_ts_code(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.endswith(".SS"):
        s = s[:-3] + ".SH"
    if s.endswith(".SZ") or s.endswith(".SH"):
        parts = s.split(".")
        if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 6:
            return s
        raise ValueError(f"Unsupported ticker format: {symbol}")
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) != 6:
        raise ValueError(f"Unsupported ticker format: {symbol}")
    if digits.startswith(("60", "68", "90")):
        return f"{digits}.SH"
    return f"{digits}.SZ"


def _get_pro():
    import tushare as ts

    token = os.getenv("TUSHARE_TOKEN") or os.getenv("TS_TOKEN")
    if not token:
        raise RuntimeError("Missing TUSHARE_TOKEN (or TS_TOKEN) in environment")
    ts.set_token(token)
    return ts.pro_api(token)


def _df_to_csv(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return ""
    return df.to_csv(index=False)


def get_stock_data_tushare(symbol: str, start_date: str, end_date: str) -> str:
    pro = _get_pro()
    ts_code = _normalize_ts_code(symbol)

    df = pro.daily(
        ts_code=ts_code,
        start_date=_to_yyyymmdd(start_date),
        end_date=_to_yyyymmdd(end_date),
    )
    if df is None or df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date")
    df = df.rename(
        columns={
            "trade_date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "vol": "Volume",
            "amount": "Amount",
        }
    )
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    cols = [
        c
        for c in ["Date", "Open", "High", "Low", "Close", "Volume", "Amount"]
        if c in df.columns
    ]
    df = df[cols]

    header = f"# Stock data for {ts_code} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(df)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + df.to_csv(index=False)


def _pick_latest_trade_date(pro, ts_code: str, curr_date: str) -> str | None:
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    start_dt = end_dt - timedelta(days=45)
    df = pro.daily_basic(
        ts_code=ts_code,
        start_date=start_dt.strftime("%Y%m%d"),
        end_date=end_dt.strftime("%Y%m%d"),
    )
    if df is None or df.empty or "trade_date" not in df.columns:
        return None
    trade_date = pd.to_datetime(df["trade_date"]).max()
    if pd.isna(trade_date):
        return None
    return trade_date.strftime("%Y%m%d")


def _latest_period_end(curr_date: str, freq: str) -> str:
    curr = datetime.strptime(curr_date, "%Y-%m-%d").date()
    if freq == "annual":
        year_end = date(curr.year, 12, 31)
        if curr < year_end:
            year_end = date(curr.year - 1, 12, 31)
        return year_end.strftime("%Y%m%d")

    quarter_ends = [
        date(curr.year, 3, 31),
        date(curr.year, 6, 30),
        date(curr.year, 9, 30),
        date(curr.year, 12, 31),
    ]
    latest = max(
        [d for d in quarter_ends if d <= curr], default=date(curr.year - 1, 12, 31)
    )
    return latest.strftime("%Y%m%d")


def get_fundamentals_tushare(ticker: str, curr_date: str) -> str:
    pro = _get_pro()
    ts_code = _normalize_ts_code(ticker)
    trade_date = _pick_latest_trade_date(pro, ts_code, curr_date) or _to_yyyymmdd(
        curr_date
    )
    period = _latest_period_end(curr_date, "quarterly")

    parts: list[str] = [f"## Tushare fundamentals for {ts_code} (as of {trade_date})\n"]

    company = pro.stock_company(ts_code=ts_code)
    if company is not None and not company.empty:
        parts.append("### Company Profile\n")
        parts.append(_df_to_csv(company))

    daily_basic = pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
    if daily_basic is not None and not daily_basic.empty:
        parts.append("### Daily Basic\n")
        parts.append(_df_to_csv(daily_basic))

    fina_indicator = pro.fina_indicator(ts_code=ts_code, period=period)
    if fina_indicator is not None and not fina_indicator.empty:
        parts.append(f"### Financial Indicators (period={period})\n")
        parts.append(_df_to_csv(fina_indicator))

    return "\n".join(p for p in parts if p)


def get_balance_sheet_tushare(
    ticker: str, freq: str = "quarterly", curr_date: str | None = None
) -> str:
    pro = _get_pro()
    ts_code = _normalize_ts_code(ticker)
    as_of = curr_date or date.today().strftime("%Y-%m-%d")
    period = _latest_period_end(as_of, "annual" if freq == "annual" else "quarterly")
    df = pro.balancesheet(ts_code=ts_code, period=period)
    if df is None or df.empty:
        return f"No balance sheet data for {ts_code} (period={period})"
    return (
        f"## Tushare balance sheet for {ts_code} (period={period})\n\n"
        + df.to_csv(index=False)
    )


def get_cashflow_tushare(
    ticker: str, freq: str = "quarterly", curr_date: str | None = None
) -> str:
    pro = _get_pro()
    ts_code = _normalize_ts_code(ticker)
    as_of = curr_date or date.today().strftime("%Y-%m-%d")
    period = _latest_period_end(as_of, "annual" if freq == "annual" else "quarterly")
    df = pro.cashflow(ts_code=ts_code, period=period)
    if df is None or df.empty:
        return f"No cashflow data for {ts_code} (period={period})"
    return (
        f"## Tushare cashflow for {ts_code} (period={period})\n\n"
        + df.to_csv(index=False)
    )


def get_income_statement_tushare(
    ticker: str, freq: str = "quarterly", curr_date: str | None = None
) -> str:
    pro = _get_pro()
    ts_code = _normalize_ts_code(ticker)
    as_of = curr_date or date.today().strftime("%Y-%m-%d")
    period = _latest_period_end(as_of, "annual" if freq == "annual" else "quarterly")
    df = pro.income(ts_code=ts_code, period=period)
    if df is None or df.empty:
        return f"No income statement data for {ts_code} (period={period})"
    return (
        f"## Tushare income statement for {ts_code} (period={period})\n\n"
        + df.to_csv(index=False)
    )

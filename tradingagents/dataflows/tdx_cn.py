"""
通达信 (TDX) 数据源适配器
为 TradingAgents 提供 A 股数据：
- K线行情 (OHLCV)
- 基本面 (PE/ROE/EPS)
- 技术指标（委托给 stockstats）
- 新闻（委托给 AkShare）

使用前提：通达信量化客户端已启动（仅行情/基本面需要）
"""
import os, sys
from datetime import datetime, timedelta
import pandas as pd


# ---- 符号标准化 ----

def _normalize_tdx_symbol(symbol: str) -> str:
    """转为通达信标准格式：6位代码.SH 或 .SZ"""
    s = symbol.strip().upper()
    if s.endswith((".SZ", ".SH", ".SS")):
        return s
    # 纯数字6位代码
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) != 6:
        raise ValueError(f"不支持的股票代码格式: {symbol}")
    if digits.startswith(("6", "5", "9")):
        return f"{digits}.SH"
    return f"{digits}.SZ"


# ---- TQ 连接管理 ----

_tq = None

def _get_tq():
    """懒加载 TQ 连接"""
    global _tq
    if _tq is not None:
        return _tq
    try:
        from tqcenter import tq
        tq.initialize(__file__)
        _tq = tq
        return tq
    except ImportError:
        print("[TDX] tqcenter 未安装，请确认通达信量化环境配置正确")
        return None
    except Exception as e:
        print(f"[TDX] TQ 连接失败: {e}")
        return None


# ---- 行情数据 ----

def get_stock_data_tdx(
    symbol: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """获取 A 股日线 OHLCV 数据"""
    code = _normalize_tdx_symbol(symbol)
    tq = _get_tq()
    if tq is None:
        raise RuntimeError("TDX 数据源不可用")

    start = start_date.replace("-", "")
    end = end_date.replace("-", "")
    fields = ['Open', 'High', 'Low', 'Close', 'Volume']

    try:
        df_raw = tq.get_market_data(
            field_list=fields,
            stock_list=[code],
            start_time=start,
            end_time=end,
            period='1d',
            dividend_type='front',
            fill_data=True,
        )
        result = pd.DataFrame(index=pd.to_datetime(df_raw.index))
        for f in fields:
            col_df = tq.price_df(df_raw, f, column_names=[code])
            result[f.lower()] = col_df[code]
        result.index.name = 'date'
        return result
    except Exception as e:
        raise RuntimeError(f"TDX 获取行情失败 {code}: {e}")


# ---- 基本面数据 ----

def get_fundamentals_tdx(symbol: str) -> dict:
    """获取基本面指标：ROE, EPS, PE, PB, 净利润"""
    code = _normalize_tdx_symbol(symbol)
    tq = _get_tq()
    if tq is None:
        raise RuntimeError("TDX 数据源不可用")

    try:
        info = tq.get_stock_info(stock_code=code, field_list=[])
        more = tq.get_more_info(stock_code=code, field_list=[])
        snap = tq.get_market_snapshot(stock_code=code, field_list=[])

        return {
            "Name": info.get("Name", symbol),
            "Price": float(snap.get("Now", snap.get("LastClose", 0))),
            "PE": float(more.get("StaticPE_TTM", 0) or 0),
            "PB": float(more.get("PB_MRQ", 0) or 0),
            "ROE": float(info.get("J_jyl", 0) or 0),
            "EPS": float(info.get("J_mgsy", 0) or 0),
            "NetProfit": float(info.get("J_jly", 0) or 0),
        }
    except Exception as e:
        raise RuntimeError(f"TDX 获取基本面失败 {code}: {e}")


# ---- 财务报表（委托给 AkShare） ----

def _fallback_to_akshare(symbol: str, fn_name: str):
    """回退到 AkShare"""
    from .akshare_cn import (
        get_balance_sheet_akshare,
        get_cashflow_akshare,
        get_income_statement_akshare,
    )
    fallbacks = {
        "balance_sheet": get_balance_sheet_akshare,
        "cashflow": get_cashflow_akshare,
        "income_statement": get_income_statement_akshare,
    }
    fn = fallbacks.get(fn_name)
    if fn:
        return fn(symbol)
    raise RuntimeError(f"无可用数据源: {fn_name}")


def get_balance_sheet_tdx(symbol: str) -> pd.DataFrame:
    return _fallback_to_akshare(symbol, "balance_sheet")

def get_cashflow_tdx(symbol: str) -> pd.DataFrame:
    return _fallback_to_akshare(symbol, "cashflow")

def get_income_statement_tdx(symbol: str) -> pd.DataFrame:
    return _fallback_to_akshare(symbol, "income_statement")


# ---- 技术指标 ----

def get_indicators_tdx(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """技术指标 — 基于 K线用 stockstats 计算"""
    df = get_stock_data_tdx(symbol, start_date, end_date)
    from .stockstats_utils import add_stockstats_indicators
    return add_stockstats_indicators(df)


# ---- 新闻（委托 AkShare） ----

def get_news_tdx(symbol: str, date_str: str = None) -> list:
    from .akshare_cn import get_news_akshare
    return get_news_akshare(symbol, date_str)

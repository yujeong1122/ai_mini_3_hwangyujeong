import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

import yfinance as yf
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

from state.ev_market_state import EVMarketState

# 환경 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

OUTPUT_DIR = "results/stock_results"
START_DATE = "2024-11-01"
END_DATE = "2025-05-19"
LLM_MODEL = "gpt-4o"

os.makedirs(OUTPUT_DIR, exist_ok=True)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# LangGraph Node 실행 함수
def run(state: EVMarketState) -> EVMarketState:
    tickers = state.tickers or []
    results = []

    for ticker in tickers:
        logging.info(f"[StockAnalyzer] 주식 분석 시작 - {ticker}")
        result = analyze_stock(ticker)
        if result.get("status") == "success":
            results.append(result)

    final_summary, summary_path = summarize_all_analysis(results)
    state.stock_data = results
    state.stock_summary_path = summary_path
    state.stock_summary_content = final_summary  # 요약 내용 상태에 저장

    return state


def analyze_stock(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        price_data = stock.history(start=START_DATE, end=END_DATE)

        if price_data.empty:
            raise ValueError("주가 데이터 없음.")

        financials = stock.financials
        balance_sheet = stock.balance_sheet
        earnings = stock.earnings

        stock_metrics = _analyze_price_data(price_data)
        financial_metrics = _analyze_financials(
            financials, balance_sheet, earnings, stock
        )

        result = {
            "agent_name": "Stock_Analyzer",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "company": ticker,
            "stock_analysis": {
                "price_metrics": stock_metrics,
                "financial_metrics": financial_metrics,
            },
        }

        _save_to_file(result, ticker)
        return result

    except Exception as e:
        logging.error(f"[StockAnalyzer] 분석 실패 - {ticker} - {e}")
        return _failure_response(ticker, str(e))


def _analyze_price_data(price_data: pd.DataFrame) -> dict:
    close_prices = price_data["Close"]
    start_price = close_prices.iloc[0]
    end_price = close_prices.iloc[-1]
    returns = (end_price - start_price) / start_price * 100
    volatility = close_prices.pct_change().std() * (252**0.5) * 100
    high_price = close_prices.max()
    low_price = close_prices.min()
    current_price = end_price
    price_position = (current_price - low_price) / (high_price - low_price + 1e-9) * 100

    return {
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
        "return_percentage": round(returns, 2),
        "volatility_percentage": round(volatility, 2),
        "price_position_percentage": round(price_position, 2),
    }


def _analyze_financials(financials, balance_sheet, earnings, stock) -> dict:
    try:
        total_revenue = (
            financials.loc["Total Revenue"].iloc[0]
            if "Total Revenue" in financials.index
            else None
        )
        operating_income = (
            financials.loc["Operating Income"].iloc[0]
            if "Operating Income" in financials.index
            else None
        )
        net_income = (
            financials.loc["Net Income"].iloc[0]
            if "Net Income" in financials.index
            else None
        )

        info = stock.info
        eps = info.get("trailingEps")
        current_price = info.get("currentPrice")
        book_value = info.get("bookValue")

        per = round(current_price / eps, 2) if eps and eps != 0 else None
        pbr = (
            round(current_price / book_value, 2)
            if book_value and book_value != 0
            else None
        )

        return {
            "total_revenue_ttm": (
                f"{total_revenue / 1e9:.2f}B USD" if total_revenue else "N/A"
            ),
            "operating_income_ttm": (
                f"{operating_income / 1e9:.2f}B USD" if operating_income else "N/A"
            ),
            "net_income_ttm": f"{net_income / 1e9:.2f}B USD" if net_income else "N/A",
            "eps": round(eps, 2) if eps else "N/A",
            "per": per or "N/A",
            "pbr": pbr or "N/A",
        }
    except Exception as e:
        logging.error(f"[StockAnalyzer] 재무 분석 실패 - {e}")
        return {
            "total_revenue_ttm": "N/A",
            "operating_income_ttm": "N/A",
            "net_income_ttm": "N/A",
            "eps": "N/A",
            "per": "N/A",
            "pbr": "N/A",
        }


def _save_to_file(data: dict, ticker: str):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{ticker}_stock_analysis_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"[StockAnalyzer] 결과 저장 - {filepath}")
    except IOError as e:
        logging.error(f"[StockAnalyzer] 저장 실패 - {e}")


def _failure_response(ticker: str, error_info: str) -> dict:
    return {
        "agent_name": "Stock_Analyzer",
        "status": "fail",
        "timestamp": datetime.utcnow().isoformat(),
        "company": ticker,
        "error_info": error_info,
    }


def summarize_all_analysis(
    results: List[dict], output_filename: str = "stock_summary"
) -> Tuple[str, str]: 
    combined_text = ""

    for result in results:
        company = result.get("company", "Unknown")
        price_metrics = result["stock_analysis"].get("price_metrics", {})
        financial_metrics = result["stock_analysis"].get("financial_metrics", {})

        combined_text += f"기업명: {company}\n"
        combined_text += f"주가 지표: {price_metrics}\n"
        combined_text += f"재무 지표: {financial_metrics}\n\n"

    try:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 글로벌 전기차 산업 주식 분석 전문가입니다. 아래 내용을 바탕으로 기업들의 주가 및 재무 상태를 요약하고 투자 시사점을 작성하세요. 꼭 한국어로 작성하세요.",
                },
                {"role": "user", "content": combined_text},
            ],
            max_tokens=3000,
            temperature=0.2,
        )

        final_summary = response.choices[0].message.content.strip()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_filename}_{timestamp}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": final_summary,
                },
                f,
                ensure_ascii=False,
                indent=4,
            )

        logging.info(f"[StockAnalyzer] 통합 요약 저장 - {filepath}")
        return final_summary, filepath

    except Exception as e:
        logging.error(f"[StockAnalyzer] 요약 실패 - {e}")
        return "", ""

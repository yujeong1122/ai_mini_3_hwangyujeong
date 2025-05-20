import os
import json
import logging

from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI

# 환경 설정 및 초기화
load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4o"
OUTPUT_DIR = "results/market_results"
MAX_CONTENT_LENGTH = 5000
MAX_SUMMARY_TOKENS = 300
REQUEST_TIMEOUT = 5
START_DATE = "2024-11-19"
END_DATE = "2025-05-19"

os.makedirs(OUTPUT_DIR, exist_ok=True)
tavily_client = TavilyClient(TAVILY_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# LangGraph Node 함수
from state.ev_market_state import EVMarketState  # 상태 모델 import


def run(state: EVMarketState) -> EVMarketState:
    companies = state.companies or []
    num_results = state.num_results or 5
    market_results = []

    if state.market_summary_content:
        # 미리 주어진 요약 내용이 있는 경우 직접 결과 구성
        logging.info("[MarketResearcher] 미리 제공된 market_summary_content 사용")
        market_results.append(
            {
                "agent_name": "Market_Researcher",
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "company": ", ".join(companies),
                "market_trends": [
                    {
                        "headline": "요약 제공",
                        "url": "",
                        "published_at": "",
                        "summary": state.market_summary_content,
                    }
                ],
            }
        )
    else:
        for company in companies:
            logging.info(f"[MarketResearcher] 트렌드 조사 시작 - {company}")
            result = search_trends(company, num_results)
            if result.get("status") == "success":
                market_results.append(result)

    state.market_data = market_results
    return state


# 검색 및 요약 관련 함수들
def search_trends(company: str, num_results: int = 5) -> Dict[str, Any]:
    collected_articles = []
    query_base = f"{company} electric vehicle market trends"
    attempts = 0
    max_attempts = 3
    results_per_attempt = 10

    while len(collected_articles) < num_results and attempts < max_attempts:
        query = f"{query_base} from {START_DATE} to {END_DATE}"
        try:
            response = tavily_client.search(
                query=query, max_results=results_per_attempt
            )
            new_articles = _filter_and_collect_articles(
                response, num_results - len(collected_articles)
            )
            collected_articles.extend(new_articles)
        except Exception as e:
            logging.error(f"[MarketResearcher] Tavily 검색 실패 - {company} - {e}")
        attempts += 1

    if len(collected_articles) < num_results:
        logging.warning(
            f"[MarketResearcher] {company} 기사 부족 - {len(collected_articles)}개 확보됨"
        )

    result = _format_results(collected_articles, company)
    _save_to_file(result, company)
    return result


def _filter_and_collect_articles(
    raw_data: Dict[str, Any], needed: int
) -> List[Dict[str, str]]:
    results = raw_data.get("results", [])
    collected = []

    for item in results:
        url = item.get("url", "")
        content = _fetch_article_content(url)
        if content:
            collected.append(
                {
                    "headline": item.get("title", "No Title"),
                    "url": url,
                    "published_at": item.get("published_at") or "Unknown",
                    "content": content,
                }
            )
        if len(collected) >= needed:
            break

    return collected


def _fetch_article_content(url: str) -> Optional[str]:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.ok:
            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            return " ".join(p.get_text() for p in paragraphs)[:MAX_CONTENT_LENGTH]
    except requests.RequestException:
        pass
    return None


def _format_results(articles: List[Dict[str, str]], company: str) -> Dict[str, Any]:
    formatted_results = []
    for article in articles:
        summary = _summarize_content(article["content"])
        formatted_results.append(
            {
                "headline": article["headline"],
                "url": article["url"],
                "published_at": article["published_at"],
                "summary": summary,
            }
        )

    return {
        "agent_name": "Market_Researcher",
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "company": company,
        "market_trends": formatted_results,
    }


def _summarize_content(content: str) -> str:
    try:

        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes news articles in Korean.",
                },
                {
                    "role": "user",
                    "content": f"Summarize this article in Korean:\n{content}",
                },
            ],
            max_tokens=MAX_SUMMARY_TOKENS,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "요약 실패"


def _save_to_file(data: Dict[str, Any], company: str):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{company}_trends_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"[MarketResearcher] 저장 완료 - {filepath}")
    except IOError as e:
        logging.error(f"[MarketResearcher] 저장 실패 - {e}")

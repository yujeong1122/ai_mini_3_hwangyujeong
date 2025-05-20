import os
import json
import logging
from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI

from state.ev_market_state import EVMarketState  # Pydantic 상태 사용

# 환경 설정
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4o"
OUTPUT_DIR = "results/company_results"
MAX_CONTENT_LENGTH = 5000
MAX_SUMMARY_TOKENS = 500
REQUEST_TIMEOUT = 5
START_DATE = "2024-11-19"
END_DATE = "2025-05-19"

os.makedirs(OUTPUT_DIR, exist_ok=True)
tavily_client = TavilyClient(TAVILY_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# LangGraph Node 실행 함수
def run(state: EVMarketState) -> EVMarketState:
    companies = state.companies or []
    num_results = state.num_results
    results = []

    for company in companies:
        logging.info(f"[CompanyAnalyzer] 분석 시작 - {company}")
        result = analyze_company(company, num_results)
        if result.get("status") == "success":
            results.append(result)

    # 상태 업데이트
    state.company_data = results
    return state

# 분석 함수
def analyze_company(company_name: str, num_results: int = 5) -> dict:
    collected_articles = []
    query_base = f"{company_name} business strategy investment R&D"
    attempts = 0
    max_attempts = 3
    results_per_attempt = 10

    while len(collected_articles) < num_results and attempts < max_attempts:
        query = f"{query_base} from {START_DATE} to {END_DATE}"
        try:
            response = tavily_client.search(query=query, max_results=results_per_attempt)
            new_articles = _filter_and_collect_articles(response, num_results - len(collected_articles))
            collected_articles.extend(new_articles)
        except Exception as e:
            logging.error(f"[CompanyAnalyzer] 검색 실패 - {company_name} - {e}")
        attempts += 1

    if len(collected_articles) < num_results:
        logging.warning(f"[CompanyAnalyzer] {company_name} 기사 부족 - {len(collected_articles)}개 확보됨")

    result = _format_results(collected_articles, company_name)
    _save_to_file(result, company_name)
    return result

def _filter_and_collect_articles(raw_data: dict, needed: int) -> List[dict]:
    results = raw_data.get("results", [])
    collected = []

    for item in results:
        url = item.get("url", "")
        content = _fetch_article_content(url)
        if content:
            collected.append({
                "headline": item.get("title", "No Title"),
                "url": url,
                "published_at": item.get("published_at") or "Unknown",
                "content": content,
            })
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

def _format_results(articles: List[dict], company_name: str) -> dict:
    combined_text = "\n\n".join(article["content"] for article in articles if article["content"])
    summary = _summarize_content(combined_text)

    return {
        "agent_name": "Company_Analyzer",
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "company": company_name,
        "business_strategy": summary,
    }

def _summarize_content(content: str) -> dict:
    try:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 글로벌 기업의 사업 동향을 분석하는 전문 애널리스트입니다.\n\n"
                        "다음 항목에 맞춰 체계적으로 정리하세요:\n"
                        "1. 사업 전략 (Core Strategy)\n"
                        "2. 신제품 출시 및 R&D 동향\n"
                        "3. 생산 능력 확대 및 투자 계획\n"
                        "4. 경쟁사 대비 차별화 요소\n\n"
                        "- 반드시 정량적 정보(수치, 일정, 투자 규모 등)를 포함하세요.\n"
                        "- 전체 요약은 500~600자 이내로 작성하세요."
                    ),
                },
                {"role": "user", "content": content},
            ],
            max_tokens=MAX_SUMMARY_TOKENS,
            temperature=0.3,
        )
        summary_text = response.choices[0].message.content.strip()
        return _parse_summary(summary_text)
    except Exception as e:
        logging.error(f"요약 실패 - Error: {e}")
        return {
            "core_strategy": "요약 실패",
            "new_products_rnd": "요약 실패",
            "investment_plans": "요약 실패",
            "differentiators": "요약 실패",
        }

def _parse_summary(summary_text: str) -> dict:
    sections = {
        "core_strategy": "",
        "new_products_rnd": "",
        "investment_plans": "",
        "differentiators": "",
    }
    current_key = None

    for line in summary_text.splitlines():
        line = line.strip()
        if line.startswith("1."):
            current_key = "core_strategy"
            sections[current_key] = line[3:].strip()
        elif line.startswith("2."):
            current_key = "new_products_rnd"
            sections[current_key] = line[3:].strip()
        elif line.startswith("3."):
            current_key = "investment_plans"
            sections[current_key] = line[3:].strip()
        elif line.startswith("4."):
            current_key = "differentiators"
            sections[current_key] = line[3:].strip()
        elif current_key:
            sections[current_key] += " " + line

    return sections

def _save_to_file(data: dict, company_name: str):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{company_name}_business_analysis_{timestamp}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"[CompanyAnalyzer] 저장 완료 - {filepath}")
    except IOError as e:
        logging.error(f"[CompanyAnalyzer] 저장 실패 - {e}")

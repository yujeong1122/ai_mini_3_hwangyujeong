from agents.visualization import ChartMetadata
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Annotated, Union, Literal
from datetime import datetime
import operator
from langchain_core.messages import BaseMessage


class EVMarketState(BaseModel):
    # 입력 파라미터
    companies: List[str] = []
    tickers: List[str] = []
    num_results: int = 5
    current_date: str = datetime.utcnow().strftime("%Y-%m-%d")
    analysis_period: str = "2024-11-01 ~ 2025-05-19"
    target_companies: str = ""
    report_format: str = "pdf"  # pdf or other formats

    # 중간 결과 저장 (에이전트 결과들)
    market_data: List[dict] = []
    market_data_path: Optional[str] = None

    company_data: List[dict] = []
    company_data_path: Optional[str] = None

    stock_data: List[dict] = []
    stock_data_path: Optional[str] = None

    market_summary_content: Optional[str] = None

    # 최종 리포트 결과
    final_report_path: Optional[str] = None
    final_report_content: Optional[str] = None

    # 누락된 속성 추가 (Stock Summary)
    stock_summary_path: Optional[str] = None
    stock_summary_content: Optional[str] = None

    chart_requests: Dict[str, dict] = {}
    generated_charts: Dict[str, ChartMetadata] = {}
    errors: Dict[str, str] = {}

    # 슈퍼바이저 패턴을 위한 추가 필드
    current_step: Optional[str] = Field(default="start")  # 현재 처리 단계
    messages: List[BaseMessage] = Field(default_factory=list)  # 에이전트 간 메시지


def get_initial_state() -> dict:
    """초기 상태를 LangGraph용 dict로 반환"""
    state = EVMarketState(
        companies=[
            "Tesla",
            "BYD Auto",
            "Volkswagen Group",
            "XPeng",
            "Ford Motor Company",
            "Li Auto",
            "Contemporary Amperex Technology",
            "Samsung SDI",
        ],
        tickers=["TSLA", "BYDDF", "VWAGY", "XPEV", "F", "LI", "300750.SZ", "006400.KQ"],
        target_companies="Tesla, BYD, Volkswagen, XPeng, Ford, Li Auto, Contemporary Amperex Technology, Samsung SDI",
        current_date=datetime.utcnow().strftime("%Y-%m-%d"),
        chart_requests={"ev_market_growth": {}},
        current_step="start",  # 시작 단계 설정
    )
    return state.dict()  # LangGraph에서는 dict로 사용

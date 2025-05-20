import matplotlib  # 먼저 추가

matplotlib.use("Agg")  # GUI 백엔드 비활성화
import matplotlib.pyplot as plt

import matplotlib.font_manager as fm
import os
from pydantic import BaseModel, Field
from typing import Dict, Any


# 한글 폰트 설정
font_path = "C:/Windows/Fonts/malgun.ttf"
if os.path.exists(font_path):
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc("font", family=font_name)

OUTPUT_DIR = "results/charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Supervisor에서 공유하는 상태 객체 (예시)
class ChartMetadata(BaseModel):
    title: str
    description: str
    source: str
    file_path: str


class EVMarketState(BaseModel):
    chart_requests: Dict[str, Any] = Field(default_factory=dict)
    generated_charts: Dict[str, ChartMetadata] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)


# 그래프 생성 함수
def plot_ev_market_growth() -> str:
    years = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032]
    market_size = [3680, 3960, 4260, 4580, 4930, 5320, 5720, 6160, 6620, 7120]

    plt.figure(figsize=(10, 6))
    plt.plot(
        years,
        market_size,
        marker="o",
        linestyle="-",
        color="b",
        label="EV Market Size (Billion USD)",
    )
    plt.xlabel("Year")
    plt.ylabel("Market Size (Billion USD)")
    plt.title("Electric Vehicle Market Size Forecast (2023-2032)")
    plt.legend()
    plt.grid(True)

    file_path = os.path.join(OUTPUT_DIR, "ev_market_size_forecast.png")
    plt.savefig(file_path)
    plt.close()
    return file_path


# LangGraph Supervisor에서 호출할 함수
def run(state: EVMarketState) -> EVMarketState:
    for chart_type, params in state.chart_requests.items():
        try:
            if chart_type == "ev_market_growth":
                file_path = plot_ev_market_growth()
                meta = ChartMetadata(
                    title="Electric Vehicle Market Size Forecast (2023-2032)",
                    description="글로벌 전기차 시장 규모 성장 추이 (단위: 억 달러, Billion USD)",
                    source="IEA Global EV Outlook 2024; Our World in Data, 2024",
                    file_path=file_path,
                )
                state.generated_charts[chart_type] = meta
        except Exception as e:
            state.errors[chart_type] = str(e)
    return state

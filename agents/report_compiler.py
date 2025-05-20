import os
import json
import logging
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

from state.ev_market_state import EVMarketState
from .visualization import ChartMetadata

# 환경 변수 및 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

FONT_PATH = r"C:/Windows/Fonts/malgun.ttf"
PDF_FONT_NAME = "MalgunGothic"
OUTPUT_DIR = "results/final_reports"
LLM_MODEL = "gpt-4o"

os.makedirs(OUTPUT_DIR, exist_ok=True)
pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, FONT_PATH))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _convert_to_rgb_png(path: str) -> str:
    if path.lower().endswith(".png"):
        return path
    new_path = os.path.splitext(path)[0] + ".converted.png"
    try:
        with PILImage.open(path) as img:
            rgb_img = img.convert("RGB")
            rgb_img.save(new_path)
            return new_path
    except Exception as e:
        logging.warning(f"[ImageConvert] 변환 실패: {path} - {e}")
        return path


def run(state: EVMarketState) -> EVMarketState:
    current_date = state.current_date or datetime.utcnow().strftime("%Y-%m-%d")
    analysis_period = state.analysis_period or "2024-11-01 ~ 2025-05-19"
    target_companies = (
        state.target_companies or "Tesla, BYD, Volkswagen, Ford, Samsung SDI"
    )
    report_format = state.report_format or "pdf"

    market_data = _load_json(state.market_data_path)
    company_data = _load_json(state.company_data_path)
    stock_data = _load_json(state.stock_data_path)

    chart_metadata = {
        k: v.dict() if hasattr(v, "dict") else v
        for k, v in state.generated_charts.items()
    }

    report_content = _generate_report_content(
        market_data,
        company_data,
        stock_data,
        current_date,
        analysis_period,
        target_companies,
        chart_metadata=chart_metadata,
        stock_summary_content=state.stock_summary_content or "",
    )

    if report_format == "pdf":
        report_path = _save_as_pdf(report_content, current_date, chart_metadata)
        state.final_report_path = report_path
        state.final_report_content = report_content

    return state


def _load_json(file_path: str) -> dict:
    if not file_path:
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _generate_report_content(
    market_data: dict,
    company_data: dict,
    stock_data: dict,
    current_date: str,
    analysis_period: str,
    target_companies: str,
    chart_metadata: dict,
    stock_summary_content: str,
) -> str:
    prompt_template = f"""
당신은 글로벌 전기차 산업 분석 보고서를 작성하는 전문가입니다.

아래의 JSON 데이터와 차트 정보를 기반으로 다음과 같은 형식의 보고서를 작성하세요:

## 입력 데이터
- 시장 분석 데이터: {json.dumps(market_data, ensure_ascii=False, indent=2)}
- 기업 분석 데이터: {json.dumps(company_data, ensure_ascii=False, indent=2)}
- 주가/재무 분석 데이터: {json.dumps(stock_data, ensure_ascii=False, indent=2)}
- 요약 데이터: {stock_summary_content}
- 시각화 차트 정보: {json.dumps(chart_metadata, ensure_ascii=False, indent=2)}
- 리포트 제목: 글로벌 전기차 시장 트렌드 및 주요 기업 주식 분석 - {current_date}
- 분석 대상 기업: {target_companies}
- 분석 기간: {analysis_period}

1. **요약(Summary)**: 5문장 이내로 전체 보고서 핵심을 설명하는 단락을 작성하세요. 제목 없이 본문으로 시작합니다. 5문장 이내로 작성히세요.

2. **2. 시장 트렌드 분석**
   - 차트(`ev_market_growth`)를 본문 중간 또는 바로 아래에 포함시키고, **전기차 시장 규모 및 연평균 성장률(CAGR)** 등을 수치로 해석하세요.
   - 기술 혁신, 정책 변화 등의 트렌드 요소를 설명하세요.

3. **3. 기업 사업 전개 분석**
   - 기업별 전략을 설명하며, **구체적인 수치 (예: 매출, PER, ROE)** 포함하세요.
   - 각 기업의 전략은 다음과 같이 정리해 주세요:
     - Tesla:
     - BYD: 
     - ...

4. **4. 투자 시사점**
   - 성장 가능성과 위험 요소를 종합적으로 5문장 설명한다음, 항목별로 정리하세요.
   - 예:
    전기차 시장 성장 가능성은 높으나, 현재 평가가 높은 기업들은 투자 기회가 적을 수 있습니다.
     - Tesla: 고성장 기대 / 고평가 상태(PER 68), ROE 15.4%
     - Volkswagen: 저평가(PER 5.4) / 안정적 현금 흐름

5. **5. 결론**
   - 전체 시장과 기업 요약 평가
   - 투자자에게 시사하는 전략적 판단 요점 2~3개

작성 시 유의사항:
- 본문은 **전문적인 어조의 자연스러운 문단 형식**으로 작성합니다.
- **불릿 포인트(-)**는 기업 비교 및 투자 시사점에서만 사용 가능합니다.
- **수치 기반의 정량 데이터**를 반드시 포함하여 신뢰도를 높이세요.
- 그래프에 대한 해석과 출처 명시는 반드시 포함하세요.
- 각 단락들 모두 최소 800자를 넘기세요.

"""

    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "당신은 전문 리서치 리포트를 작성하는 어시스턴트입니다.",
            },
            {"role": "user", "content": prompt_template},
        ],
        max_tokens=3000,
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


def _save_as_pdf(
    report_text: str, current_date: str, chart_metadata: dict = None
) -> str:
    filename = f"EV_Market_Report_{current_date}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Korean",
            fontName=PDF_FONT_NAME,
            fontSize=12,
            leading=18,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            fontName=PDF_FONT_NAME,
            fontSize=18,
            leading=24,
            spaceAfter=20,
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ChartCaption",
            fontName=PDF_FONT_NAME,
            fontSize=10,
            leading=14,
            italic=True,
        )
    )

    elements = [
        Paragraph(
            f"글로벌 전기차 시장 트렌드 및 주요 기업 주식 분석",
            styles["CustomTitle"],
        ),
        Spacer(1, 20),
    ]

    inserted_chart = False
    for section in report_text.split("\n\n"):
        elements.append(Paragraph(section.replace("\n", "<br/>"), styles["Korean"]))
        elements.append(Spacer(1, 14))

        if not inserted_chart and "시장 트렌드" in section and chart_metadata:
            for chart in chart_metadata.values():
                if os.path.exists(chart["file_path"]):
                    img_path = _convert_to_rgb_png(chart["file_path"])
                    elements.append(Spacer(1, 16))
                    elements.append(Image(img_path, width=440, height=260))
                    elements.append(Spacer(1, 6))
                    elements.append(
                        Paragraph(
                            f"그림 설명: {chart['description']}<br/>출처: {chart['source']}",
                            styles["ChartCaption"],
                        )
                    )
                    elements.append(Spacer(1, 16))
                    inserted_chart = True
                    break

    doc.build(elements)
    logging.info(f"[ReportCompiler] 최종 리포트 저장 완료 - {filepath}")
    return filepath

from graph.ev_market_graph import build_graph
from state.ev_market_state import EVMarketState, get_initial_state
import logging
import os


# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 이전 실행 결과 정리
results_dirs = ["results/market_results", "results/company_results", 
                "results/stock_results", "results/final_reports"]

for directory in results_dirs:
    if os.path.exists(directory):
        logger.info(f"이전 결과 삭제 중: {directory}")
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"파일 삭제 중 오류: {e}")

# 그래프 생성
graph = build_graph()

# get_initial_state() 함수를 통해 초기 상태 설정
# state = EVMarketState(**get_initial_state())  # 이 방법 또는
initial_state_dict = get_initial_state()
logger.info(f"초기 상태: {initial_state_dict}")
state = EVMarketState.parse_obj(initial_state_dict)  # 또는 이 방법으로 초기화

# 명시적으로 current_step 확인
logger.info(f"시작 전 current_step: {state.current_step}")
state.current_step = "start"  # 명시적으로 다시 설정
logger.info(f"명시적 설정 후 current_step: {state.current_step}")

# 그래프 실행
logger.info("그래프 실행 시작")
final_state = graph.invoke(state)
logger.info("그래프 실행 완료")

# 결과 확인
pdf_path = "results/final_reports/EV_Market_Report_2025-05-20.pdf"
if os.path.exists(pdf_path):
    logger.info(f"보고서가 성공적으로 생성되었습니다: {pdf_path}")
else:
    logger.warning("PDF 파일을 찾을 수 없습니다.")
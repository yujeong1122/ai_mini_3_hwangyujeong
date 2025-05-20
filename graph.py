import os
import sys

# 현재 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.abspath(os.getcwd()))

# ev_market_graph 모듈에서 build_graph 함수 임포트
from graph.ev_market_graph import build_graph


def visualize_ev_market_graph():
    """EV 시장 분석 그래프를 시각화합니다."""
    # 그래프 빌드
    workflow = build_graph()

    # 그래프 시각화
    output_file = "graph.png"
    workflow.get_graph(xray=True).draw_mermaid_png(output_file_path=output_file)
    print(f"그래프 시각화를 {output_file} 파일로 저장했습니다.")


if __name__ == "__main__":
    print("그래프 시각화 시작...")
    visualize_ev_market_graph()

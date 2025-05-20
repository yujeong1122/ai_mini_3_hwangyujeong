from langgraph.graph import StateGraph, END
from state.ev_market_state import EVMarketState
import functools
from agents import market_researcher, company_analyzer, stock_analyzer, report_compiler, visualization


def build_graph():
    # 상태 스키마 지정
    graph = StateGraph(state_schema=EVMarketState)

    # 에이전트 함수들
    def supervisor_agent(state):
        # 상태를 분석하고 다음에 실행할 에이전트를 결정
        current_step = getattr(state, "current_step", "start")

        if current_step == "start":
            return {"current_step": "market_research"}
        elif current_step == "market_research":
            return {"current_step": "company_analysis"}
        elif current_step == "company_analysis":
            return {"current_step": "stock_analysis"}
        elif current_step == "stock_analysis":
            return {"current_step": "visualization"}
        elif current_step == "visualization":
            return {"current_step": "report_compile"}
        else:
            return {"current_step": "end"}

    # 노드 추가
    graph.add_node("Supervisor", supervisor_agent)
    graph.add_node("MarketResearcher", market_researcher.run)
    graph.add_node("CompanyAnalyzer", company_analyzer.run)
    graph.add_node("StockAnalyzer", stock_analyzer.run)
    graph.add_node("Visualization", visualization.run)
    graph.add_node("ReportCompiler", report_compiler.run)

    # 슈퍼바이저가 에이전트들을 결정하는 조건부 엣지 추가
    graph.add_conditional_edges(
        "Supervisor",
        # 여기서 딕셔너리 접근 방식을 속성 접근 방식으로 변경
        lambda state: state.current_step,
        {
            "market_research": "MarketResearcher",
            "company_analysis": "CompanyAnalyzer",
            "stock_analysis": "StockAnalyzer",
            "visualization": "Visualization",
            "report_compile": "ReportCompiler",
            "end": END,
        },
    )

    # 각 에이전트는 작업 완료 후 다시 슈퍼바이저에게 돌아감
    graph.add_edge("MarketResearcher", "Supervisor")
    graph.add_edge("CompanyAnalyzer", "Supervisor")
    graph.add_edge("StockAnalyzer", "Supervisor")
    graph.add_edge("Visualization", "Supervisor")
    graph.add_edge("ReportCompiler", "Supervisor")

    # 시작점 설정
    graph.set_entry_point("Supervisor")

    return graph.compile()
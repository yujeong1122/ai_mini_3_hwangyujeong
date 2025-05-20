s
# 전기차 산업 투자 분석 에이전트 시스템

본 프로젝트는 전기차 산업의 글로벌 시장 동향과 주요 기업에 대한 투자 분석 리포트를 자동으로 생성하는 AI 기반 Multi-Agent 시스템을 설계하고 구현한 실습 프로젝트입니다.

## Overview

- Objective : 전기차 시장 트렌드 및 주요 기업 분석을 통한 투자 보고서 생성 자동화
- Methods : LangGraph 기반 Multi-Agent 워크플로우, LLM 기반 보고서 생성
- Tools : LangChain, yfinance, OpenAI API, ReportLab

## Features

- 전기차 시장 성장률 및 트렌드 자동 수집 및 분석
- 주요 기업의 전략, 재무지표, 주가 변동 분석
- 전문적인 투자 분석 보고서 PDF 자동 생성

## Tech Stack 

| Category   | Details                      |
|------------|------------------------------|
| Framework  | LangGraph, LangChain, Python |
| LLM        | GPT-4o |
| Retrieval  | yfinance, Tavily |

## Agents
 
- Market_Researcher : 전기차 산업의 트렌드 및 시장 현황 조사
- Company_Analyzer : 기업별 사업 전략 및 차별화 요소 분석
- Stock_Analyzer : PER, ROE 등 주요 재무 지표 수집 및 정리
- Visualization_Agent : 시장 성장 그래프 생성
- Report_Compiler : LLM을 활용해 전체 보고서 자동 작성

## State 
- market_data : Tavily 기반 산업 기사 요약 결과
- company_data : 기업별 전략 요약 데이터
- stock_data : yfinance 기반 Valuation 지표
- generated_charts : 차트 이미지와 메타데이터 정보
- final_report_path : PDF로 저장된 보고서 경로

## Architecture
![image](https://github.com/user-attachments/assets/488115e3-6c07-4302-a628-a69fce7c95ed)


## Directory Structure
```
project/
├── agents/                # 각 역할별 에이전트 코드
│   ├── company_analyzer.py    # 기업 분석 에이전트
│   ├── market_researcher.py   # 시장 조사 에이전트
│   ├── report_compiler.py     # 최종 보고서 생성 에이전트
│   ├── stock_analyzer.py      # 주가 분석 에이전트
│   └── visualization.py       # 데이터 시각화 에이전트
│
├── graph/                 # LangGraph 워크플로우 정의
│   └── ev_market_graph.py     # 그래프 구조 및 노드 정의
│
├── state/                 # 상태 관리 모델
│   └── ev_market_state.py     # 상태 스키마 및 초기 상태 정의
│
├── results/               # 리포트, 차트, json 결과 저장 디렉토리
│   ├── charts/                # 시각화 결과물
│   ├── company_results/       # 기업 분석 결과
│   ├── final_reports/         # 최종 PDF 보고서
│   ├── market_results/        # 시장 조사 데이터
│   └── stock_results/         # 주가 분석 결과
│
├── .env                   # API 키 환경 변수
├── .gitignore             
├── graph.png              # 워크플로우 시각화 이미지
├── graph.py               # 워크플로우 시각화
├── main.py                # LangGraph 실행 스크립트
└── requirements.txt       # 프로젝트 의존성 파일
```

## Contributors 

- 황유정 : 전체 에이전트 구조 설계, 시각화 기능 구현, PDF 보고서 디자인, 프롬프트 엔지니어링

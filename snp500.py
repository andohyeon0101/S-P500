import streamlit as st
st.title('S&P500(by andohyeon)')
st.write('안녕하시겠어요?!!!')

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import requests
import json

# 페이지 설정
st.set_page_config(
    page_title="S&P 500 재무제표 분석기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 설정
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e7d32 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin-bottom: 0;
    }
    .main-header p {
        color: white;
        text-align: center;
        margin-top: 0.5rem;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
    }
    .positive {
        color: #2e7d32;
        font-weight: bold;
    }
    .negative {
        color: #d32f2f;
        font-weight: bold;
    }
    .neutral {
        color: #757575;
        font-weight: bold;
    }
    .info-box {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# S&P 500 기업 목록 (주요 기업들만 샘플로)
SP500_COMPANIES = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla Inc.',
    'META': 'Meta Platforms Inc.',
    'NVDA': 'NVIDIA Corporation',
    'JPM': 'JPMorgan Chase & Co.',
    'JNJ': 'Johnson & Johnson',
    'V': 'Visa Inc.',
    'PG': 'Procter & Gamble Company',
    'UNH': 'UnitedHealth Group Inc.',
    'HD': 'Home Depot Inc.',
    'MA': 'Mastercard Inc.',
    'BAC': 'Bank of America Corp.',
    'XOM': 'Exxon Mobil Corporation',
    'DIS': 'Walt Disney Company',
    'ADBE': 'Adobe Inc.',
    'NFLX': 'Netflix Inc.',
    'KO': 'Coca-Cola Company',
    'PFE': 'Pfizer Inc.',
    'INTC': 'Intel Corporation',
    'CRM': 'Salesforce Inc.',
    'CSCO': 'Cisco Systems Inc.',
    'WMT': 'Walmart Inc.',
    'ABT': 'Abbott Laboratories',
    'TMO': 'Thermo Fisher Scientific Inc.',
    'COST': 'Costco Wholesale Corporation',
    'AVGO': 'Broadcom Inc.',
    'ACN': 'Accenture plc',
    'PEP': 'PepsiCo Inc.',
    'AMD': 'Advanced Micro Devices Inc.',
    'GS' : 'The Goldman Sachs Group, Inc.',
    'VZ' : 'Verizon Communications, Inc.',
    'QCOM': 'Qualcomm, Inc.',
    'BLK' : 'BlackRock, Inc.',
    'C'  : 'Citigroup Inc.',
    'HOOD' : 'Robinhood Markets, Inc.',
    'QBTS' :'D-Wave Quantum Inc.',
    'ASML' : 'ASML Holding N.V.',
    'RGTI' : 'Rigetti Computing, Inc.'
}

@st.cache_data
def get_company_data(symbol):
    """회사 데이터를 가져오는 함수"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 재무제표 데이터
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cash_flow = ticker.cashflow
        
        # 주가 데이터
        hist = ticker.history(period="1y")
        
        return {
            'info': info,
            'financials': financials,
            'balance_sheet': balance_sheet,
            'cash_flow': cash_flow,
            'price_history': hist
        }
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return None

def format_currency(value):
    """통화 형식으로 변환"""
    if pd.isna(value):
        return "N/A"
    
    if abs(value) >= 1e12:
        return f"${value/1e12:.2f}T"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.2f}M"
    else:
        return f"${value:,.0f}"

def calculate_financial_ratios(data):
    """재무 비율 계산"""
    try:
        info = data['info']
        financials = data['financials']
        balance_sheet = data['balance_sheet']
        
        ratios = {}
        
        # 기본 정보
        ratios['market_cap'] = info.get('marketCap', 0)
        ratios['pe_ratio'] = info.get('forwardPE', info.get('trailingPE', 0))
        ratios['pb_ratio'] = info.get('priceToBook', 0)
        ratios['dividend_yield'] = info.get('dividendYield', 0)
        ratios['roe'] = info.get('returnOnEquity', 0)
        ratios['roa'] = info.get('returnOnAssets', 0)
        
        # 최신 재무제표 데이터
        if not financials.empty:
            latest_financials = financials.iloc[:, 0]
            ratios['revenue'] = latest_financials.get('Total Revenue', 0)
            ratios['net_income'] = latest_financials.get('Net Income', 0)
            ratios['gross_profit'] = latest_financials.get('Gross Profit', 0)
            
            # 마진 계산
            if ratios['revenue'] > 0:
                ratios['gross_margin'] = (ratios['gross_profit'] / ratios['revenue']) * 100
                ratios['net_margin'] = (ratios['net_income'] / ratios['revenue']) * 100
            else:
                ratios['gross_margin'] = 0
                ratios['net_margin'] = 0
        
        if not balance_sheet.empty:
            latest_balance = balance_sheet.iloc[:, 0]
            ratios['total_assets'] = latest_balance.get('Total Assets', 0)
            ratios['total_debt'] = latest_balance.get('Total Debt', 0)
            ratios['total_equity'] = latest_balance.get('Total Stockholder Equity', 0)
            
            # 부채비율 계산
            if ratios['total_equity'] > 0:
                ratios['debt_to_equity'] = ratios['total_debt'] / ratios['total_equity']
            else:
                ratios['debt_to_equity'] = 0
        
        return ratios
    except Exception as e:
        st.error(f"재무 비율 계산 중 오류: {str(e)}")
        return {}

def create_revenue_chart(financials):
    """매출 추이 차트"""
    if financials.empty:
        return None
    
    revenue_data = financials.loc['Total Revenue'].dropna()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=revenue_data.index,
        y=revenue_data.values,
        mode='lines+markers',
        name='매출',
        line=dict(color='#1f4e79', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='연간 매출 추이',
        xaxis_title='연도',
        yaxis_title='매출 ($)',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_profit_chart(financials):
    """순이익 추이 차트"""
    if financials.empty:
        return None
    
    net_income_data = financials.loc['Net Income'].dropna()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=net_income_data.index,
        y=net_income_data.values,
        mode='lines+markers',
        name='순이익',
        line=dict(color='#2e7d32', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='연간 순이익 추이',
        xaxis_title='연도',
        yaxis_title='순이익 ($)',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_balance_sheet_chart(balance_sheet):
    """대차대조표 차트"""
    if balance_sheet.empty:
        return None
    
    latest_balance = balance_sheet.iloc[:, 0]
    
    # 자산 구성
    total_assets = latest_balance.get('Total Assets', 0)
    current_assets = latest_balance.get('Total Current Assets', 0)
    non_current_assets = total_assets - current_assets
    
    # 부채 및 자본
    total_debt = latest_balance.get('Total Debt', 0)
    total_equity = latest_balance.get('Total Stockholder Equity', 0)
    
    # 두 개의 서브플롯 생성
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        subplot_titles=('자산 구성', '자본 구조')
    )
    
    # 자산 구성 파이 차트
    fig.add_trace(go.Pie(
        labels=['유동자산', '비유동자산'],
        values=[current_assets, non_current_assets],
        name="자산"
    ), row=1, col=1)
    
    # 자본 구조 파이 차트
    fig.add_trace(go.Pie(
        labels=['부채', '자본'],
        values=[total_debt, total_equity],
        name="자본구조"
    ), row=1, col=2)
    
    fig.update_layout(height=400, title_text="재무 구조 분석")
    
    return fig

def create_stock_price_chart(price_history):
    """주가 차트"""
    if price_history.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=price_history.index,
        open=price_history['Open'],
        high=price_history['High'],
        low=price_history['Low'],
        close=price_history['Close'],
        name='주가'
    ))
    
    fig.update_layout(
        title='1년간 주가 추이',
        xaxis_title='날짜',
        yaxis_title='주가 ($)',
        template='plotly_white',
        height=400
    )
    
    return fig

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>📊 S&P 500 재무제표 분석기</h1>
    <p>S&P 500 기업의 재무제표를 실시간으로 분석하고 시각화합니다</p>
</div>
""", unsafe_allow_html=True)

# 사이드바
st.sidebar.title("🔍 기업 선택")
st.sidebar.markdown("---")

# 기업 선택
selected_symbol = st.sidebar.selectbox(
    "분석할 기업을 선택하세요:",
    options=list(SP500_COMPANIES.keys()),
    format_func=lambda x: f"{x} - {SP500_COMPANIES[x]}",
    index=0
)

# 분석 유형 선택
analysis_type = st.sidebar.selectbox(
    "분석 유형:",
    ["전체 분석", "재무제표", "재무비율", "주가 분석", "비교 분석"]
)

# 데이터 로드
if selected_symbol:
    with st.spinner('데이터를 불러오는 중...'):
        company_data = get_company_data(selected_symbol)
    
    if company_data:
        company_info = company_data['info']
        company_name = company_info.get('longName', SP500_COMPANIES[selected_symbol])
        
        # 기업 정보 헤더
        st.header(f"📈 {company_name} ({selected_symbol})")
        
        # 기본 정보
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = company_info.get('currentPrice', 0)
            st.metric("현재 주가", f"${current_price:.2f}")
        
        with col2:
            market_cap = company_info.get('marketCap', 0)
            st.metric("시가총액", format_currency(market_cap))
        
        with col3:
            pe_ratio = company_info.get('forwardPE', 0)
            st.metric("P/E 비율", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
        
        with col4:
            dividend_yield = company_info.get('dividendYield', 0)
            dividend_pct = dividend_yield * 100 if dividend_yield else 0
            st.metric("배당수익률", f"{dividend_pct:.2f}%" if dividend_pct else "N/A")
        
        st.markdown("---")
        
        # 분석 유형별 표시
        if analysis_type == "전체 분석" or analysis_type == "재무제표":
            st.subheader("📋 재무제표 분석")
            
            # 손익계산서
            if not company_data['financials'].empty:
                st.write("**손익계산서 (최근 4년)**")
                financials_display = company_data['financials'].copy()
                
                # 주요 항목만 표시
                key_items = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
                available_items = [item for item in key_items if item in financials_display.index]
                
                if available_items:
                    financials_subset = financials_display.loc[available_items]
                    financials_formatted = financials_subset.applymap(format_currency)
                    st.dataframe(financials_formatted)
                
                # 매출 및 순이익 차트
                col1, col2 = st.columns(2)
                
                with col1:
                    revenue_chart = create_revenue_chart(company_data['financials'])
                    if revenue_chart:
                        st.plotly_chart(revenue_chart, use_container_width=True)
                
                with col2:
                    profit_chart = create_profit_chart(company_data['financials'])
                    if profit_chart:
                        st.plotly_chart(profit_chart, use_container_width=True)
            
            # 대차대조표
            if not company_data['balance_sheet'].empty:
                st.write("**대차대조표 (최근 4년)**")
                balance_sheet_display = company_data['balance_sheet'].copy()
                
                # 주요 항목만 표시
                key_items = ['Total Assets', 'Total Current Assets', 'Total Debt', 'Total Stockholder Equity']
                available_items = [item for item in key_items if item in balance_sheet_display.index]
                
                if available_items:
                    balance_subset = balance_sheet_display.loc[available_items]
                    balance_formatted = balance_subset.applymap(format_currency)
                    st.dataframe(balance_formatted)
                
                # 재무 구조 차트
                balance_chart = create_balance_sheet_chart(company_data['balance_sheet'])
                if balance_chart:
                    st.plotly_chart(balance_chart, use_container_width=True)
        
        if analysis_type == "전체 분석" or analysis_type == "재무비율":
            st.subheader("🔢 재무비율 분석")
            
            ratios = calculate_financial_ratios(company_data)
            
            if ratios:
                # 수익성 비율
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**수익성 비율**")
                    
                    gross_margin = ratios.get('gross_margin', 0)
                    net_margin = ratios.get('net_margin', 0)
                    roe = ratios.get('roe', 0) * 100 if ratios.get('roe') else 0
                    roa = ratios.get('roa', 0) * 100 if ratios.get('roa') else 0
                    
                    st.metric("매출총이익률", f"{gross_margin:.2f}%")
                    st.metric("순이익률", f"{net_margin:.2f}%")
                    st.metric("ROE", f"{roe:.2f}%")
                    st.metric("ROA", f"{roa:.2f}%")
                
                with col2:
                    st.markdown("**안정성 비율**")
                    
                    debt_to_equity = ratios.get('debt_to_equity', 0)
                    pb_ratio = ratios.get('pb_ratio', 0)
                    
                    st.metric("부채비율", f"{debt_to_equity:.2f}")
                    st.metric("PBR", f"{pb_ratio:.2f}" if pb_ratio else "N/A")
                
                # 재무 건전성 평가
                st.markdown("**재무 건전성 평가**")
                
                health_score = 0
                evaluation = []
                
                if net_margin > 10:
                    health_score += 2
                    evaluation.append("✅ 우수한 수익성")
                elif net_margin > 5:
                    health_score += 1
                    evaluation.append("🟡 양호한 수익성")
                else:
                    evaluation.append("❌ 낮은 수익성")
                
                if debt_to_equity < 0.5:
                    health_score += 2
                    evaluation.append("✅ 안정적인 부채 수준")
                elif debt_to_equity < 1.0:
                    health_score += 1
                    evaluation.append("🟡 보통 부채 수준")
                else:
                    evaluation.append("❌ 높은 부채 수준")
                
                if roe > 15:
                    health_score += 2
                    evaluation.append("✅ 높은 자본 효율성")
                elif roe > 10:
                    health_score += 1
                    evaluation.append("🟡 양호한 자본 효율성")
                else:
                    evaluation.append("❌ 낮은 자본 효율성")
                
                for eval_item in evaluation:
                    st.write(eval_item)
                
                overall_rating = "우수" if health_score >= 5 else "양호" if health_score >= 3 else "주의"
                st.info(f"**종합 평가: {overall_rating}** (점수: {health_score}/6)")
        
        if analysis_type == "전체 분석" or analysis_type == "주가 분석":
            st.subheader("📈 주가 분석")
            
            # 주가 차트
            stock_chart = create_stock_price_chart(company_data['price_history'])
            if stock_chart:
                st.plotly_chart(stock_chart, use_container_width=True)
            
            # 주가 통계
            if not company_data['price_history'].empty:
                price_data = company_data['price_history']['Close']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("52주 최고가", f"${price_data.max():.2f}")
                
                with col2:
                    st.metric("52주 최저가", f"${price_data.min():.2f}")
                
                with col3:
                    price_change = price_data.iloc[-1] - price_data.iloc[0]
                    price_change_pct = (price_change / price_data.iloc[0]) * 100
                    st.metric("1년 수익률", f"{price_change_pct:.2f}%")
                
                with col4:
                    volatility = price_data.pct_change().std() * np.sqrt(252) * 100
                    st.metric("변동성", f"{volatility:.2f}%")
        
        if analysis_type == "비교 분석":
            st.subheader("📊 동종업계 비교")
            st.info("동종업계 비교 기능은 추후 업데이트 예정입니다.")
    
    else:
        st.error("데이터를 불러올 수 없습니다. 다른 기업을 선택해주세요.")

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>📊 데이터 출처: Yahoo Finance | 실시간 데이터 기반 분석</p>
    <p>⚠️ 투자 결정은 신중하게 하시기 바랍니다. 이 분석은 참고용입니다.</p>
</div>
""", unsafe_allow_html=True)

# 추가 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 사용 방법")
st.sidebar.markdown("""
1. 분석할 기업을 선택하세요
2. 원하는 분석 유형을 선택하세요
3. 실시간 재무 데이터를 확인하세요
4. 차트와 지표를 통해 분석하세요
""")

st.sidebar.markdown("### 🔍 주요 기능")
st.sidebar.markdown("""
- 실시간 재무제표 데이터
- 재무비율 자동 계산
- 인터랙티브 차트
- 재무 건전성 평가
- 주가 분석
""")

st.sidebar.markdown("### ⚡ 필요한 라이브러리")
st.sidebar.code("""
pip install streamlit
pip install yfinance
pip install plotly
pip install pandas
pip install numpy
""")

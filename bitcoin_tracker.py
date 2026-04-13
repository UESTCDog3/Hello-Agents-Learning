"""
比特币价格展示（Streamlit）— 由 AutoGen 案例中 Engineer 产出，并按 CodeReviewer 意见做小调整：
- 图表为基于当前价的模拟走势，文案中明确标注；
- 自动刷新改用 st.fragment(run_every=...)，避免 time.sleep 长时间阻塞；
- 图表计算使用 data 字段，避免 price_change 未赋值。
"""

from __future__ import annotations

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Any, Dict, Optional

import plotly.express as px

# 设置页面配置
st.set_page_config(
    page_title="Bitcoin Price Tracker",
    page_icon="₿",
    layout="wide",
)

# 自定义CSS美化界面
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF9900;
        text-align: center;
        margin-bottom: 1rem;
    }
    .price-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .price-value {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 10px 0;
    }
    .change-positive {
        color: #00FF00;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .change-negative {
        color: #FF4444;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .data-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .last-updated {
        font-size: 0.9rem;
        color: #666;
        font-style: italic;
    }
    .stSpinner > div {
        border-top-color: #FF9900 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BITCOIN_ID = "bitcoin"
VS_CURRENCY = "usd"


class BitcoinPriceTracker:
    """从 CoinGecko 拉取比特币市场数据。"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Bitcoin-Price-Tracker-App/1.0"})
        self.timeout = 10

    def fetch_bitcoin_data(self) -> Optional[Dict[str, Any]]:
        try:
            endpoint = f"{COINGECKO_API_URL}/coins/{BITCOIN_ID}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            }
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            market_data = data.get("market_data", {})
            return {
                "current_price": market_data.get("current_price", {}).get(VS_CURRENCY),
                "price_change_24h": market_data.get("price_change_24h_in_currency", {}).get(
                    VS_CURRENCY
                ),
                "price_change_percentage_24h": market_data.get(
                    "price_change_percentage_24h_in_currency", {}
                ).get(VS_CURRENCY),
                "high_24h": market_data.get("high_24h", {}).get(VS_CURRENCY),
                "low_24h": market_data.get("low_24h", {}).get(VS_CURRENCY),
                "market_cap": market_data.get("market_cap", {}).get(VS_CURRENCY),
                "total_volume": market_data.get("total_volume", {}).get(VS_CURRENCY),
                "last_updated": data.get("last_updated"),
                "name": data.get("name", "Bitcoin"),
                "symbol": data.get("symbol", "btc").upper(),
            }
        except requests.exceptions.Timeout:
            st.error("请求超时，请检查网络连接或稍后重试")
            return None
        except requests.exceptions.ConnectionError:
            st.error("网络连接失败，请检查您的互联网连接")
            return None
        except requests.exceptions.HTTPError as e:
            st.error(f"API请求失败: {e}")
            return None
        except KeyError as e:
            st.error(f"数据解析失败，API响应格式可能已更改: {e}")
            return None
        except Exception as e:
            st.error(f"获取数据时发生未知错误: {e}")
            return None

    @staticmethod
    def format_price(price: Optional[float]) -> str:
        if price is None:
            return "N/A"
        if price >= 1000:
            return f"${price:,.2f}"
        return f"${price:.2f}"

    @staticmethod
    def format_change(change: Optional[float]) -> str:
        if change is None:
            return "N/A"
        if change >= 0:
            return f"+{change:.2f}"
        return f"{change:.2f}"

    @staticmethod
    def format_percentage(percentage: Optional[float]) -> str:
        if percentage is None:
            return "N/A"
        if percentage >= 0:
            return f"+{percentage:.2f}%"
        return f"{percentage:.2f}%"


@st.fragment(run_every=30)
def _auto_refresh_tick() -> None:
    """每 30 秒在后台拉取一次；未开启自动刷新时立即返回。"""
    if not st.session_state.get("auto_refresh"):
        return
    tracker = BitcoinPriceTracker()
    new_data = tracker.fetch_bitcoin_data()
    if new_data:
        st.session_state.btc_data = new_data
        st.session_state.last_fetch_time = datetime.now()


def main() -> None:
    st.markdown(
        '<h1 class="main-header">₿ Bitcoin Price Tracker</h1>', unsafe_allow_html=True
    )

    tracker = BitcoinPriceTracker()

    if "btc_data" not in st.session_state:
        st.session_state.btc_data = None
    if "last_fetch_time" not in st.session_state:
        st.session_state.last_fetch_time = None
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False

    with st.sidebar:
        st.header("⚙️ 设置")
        auto_refresh = st.checkbox(
            "自动刷新 (每30秒)",
            value=st.session_state.auto_refresh,
        )
        st.session_state.auto_refresh = auto_refresh
        st.markdown("---")
        st.markdown("### 📊 数据来源")
        st.info("数据来自 [CoinGecko API](https://www.coingecko.com/)")
        st.markdown("---")
        st.markdown("### 📱 关于应用")
        st.caption(
            "提供比特币价格与 24 小时涨跌；"
            "折线图为基于当前数据的模拟走势，非交易所逐笔历史。"
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        col_btn, col_status = st.columns([1, 2])
        with col_btn:
            refresh_clicked = st.button(
                "🔄 刷新价格",
                key="refresh_btn",
                use_container_width=True,
                type="primary",
            )
        with col_status:
            if st.session_state.last_fetch_time:
                st.caption(
                    f"最后更新: {st.session_state.last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )

        if refresh_clicked or st.session_state.btc_data is None:
            with st.spinner("正在获取比特币价格数据..."):
                st.session_state.btc_data = tracker.fetch_bitcoin_data()
                st.session_state.last_fetch_time = datetime.now()
                if st.session_state.btc_data is None:
                    st.error("无法获取比特币价格数据，请稍后重试")
                    st.stop()
                st.rerun()

    if st.session_state.btc_data:
        data = st.session_state.btc_data
        price_change = data.get("price_change_24h")
        price_change_pct = data.get("price_change_percentage_24h")

        with col1:
            st.markdown('<div class="price-card">', unsafe_allow_html=True)
            st.markdown(f"### {data['name']} ({data['symbol']})")
            current_price = tracker.format_price(data["current_price"])
            st.markdown(f'<div class="price-value">{current_price}</div>', unsafe_allow_html=True)

            if price_change is not None and price_change_pct is not None:
                change_formatted = tracker.format_change(price_change)
                pct_formatted = tracker.format_percentage(price_change_pct)
                if price_change >= 0:
                    st.markdown(
                        f'<div class="change-positive">▲ {change_formatted} ({pct_formatted})</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="change-negative">▼ {change_formatted} ({pct_formatted})</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            st.subheader("📈 24 小时价格趋势（模拟）")
            st.caption(
                "以下为根据当前价与 24h 涨跌生成的示意曲线，"
                "并非 CoinGecko 返回的逐小时历史 K 线。"
            )
            try:
                hours = list(range(24))
                ch24 = data.get("price_change_24h") or 0.0
                cur = data["current_price"]
                high_24h = data.get("high_24h")
                low_24h = data.get("low_24h")
                base_price = (cur or 0) - ch24
                if high_24h and low_24h:
                    volatility = (high_24h - low_24h) / 2
                else:
                    volatility = (cur or 0) * 0.02

                prices = []
                for i, _ in enumerate(hours):
                    trend = ch24 / 24 * i
                    random_factor = volatility * 0.3 * (i / 24 - 0.5)
                    prices.append(base_price + trend + random_factor)

                df = pd.DataFrame({"小时": hours, "价格 (USD)": prices})
                line_color = "green" if ch24 >= 0 else "red"
                fig = px.line(
                    df,
                    x="小时",
                    y="价格 (USD)",
                    title="过去 24 小时价格变化（模拟）",
                    markers=True,
                )
                fig.update_traces(
                    line=dict(color=line_color, width=3),
                    marker=dict(size=8),
                )
                fig.update_layout(
                    xaxis_title="过去24小时",
                    yaxis_title="价格 (USD)",
                    hovermode="x unified",
                    template="plotly_white",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"无法生成价格图表: {e!s}")

        with col2:
            st.subheader("📊 市场数据")
            with st.container():
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                st.metric(
                    label="24小时最高",
                    value=tracker.format_price(data["high_24h"]),
                    delta=None,
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                st.metric(
                    label="24小时最低",
                    value=tracker.format_price(data["low_24h"]),
                    delta=None,
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                mc = data["market_cap"]
                st.metric(
                    label="市值",
                    value=f"${mc:,.0f}" if mc else "N/A",
                    delta=None,
                )
                st.markdown("</div>", unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="data-card">', unsafe_allow_html=True)
                vol = data["total_volume"]
                st.metric(
                    label="24小时交易量",
                    value=f"${vol:,.0f}" if vol else "N/A",
                    delta=None,
                )
                st.markdown("</div>", unsafe_allow_html=True)
            if data["last_updated"]:
                try:
                    lu = datetime.fromisoformat(
                        data["last_updated"].replace("Z", "+00:00")
                    )
                    local_time = lu.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                    st.caption(f"数据更新时间: {local_time}")
                except Exception:
                    st.caption(f"数据更新时间: {data['last_updated']}")

    _auto_refresh_tick()

    st.markdown("---")
    with st.expander("ℹ️ 使用说明"):
        st.markdown(
            """
        1. **查看价格**：首次进入会自动拉取数据；也可点「刷新价格」。
        2. **涨跌颜色**：绿色上涨，红色下跌。
        3. **自动刷新**：侧边栏勾选后，约每 30 秒后台更新一次（无需整页阻塞等待）。
        4. **趋势图**：为模拟示意，真实历史曲线需接入带时间序列的 API。
        """
        )


if __name__ == "__main__":
    main()
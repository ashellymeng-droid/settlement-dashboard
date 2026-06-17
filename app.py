"""结算看板 — Streamlit Web App 入口"""
import streamlit as st

st.set_page_config(
    page_title="歌单结算看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Password gate
# ============================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Get password from secrets (Cloud) or env (local)
    import os
    APP_PASSWORD = os.getenv("APP_PASSWORD", None)
    # Streamlit Cloud fallback
    try:
        if not APP_PASSWORD:
            APP_PASSWORD = st.secrets.get("APP_PASSWORD", "xiaolaba")
    except:
        APP_PASSWORD = "xiaolaba"

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("### 🔐 结算看板")
        pwd = st.text_input("请输入访问密码", type="password", placeholder="输入密码后回车")
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("密码错误")
    st.stop()

# ============================================================
# Main page
# ============================================================
st.sidebar.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: #1F4E79;'>📊 歌单结算看板</h1>
    <p style='color: #666;'>达人招募 · 投稿结算管理</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📖 使用指南
1. **结算计算** — 上传底表，一键生成结算
2. **达人查询** — 搜索达人ID，查看结算明细
3. **版本对比** — 新旧底表差异分析
4. **反馈管理** — 达人反馈追踪
""")

st.sidebar.markdown("---")
st.sidebar.caption("💡 结算规则在各页面中均有说明")

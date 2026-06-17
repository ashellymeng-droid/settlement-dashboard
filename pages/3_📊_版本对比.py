"""Page 3: 版本对比 — 新旧底表差异分析"""
import streamlit as st
import pandas as pd
import sys, os, tempfile, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settlement_engine import SettlementEngine, SettlementConfig

st.title("📊 版本对比")
st.caption("上传新旧两版底表，自动分析差异")

# Check if base settlement is loaded
if 'result' not in st.session_state or st.session_state.result is None:
    st.warning("⚠️ 请先在「📤 结算计算」页面上传底表并运行结算")
    st.info("💡 或者在此页直接上传新旧两版底表进行对比")

# --- Upload ---
col1, col2 = st.columns(2)
with col1:
    old_file = st.file_uploader("旧版底表", type=['xlsx'], key='cmp_old',
                                help="上一次结算使用的底表")
with col2:
    new_file = st.file_uploader("新版底表", type=['xlsx'], key='cmp_new',
                                help="当前结算使用的底表")
    # Auto-fill from session
    if new_file is None and 'engine' in st.session_state:
        st.caption("✅ 将使用当前已加载的底表作为「新版」")

if st.button("🔍 开始对比", type="primary", disabled=not old_file):
    with st.spinner("正在对比..."):
        engine = SettlementEngine(SettlementConfig())

        # Save temp files
        with tempfile.NamedTemporaryFile(delete=False, suffix='_old.xlsx') as o:
            o.write(old_file.getvalue())
            old_path = o.name

        if new_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='_new.xlsx') as n:
                n.write(new_file.getvalue())
                new_path = n.name
        else:
            # Use current session data
            with tempfile.NamedTemporaryFile(delete=False, suffix='_new.xlsx') as n:
                if st.session_state.result.raw_data is not None:
                    st.session_state.result.raw_data.to_excel(n.name, index=False)
                new_path = n.name

        start = time.time()
        diff = engine.compare_versions(old_path, new_path)
        elapsed = time.time() - start

        # Cleanup
        try: os.unlink(old_path); os.unlink(new_path)
        except: pass

        st.session_state.diff = diff
        st.success(f"✅ 对比完成！耗时 {elapsed:.1f} 秒")

# --- Display results ---
if 'diff' in st.session_state:
    diff = st.session_state.diff

    st.markdown("---")
    st.subheader("📈 变化概览")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("新增稿件", f"{diff['added']} 条")
    with m2:
        st.metric("数据修改", f"{diff['modified']} 条")
    with m3:
        count = len(diff['settlement_changes'])
        total_change = sum(c['变化'] for c in diff['settlement_changes'])
        st.metric("金额变化达人", f"{count} 人", delta=f"¥{total_change:+,.0f}" if total_change != 0 else None)

    # Settlement changes table
    st.subheader("💰 达人结算金额变化")
    if diff['settlement_changes']:
        df_sc = pd.DataFrame(diff['settlement_changes'])
        df_sc.columns = ['创作匠ID', '旧版金额', '新版金额', '变化']

        st.dataframe(
            df_sc,
            use_container_width=True,
            hide_index=True,
            column_config={
                '旧版金额': st.column_config.NumberColumn(format='¥%d'),
                '新版金额': st.column_config.NumberColumn(format='¥%d'),
                '变化': st.column_config.NumberColumn(format='¥%+d'),
            }
        )

        # Bar chart
        df_sc_sorted = df_sc.sort_values('变化', key=abs, ascending=False).head(15)
        chart_data = pd.DataFrame({
            '达人': df_sc_sorted['创作匠ID'],
            '变化金额': df_sc_sorted['变化'],
        }).set_index('达人')
        st.bar_chart(chart_data, use_container_width=True)
    else:
        st.info("达人金额无变化")

    # Detail changes
    if diff['changes']:
        st.subheader(f"🔍 稿件数据变更 ({len(diff['changes'])} 条)")
        df_changes = pd.DataFrame(diff['changes'])
        st.dataframe(df_changes, use_container_width=True, hide_index=True)

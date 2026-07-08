"""Page 1: 数据导入 & 结算计算"""
import streamlit as st
import pandas as pd
import os, time

from settlement_engine import SettlementEngine, SettlementConfig, quick_settle

st.title("📤 数据导入 & 结算计算")
st.caption("上传底表，配置参数，一键生成结算结果")

# --- Session state init ---
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'result' not in st.session_state:
    st.session_state.result = None

# --- Config sidebar ---
with st.sidebar:
    st.subheader("⚙️ 结算规则配置")
    cap = st.number_input("单人金额上限（元）", value=10000, step=500)
    month = st.selectbox("📅 任务月份", ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"], index=5,
                         help="⚠️ 请确认选择正确的月份！导出的文件名和结算月份以此为准")
    st.markdown("---")
    st.caption("播放量字段优先级:")
    st.caption("`7日播放量` → `7日播放量(三方)`")
    st.caption("内容分类：`稿件内容标签`")
    st.caption("结算条件：审核通过 + 可访问")

# --- Main upload area ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 上传底表")
    base_file = st.file_uploader(
        "选择底表文件 (.xlsx)",
        type=['xlsx'],
        key='base_file',
        help="包含全部投稿数据的Excel文件"
    )
    if base_file:
        st.success(f"✅ 已选择: {base_file.name} ({base_file.size/1024:.0f} KB)")

with col2:
    st.subheader("📋 附加文件（可选）")
    old_file = st.file_uploader(
        "旧版底表（用于版本对比）",
        type=['xlsx'],
        key='old_file',
        help="上一次的底表，用于对比差异"
    )
    feedback_file = st.file_uploader(
        "达人反馈表",
        type=['xlsx'],
        key='feedback_file',
        help="问题反馈收集表"
    )

# --- Calculate button ---
st.markdown("---")
calc_col1, calc_col2, calc_col3 = st.columns([1, 2, 1])
with calc_col2:
    if st.button("🚀 开始结算", type="primary", use_container_width=True, disabled=not base_file):
        with st.spinner("正在计算..."):
            start = time.time()

            # Save uploaded file to temp
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(base_file.getvalue())
                tmp_path = tmp.name

            # Run settlement
            engine = SettlementEngine(SettlementConfig(cap_per_person=cap))
            engine.load_data(tmp_path)
            result = engine.calculate()

            elapsed = time.time() - start
            st.session_state.engine = engine
            st.session_state.result = result

            # Clean up
            try: os.unlink(tmp_path)
            except: pass

            st.success(f"✅ 结算完成！耗时 {elapsed:.1f} 秒")

# --- Results ---
if st.session_state.result is not None:
    result = st.session_state.result
    s = result.stats

    st.markdown("---")
    st.subheader("📊 结算概览")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("获奖人数", f"{s['awarded_creators']}人")
    with m2:
        st.metric("结算总金额", f"¥{s['grand_total']:,.0f}")
    with m3:
        st.metric("封顶前金额", f"¥{s['grand_before']:,.0f}")
    with m4:
        st.metric("万元封顶人数", f"{s['capped_count']}人")

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        cpm = s['grand_total'] / s['estimated_exposure'] * 1000 if s['estimated_exposure'] > 0 else 0
        st.metric("预估曝光cpm", f"{cpm:.2f}")
    with m6:
        cpe = s['grand_total'] / s['total_interact'] if s['total_interact'] > 0 else 0
        st.metric("CPE", f"{cpe:.2f}")
    with m7:
        st.metric("过审条数", str(s['guoshen_count']))
    with m8:
        st.metric("过审率", f"{s.get('guoshen_rate', 0):.1%}")

    # --- 公示报告 ---
    st.markdown("---")
    st.subheader("📋 公示前审核报告")

    df_raw = st.session_state.engine.result.raw_data
    guoshen = df_raw[(df_raw['发布平台'] != '网易云音乐') & (df_raw['_can_settle'])]
    total_non_ne = len(df_raw[df_raw['发布平台'] != '网易云音乐'])
    xhs_all = len(df_raw[df_raw['发布平台'] == '小红书'])
    xhs_gs = len(guoshen[guoshen['发布平台'] == '小红书'])
    awarded_p = len([item for d in result.creator_details.values() for bd in d.breakdown for item in bd.get('items', []) if item.get('award', 0) > 0])
    boom_1k = int((guoshen['7日点赞量'] >= 1000).sum())

    xhs_p = guoshen[guoshen['发布平台'] == '小红书']['7日播放量'].sum()
    other_p = guoshen[~guoshen['发布平台'].isin(['小红书'])]['_play'].sum()
    est_e = (xhs_p if pd.notna(xhs_p) else 0) * 4 + (other_p if pd.notna(other_p) else 0)
    total_int = int(guoshen['7日互动量'].sum())
    total_ppl = df_raw[df_raw['发布平台'] != '网易云音乐']['创作匠/易闪ID'].nunique()
    cpm_v = s['grand_total'] / est_e * 1000 if est_e > 0 else 0
    cpe_v = s['grand_total'] / total_int if total_int > 0 else 0
    boom_r = boom_1k / xhs_gs if xhs_gs > 0 else 0
    award_r = awarded_p / len(guoshen) if len(guoshen) > 0 else 0

    def _w(n):
        return f"{n/10000:.0f}w" if n >= 10000 else str(int(n))
    tp = int(xhs_p if pd.notna(xhs_p) else 0) + int(other_p if pd.notna(other_p) else 0)

    report = f"""```
公示前审核
【活动标题】【歌单推广任务】-{month}
【发放人数】共{len(result.creator_totals)}人
【发放金额】{s['grand_total']:,.0f}元
【发放时间】{int(month[0])+1}月
【项目效果】
• 投稿量：{total_non_ne}（小红书投稿数{xhs_all}条，小红书过审{xhs_gs}条）
• 投稿人次：{total_ppl}
• 播放量：{_w(tp)}（小红书{_w(int(xhs_p if pd.notna(xhs_p) else 0))}阅读+其他平台{_w(int(other_p if pd.notna(other_p) else 0))}播放），预估总曝光{est_e:,.0f}，预估曝光cpm {cpm_v:.2f}
• 互动量：{_w(total_int)}，CPE {cpe_v:.2f}
• 过审爆款作品：{boom_1k}条（按千赞标准计算），爆款率 {boom_r:.1%}（爆款率=过审爆款作品数/过审小红书投稿量）
• 获奖作品：{awarded_p}条，获奖率 {award_r:.1%}（获奖率=获奖作品数/过审非分发投稿量）
```"""
    st.markdown(report)

    # Copy button
    report_plain = f"""公示前审核
【活动标题】【歌单推广任务】-{month}
【发放人数】共{len(result.creator_totals)}人
【发放金额】{s['grand_total']:,.0f}元
【发放时间】{int(month[0])+1}月
【项目效果】
• 投稿量：{total_non_ne}（小红书投稿数{xhs_all}条，小红书过审{xhs_gs}条）
• 投稿人次：{total_ppl}
• 播放量：{_w(tp)}（小红书{_w(int(xhs_p if pd.notna(xhs_p) else 0))}阅读+其他平台{_w(int(other_p if pd.notna(other_p) else 0))}播放），预估总曝光{est_e:,.0f}，预估曝光cpm {cpm_v:.2f}
• 互动量：{_w(total_int)}，CPE {cpe_v:.2f}
• 过审爆款作品：{boom_1k}条（按千赞标准计算），爆款率 {boom_r:.1%}（爆款率=过审爆款作品数/过审小红书投稿量）
• 获奖作品：{awarded_p}条，获奖率 {award_r:.1%}（获奖率=获奖作品数/过审非分发投稿量）"""
    st.download_button("📋 复制报告文本", report_plain, file_name=f"歌单{month}结算报告.txt", mime="text/plain")

    # --- Export ---
    st.markdown("---")
    st.subheader("📥 导出结算结果")

    import tempfile
    output_path = os.path.join(tempfile.gettempdir(), f"歌单{month}结算.xlsx")

    # Generate Excel from session state
    engine = st.session_state.engine
    engine.to_excel(output_path)

    with open(output_path, 'rb') as f:
        st.download_button(
            "⬇️ 下载 Excel 结算表",
            f.read(),
            file_name=f"歌单{month}结算.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    # --- Top creators preview ---
    st.subheader("🏆 Top 10 达人")
    sorted_c = sorted(result.creator_totals.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
    df_top = pd.DataFrame([
        {
            '创作匠ID': cid,
            '昵称': d['昵称'],
            '小红书': d.get('小红书', 0),
            '抖音': d.get('抖音', 0),
            '快手': d.get('快手', 0),
            'B站/视频号': d.get('B站/视频号', 0),
            '结算金额': d['total'],
        }
        for cid, d in sorted_c
    ])
    st.dataframe(df_top, use_container_width=True, hide_index=True,
                 column_config={
                     '结算金额': st.column_config.NumberColumn(format='¥%d'),
                     '小红书': st.column_config.NumberColumn(format='¥%d'),
                     '抖音': st.column_config.NumberColumn(format='¥%d'),
                     '快手': st.column_config.NumberColumn(format='¥%d'),
                 })

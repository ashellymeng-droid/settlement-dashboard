"""Page 4: 反馈管理 — 达人问题反馈追踪"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.title("💬 反馈管理")
st.caption("达人问题反馈追踪 & 处理状态管理")

# --- Upload feedback ---
fb_file = st.file_uploader("上传达人反馈表 (.xlsx)", type=['xlsx'], key='fb_upload')

if fb_file:
    df_fb = pd.read_excel(fb_file)
    st.success(f"已加载 {len(df_fb)} 条反馈")

    # Check if settlement data is available
    has_settlement = 'result' in st.session_state and st.session_state.result is not None

    # --- Process & display ---
    feedback_records = []
    for _, row in df_fb.iterrows():
        cid_raw = str(row.get('创作匠id', '')).strip()
        # Clean ID
        for prefix in ['ID：', 'ID:']:
            if prefix in cid_raw:
                cid_raw = cid_raw.replace(prefix, '').strip()

        response_text = str(row.get('实际反馈', ''))
        has_link = '网易云' in response_text and ('补' in response_text or '链接' in response_text or '分发' in response_text)

        # Settlement status
        if has_settlement:
            result = st.session_state.result
            if cid_raw in result.creator_totals:
                status = '✅ 已结算'
                amount = result.creator_totals[cid_raw]['total']
            else:
                # Check if in 未分发 list
                status = '⛔ 未结算'
                amount = 0
        else:
            status = '❓ 未知'
            amount = 0

        feedback_records.append({
            '创作匠ID': cid_raw,
            '填写人': str(row.get('填写人', '')),
            '填写时间': str(row.get('填写时间', '')),
            '问题摘要': str(row.get('问题描述', ''))[:120],
            '处理结果': response_text[:120],
            '已补链接': '✅' if has_link else '❌',
            '结算状态': status,
            '当前金额': amount,
        })

    df_display = pd.DataFrame(feedback_records)

    # --- Filters ---
    st.subheader(f"反馈列表 ({len(df_display)} 条)")

    filter_cols = st.columns(4)
    with filter_cols[0]:
        status_filter = st.selectbox("结算状态", ['全部', '✅ 已结算', '⛔ 未结算', '❓ 未知'])
    with filter_cols[1]:
        link_filter = st.selectbox("补链接", ['全部', '✅', '❌'])
    with filter_cols[2]:
        if has_settlement:
            min_amount = st.number_input("最低金额", value=0, step=100)
        else:
            min_amount = 0
    with filter_cols[3]:
        search = st.text_input("搜索ID/昵称", placeholder="输入关键词")

    # Apply filters
    filtered = df_display
    if status_filter != '全部':
        filtered = filtered[filtered['结算状态'] == status_filter]
    if link_filter != '全部':
        filtered = filtered[filtered['已补链接'] == link_filter]
    if min_amount > 0:
        filtered = filtered[filtered['当前金额'] >= min_amount]
    if search:
        filtered = filtered[
            filtered['创作匠ID'].str.contains(search, case=False, na=False) |
            filtered['填写人'].str.contains(search, case=False, na=False)
        ]

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            '当前金额': st.column_config.NumberColumn(format='¥%d'),
        }
    )

    # --- Stats ---
    st.markdown("---")
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1: st.metric("总反馈", len(df_display))
    with s2: st.metric("已结算", len(df_display[df_display['结算状态'] == '✅ 已结算']))
    with s3: st.metric("未结算", len(df_display[df_display['结算状态'] == '⛔ 未结算']))
    with s4: st.metric("已补链接", len(df_display[df_display['已补链接'] == '✅']))
    with s5: st.metric("涉及总金额", f"¥{filtered['当前金额'].sum():,.0f}")

    # --- Export ---
    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 导出反馈报告 (CSV)",
        csv,
        file_name="反馈追踪报告.csv",
        mime="text/csv",
    )

else:
    st.info("👆 请上传达人问题反馈表，格式参照 5月歌单任务-问题反馈.xlsx")

    # Show template info
    with st.expander("📋 反馈表格式说明"):
        st.markdown("""
        反馈表需包含以下列：
        - `创作匠id` — 达人ID
        - `填写人` — 反馈人
        - `问题描述` — 达人反馈的问题
        - `实际反馈` — 实习生核对后的处理结果
        - `网易云分发链接` — （可选）补充的链接
        """)

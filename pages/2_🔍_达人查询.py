"""Page 2: 达人查询 — 按创作匠ID搜索结算明细"""
import streamlit as st
import pandas as pd

from settlement_engine import SettlementEngine

st.title("🔍 达人结算明细查询")
st.caption("搜索或选择创作匠ID，查看完整结算明细")

# Check if settlement data is loaded
if 'result' not in st.session_state or st.session_state.result is None:
    st.warning("⚠️ 请先在「📤 结算计算」页面上传底表并运行结算")
    st.stop()

result = st.session_state.result
engine = st.session_state.engine

# --- Search / Select ---
all_ids = sorted(result.creator_totals.keys())
all_labels = [f"{cid} ({result.creator_totals[cid]['昵称']})" for cid in all_ids]

st.markdown("### 选择达人")
search_method = st.radio("查询方式", ["下拉选择", "搜索/输入ID"], horizontal=True)

if search_method == "下拉选择":
    selected_label = st.selectbox("达人列表", all_labels, key='select_creator')
    selected_id = all_ids[all_labels.index(selected_label)]
else:
    search_text = st.text_input("输入创作匠ID 或 昵称（部分匹配）", placeholder="例如: YS1085215 或 阿坦")
    if search_text:
        matches = [
            cid for cid in all_ids
            if search_text.upper() in cid.upper()
            or search_text in result.creator_totals[cid].get('昵称', '')
        ]
        if matches:
            selected_id = st.selectbox("匹配的达人", matches)
        else:
            st.info("未找到匹配的达人")
            st.stop()
    else:
        st.stop()

# --- Display ---
detail = engine.get_creator_detail(selected_id)
if detail is None:
    st.error("未找到该达人")
    st.stop()

data = result.creator_totals[selected_id]

st.markdown("---")

# Summary card
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("达人昵称", detail.name)
with c2:
    is_capped_text = f"¥{detail.total:,.0f}" + (" 🔒封顶" if detail.is_capped else "")
    st.metric("结算金额", is_capped_text)
with c3:
    st.metric("封顶前金额", f"¥{detail.before_cap:,.0f}")
with c4:
    plat_text = '、'.join(detail.platforms.keys())
    st.metric("结算平台", plat_text)

# Per-platform detail
st.markdown("---")
st.subheader("📋 分平台结算明细")

for bd in detail.breakdown:
    label = bd.get('label', '')
    plat_name = label.split('-')[0] if '-' in label else label
    total = bd['小计']

    with st.expander(f"{label} — ¥{total:,.0f}", expanded=True):
        for item in bd.get('items', []):
            item_type = item.get('type', '')

            if item_type == '爆款奖':
                st.markdown(
                    f"🔥 **爆款奖** | 作品 `{item['作品ID']}` | "
                    f"点赞 {item['点赞']:,} | {item.get('tier', '')}"
                )

            elif item_type == '累计奖':
                cum_posts = item.get('cum_posts', [])
                likes_str = '+'.join([str(p['点赞']) for p in cum_posts[:8]])
                if len(cum_posts) > 8:
                    likes_str += f"...（共{len(cum_posts)}条）"
                st.markdown(
                    f"📈 **累计奖** | 累计 {item.get('cum_likes', 0):,} 赞 | {item.get('tier', '')}"
                )
                st.caption(f"累计稿件: {likes_str}")

            elif item_type in ('阶梯奖', '分发奖'):
                status = '✅' if item.get('达标', item.get('award', 0) > 0) else '❌ 未达标'
                play_like = item.get('播放量', item.get('点赞', ''))
                metric_name = '播放' if '播放量' in item else '点赞'
                st.markdown(
                    f"{status} **{item_type}** | 作品 `{item['作品ID']}` | "
                    f"{metric_name} {play_like:,} | 奖金 ¥{item.get('award', 0):,}"
                )

# --- All posts table ---
st.markdown("---")
st.subheader("📋 全部过审稿件列表")

cfg = engine.config
all_posts = (
    result.settled_posts[result.settled_posts[cfg.creator_id_field] == selected_id]
)[[cfg.platform_field, cfg.content_tag_field, cfg.like_field, '_play',
   cfg.interact_field, cfg.review_field, cfg.access_field]]

all_posts.columns = ['发布平台', '内容分类', '7日点赞量', '结算播放量', '互动量', '审核结果', '可访问']
st.dataframe(
    all_posts.sort_values(['发布平台', '7日点赞量'], ascending=[True, False]),
    use_container_width=True,
    hide_index=True,
    column_config={
        '7日点赞量': st.column_config.NumberColumn(format='%d'),
        '结算播放量': st.column_config.NumberColumn(format='%d'),
        '互动量': st.column_config.NumberColumn(format='%d'),
    }
)

# --- Quick note ---
st.markdown("---")
note_col1, note_col2 = st.columns(2)
with note_col1:
    st.caption("💡 结算逻辑以「📤 结算计算」页面配置的规则为准")
with note_col2:
    if st.button("📥 导出此达人明细 (CSV)", key='export_csv'):
        csv = all_posts.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ 下载 CSV",
            csv,
            file_name=f"{selected_id}_明细.csv",
            mime="text/csv",
        )

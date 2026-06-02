"""
Streamlit 主应用：A股数据格式检查器 v0.1

页面结构：
1. 文件上传区
2. 数据预览区
3. 字段映射区（支持自动猜测 + 手动覆盖）
4. 数据质量检查区
5. 标准化数据预览区
6. 标准化 CSV 下载区

模块职责分离：app.py 只负责 UI、会话状态与流程编排，
不包含大量数据清洗逻辑。
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional


from config import (
    DEFAULT_PREVIEW_ROWS,
    SUPPORTED_FILE_TYPES,
    DEFAULT_EXPORT_FILENAME,
    DATE_CANDIDATES,
    STOCK_CODE_CANDIDATES,
    CLOSE_CANDIDATES,
    ADJ_CLOSE_CANDIDATES,
    VOLUME_CANDIDATES,
    AMOUNT_CANDIDATES,
)
from data_loader import load_data
from data_checker import check_data_quality
from standardizer import standardize_data


def guess_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    """ 根据候选列表猜测最可能的列名（大小写不敏感）。 """
    if not columns:
        return None
    cols_lower = [c.lower().strip() for c in columns]
    for cand in candidates:
        cand_lower = cand.lower().strip()
        if cand_lower in cols_lower:
            idx = cols_lower.index(cand_lower)
            return columns[idx]
    return columns[0]


def init_session_state():
    """ 初始化会话状态键。 """
    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = None
    if 'mappings' not in st.session_state:
        st.session_state['mappings'] = {}
    if 'std_df' not in st.session_state:
        st.session_state['std_df'] = None
    if 'quality_report' not in st.session_state:
        st.session_state['quality_report'] = None


def render_file_upload():
    """ 文件上传区。 """
    st.header("1. 文件上传")
    st.caption("支持 .csv 和 .xlsx 文件。暂不支持 .xls（需额外依赖）。")

    uploaded_file = st.file_uploader(
        label="上传 A 股数据文件",
        type=SUPPORTED_FILE_TYPES,
        help="请上传包含股票交易数据的 CSV 或 Excel 文件。"
    )

    if uploaded_file is not None:
        try:
            with st.spinner("正在读取文件..."):
                df = load_data(uploaded_file)
            st.session_state['raw_df'] = df
            st.session_state['std_df'] = None  # 重置标准化结果
            st.session_state['quality_report'] = None
            st.session_state['mappings'] = {}  # 重置映射
            st.success(f"文件加载成功！共 {len(df)} 行 × {len(df.columns)} 列。")
            st.info("请继续下方「字段映射」步骤。")
        except Exception as e:
            st.error(f"文件加载失败: {str(e)}")
            st.session_state['raw_df'] = None


def render_data_preview():
    """ 数据预览区。 """
    if st.session_state.get('raw_df') is None:
        return

    st.header("2. 数据预览")
    df = st.session_state['raw_df']
    st.caption(f"显示前 {DEFAULT_PREVIEW_ROWS} 行（共 {len(df)} 行）")

    st.dataframe(
        df.head(DEFAULT_PREVIEW_ROWS),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("查看列名与数据类型"):
        col_info = pd.DataFrame({
            '列名': df.columns,
            '数据类型': df.dtypes.astype(str),
            '非空数量': df.count().values,
            '空值数量': df.isnull().sum().values
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)


def render_field_mapping():
    """ 字段映射区：必选 + 可选，支持自动猜测。 """
    if st.session_state.get('raw_df') is None:
        return

    st.header("3. 字段映射")
    st.caption("请选择数据中对应的标准字段。日期、股票代码、收盘价为必选，其余可选。")

    df = st.session_state['raw_df']
    columns: List[str] = list(df.columns)

    # 自动猜测初始值
    guessed_date = guess_column(columns, DATE_CANDIDATES)
    guessed_stock = guess_column(columns, STOCK_CODE_CANDIDATES)
    guessed_close = guess_column(columns, CLOSE_CANDIDATES)
    guessed_adj = guess_column(columns, ADJ_CLOSE_CANDIDATES)
    guessed_vol = guess_column(columns, VOLUME_CANDIDATES)
    guessed_amt = guess_column(columns, AMOUNT_CANDIDATES)

    with st.form(key="mapping_form"):
        col1, col2 = st.columns(2)

        with col1:
            date_col = st.selectbox(
                "日期列 (必选) *",
                options=columns,
                index=columns.index(guessed_date) if guessed_date in columns else 0,
                help="将解析为 YYYY-MM-DD 格式"
            )
            stock_col = st.selectbox(
                "股票代码列 (必选) *",
                options=columns,
                index=columns.index(guessed_stock) if guessed_stock in columns else 0,
                help="统一转为字符串"
            )
            close_col = st.selectbox(
                "收盘价列 (必选) *",
                options=columns,
                index=columns.index(guessed_close) if guessed_close in columns else 0,
                help="转为数值，错误值置为 NaN"
            )

        with col2:
            adj_options = ['(无)'] + columns
            adj_idx = adj_options.index(guessed_adj) if guessed_adj in adj_options else 0
            adj_col = st.selectbox(
                "复权收盘价列 (可选)",
                options=adj_options,
                index=adj_idx
            )

            vol_options = ['(无)'] + columns
            vol_idx = vol_options.index(guessed_vol) if guessed_vol in vol_options else 0
            vol_col = st.selectbox(
                "成交量列 (可选)",
                options=vol_options,
                index=vol_idx
            )

            amt_options = ['(无)'] + columns
            amt_idx = amt_options.index(guessed_amt) if guessed_amt in amt_options else 0
            amt_col = st.selectbox(
                "成交额列 (可选)",
                options=amt_options,
                index=amt_idx
            )

        factor_cols = st.multiselect(
            "因子列 (可多选)",
            options=columns,
            default=[],
            help="选中的因子列将以 factor_ 前缀保留在输出中（详见 README）"
        )

        remark_col = st.selectbox(
            "备注列 (可选)",
            options=['(无)'] + columns,
            index=0,
            help="备注列不会进入标准化输出，仅供参考"
        )

        submitted = st.form_submit_button("确认并应用字段映射", type="primary")

    if submitted:
        mappings: Dict[str, Any] = {
            'trade_date': date_col,
            'stock_code': stock_col,
            'close': close_col,
            'adj_close': adj_col if adj_col != '(无)' else None,
            'volume': vol_col if vol_col != '(无)' else None,
            'amount': amt_col if amt_col != '(无)' else None,
            'factors': factor_cols,
            'remark': remark_col if remark_col != '(无)' else None,
        }
        st.session_state['mappings'] = mappings
        st.session_state['std_df'] = None  # 映射变化后重置标准化结果
        st.session_state['quality_report'] = None
        st.success("字段映射已应用！请继续「数据质量检查」或「生成标准化数据」。")
        st.rerun()


def render_quality_check():
    """ 数据质量检查区。 """
    if st.session_state.get('raw_df') is None or not st.session_state.get('mappings'):
        return

    st.header("4. 数据质量检查")

    if st.button("执行数据质量检查", type="secondary"):
        with st.spinner("正在检查数据质量..."):
            report = check_data_quality(
                st.session_state['raw_df'],
                st.session_state['mappings']
            )
        st.session_state['quality_report'] = report

    report = st.session_state.get('quality_report')
    if report is None:
        st.info("点击上方按钮执行检查。检查结果不会修改原始数据。")
        return

    st.subheader("检查结果摘要")

    # 关键指标
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总记录数", report['total_rows'])
    c2.metric("股票数量", report.get('num_stocks', 'N/A'))
    c3.metric("日期范围", f"{report.get('date_range', ['N/A', 'N/A'])[0]} ~ {report.get('date_range', ['N/A', 'N/A'])[1]}" if report.get('date_range') else "N/A")
    c4.metric("重复记录数", report.get('duplicate_row_count', 'N/A'))

    # 必选字段专项检查
    st.markdown("**必选字段专项检查**")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"- 日期无效数量: {report.get('invalid_date_count', 'N/A')}")
        st.write(f"- 股票代码空值数: {report.get('stock_null_count', 'N/A')}")
    with col_b:
        st.write(f"- 收盘价空值数: {report.get('close_null_count', 'N/A')}")
        st.write(f"- 收盘价非数值数: {report.get('close_non_numeric_count', 'N/A')}")

    if report.get('has_duplicates'):
        st.warning(f"⚠️ 发现 {report['duplicate_row_count']} 行重复记录（同股票同日期）。标准化时不会自动删除。")
    else:
        st.success("✅ 未发现重复记录。")

    # 缺失值详细表格
    with st.expander("各列缺失值详情（前 20 列）"):
        miss_df = pd.DataFrame({
            '列名': list(report['missing_counts'].keys()),
            '缺失数量': list(report['missing_counts'].values()),
            '缺失率 (%)': list(report['missing_rates'].values())
        }).sort_values('缺失数量', ascending=False).head(20)
        st.dataframe(miss_df, use_container_width=True, hide_index=True)


def render_standardize_and_download():
    """ 标准化预览 + 下载区。 """
    if st.session_state.get('raw_df') is None or not st.session_state.get('mappings'):
        return

    st.header("5. 标准化数据预览与导出")

    if st.button("生成标准化数据", type="primary"):
        with st.spinner("正在生成标准化数据..."):
            std_df = standardize_data(
                st.session_state['raw_df'],
                st.session_state['mappings']
            )
        st.session_state['std_df'] = std_df
        st.success(f"标准化完成！共 {len(std_df)} 行 × {len(std_df.columns)} 列。")

    std_df = st.session_state.get('std_df')
    if std_df is None:
        st.info("点击上方按钮生成标准化数据。标准化过程不会删除行、填充缺失或修改异常值。")
        return

    st.subheader("标准化数据预览（前 10 行）")
    st.dataframe(std_df.head(10), use_container_width=True, hide_index=True)

    st.caption("标准字段说明：trade_date (YYYY-MM-DD), stock_code (str), close/adj_close/volume/amount (numeric)。因子列以 factor_ 前缀保留。")

    # 下载
    csv_bytes = std_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 下载标准化 CSV",
        data=csv_bytes,
        file_name=DEFAULT_EXPORT_FILENAME,
        mime="text/csv",
        help="使用 UTF-8 with BOM 编码，便于 Excel 直接打开中文。"
    )

    st.warning(
        "注意：本工具 v0.1 不删除重复记录、不填充缺失值、不删除异常值。"
        "请在下载后根据业务需求自行处理。"
    )


def main():
    st.set_page_config(
        page_title="A股数据格式检查器 v0.1",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 A股数据格式检查器 v0.1")
    st.caption("本地运行 · 离线优先 · 轻量化数据治理工具 | MODEL: Grok")

    init_session_state()

    # 侧边栏说明
    with st.sidebar:
        st.header("使用说明")
        st.markdown("""
        **v0.1 功能范围**
        - ✅ 文件上传与预览
        - ✅ 字段识别与手动映射
        - ✅ 数据质量检查
        - ✅ 标准化导出 CSV

        **明确不做**
        - ❌ 回测 / 策略收益
        - ❌ 数据库 / API 接入
        - ❌ 联网抓取数据
        - ❌ 自动交易 / 登录
        - ❌ 云同步 / 数据上传
        - ❌ Docker / 前端框架 / 多用户
        """)
        st.markdown("---")
        st.caption("严格遵守工程纪律：简单、清楚、可运行、可审查。")

    # 主流程
    render_file_upload()
    st.divider()

    render_data_preview()
    st.divider()

    render_field_mapping()
    st.divider()

    render_quality_check()
    st.divider()

    render_standardize_and_download()

    # 页脚
    st.markdown("---")
    st.caption(
        "本工具完全本地运行，不上传任何数据、不联网、不接任何金融数据库 API。"
        " | GitHub: Jane-zhou-code/my-first-grok-project (grok/ashare-data-inspector-v0.1)"
    )


if __name__ == "__main__":
    main()
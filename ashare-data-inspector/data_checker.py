"""
数据质量检查模块：负责对映射后的关键字段进行格式与完整性检查。
输出结构化报告，便于 app.py 展示。
不修改原始数据。
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple


def check_data_quality(df: pd.DataFrame, mappings: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行数据质量检查。

    检查项：
    1. 日期列是否可解析为日期（统计无效数量）
    2. 股票代码列空值数量
    3. 收盘价列空值数量
    4. 收盘价列非数值数量
    5. 同一股票同一日期的重复记录数量
    6. 每列缺失值数量与缺失率
    7. 数据日期范围（基于有效日期）
    8. 售一股票数量
    9. 总记录数

    Args:
        df: 原始 DataFrame
        mappings: 字段映射字典，键为 'trade_date', 'stock_code', 'close' 等

    Returns:
        包含检查结果的字典，便于 Streamlit 渲染。
    """
    report: Dict[str, Any] = {}
    report['total_rows'] = len(df)

    # 整体缺失值统计
    missing_counts = df.isnull().sum().to_dict()
    missing_rates = (df.isnull().mean() * 100).round(2).to_dict()
    report['missing_counts'] = missing_counts
    report['missing_rates'] = missing_rates

    # 日期列检查
    date_col: Optional[str] = mappings.get('trade_date')
    if date_col and date_col in df.columns:
        parsed_dates = pd.to_datetime(df[date_col], errors='coerce')
        invalid_date_count = int(parsed_dates.isna().sum())
        report['invalid_date_count'] = invalid_date_count

        valid_dates = parsed_dates.dropna()
        if len(valid_dates) > 0:
            report['date_range'] = (
                valid_dates.min().strftime('%Y-%m-%d'),
                valid_dates.max().strftime('%Y-%m-%d')
            )
        else:
            report['date_range'] = None
    else:
        report['invalid_date_count'] = None
        report['date_range'] = None

    # 股票代码列检查
    stock_col: Optional[str] = mappings.get('stock_code')
    if stock_col and stock_col in df.columns:
        report['stock_null_count'] = int(df[stock_col].isnull().sum())
        report['num_stocks'] = int(df[stock_col].nunique())
    else:
        report['stock_null_count'] = None
        report['num_stocks'] = None

    # 收盘价列检查
    close_col: Optional[str] = mappings.get('close')
    if close_col and close_col in df.columns:
        report['close_null_count'] = int(df[close_col].isnull().sum())
        close_numeric = pd.to_numeric(df[close_col], errors='coerce')
        # 非空但无法转为数值的情况
        non_null_mask = ~df[close_col].isnull()
        non_numeric_count = int((close_numeric.isna() & non_null_mask).sum())
        report['close_non_numeric_count'] = non_numeric_count
    else:
        report['close_null_count'] = None
        report['close_non_numeric_count'] = None

    # 重复记录检查（同一股票 + 同一日期）
    if stock_col and date_col and stock_col in df.columns and date_col in df.columns:
        temp_df = df[[stock_col, date_col]].copy()
        # 日期标准化为 date 对象以避免时间部分影响
        temp_df['date_norm'] = pd.to_datetime(temp_df[date_col], errors='coerce').dt.date
        # 标记所有重复的行（keep=False 标记所有重复项）
        dup_mask = temp_df.duplicated(subset=[stock_col, 'date_norm'], keep=False)
        duplicate_row_count = int(dup_mask.sum())
        report['duplicate_row_count'] = duplicate_row_count
        report['has_duplicates'] = duplicate_row_count > 0
    else:
        report['duplicate_row_count'] = None
        report['has_duplicates'] = None

    return report
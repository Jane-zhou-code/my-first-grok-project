"""
标准化模块：根据用户选择的字段映射，生成符合标准字段名的 DataFrame。
严格遵守 v0.1 规则：
- 日期 -> YYYY-MM-DD 字符串格式
- 股票代码 -> 字符串（strip 空格）
- 价格/量 -> 数值（coerce 错误为 NaN）
- 可选列未选择则不生成对应标准列
- 因子列加 'factor_' 前缀保留（避免与标准字段冲突）
- 不删除任何行、不填充缺失值、不删除异常值或重复记录
- 完全空行保留（用户可在界面看到并决定后续处理）
"""

import pandas as pd
from typing import Dict, Any, List, Optional


def standardize_data(df: pd.DataFrame, mappings: Dict[str, Any]) -> pd.DataFrame:
    """
    根据字段映射生成标准化 DataFrame。

    Args:
        df: 原始数据
        mappings: 包含 'trade_date', 'stock_code', 'close', 'adj_close', 'volume', 'amount', 'factors' (list) 等键的字典

    Returns:
        标准化后的 DataFrame（行数与原始一致，列为标准字段 + factor_ 前缀列）
    """
    std_df = pd.DataFrame(index=df.index)

    # 1. trade_date: 标准化为 YYYY-MM-DD 字符串
    date_col: Optional[str] = mappings.get('trade_date')
    if date_col and date_col in df.columns:
        parsed = pd.to_datetime(df[date_col], errors='coerce')
        # 有效日期格式化，无效保留空字符串（不使用 NaT 字符串）
        std_df['trade_date'] = parsed.apply(
            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else ''
        )

    # 2. stock_code: 统一为字符串并去除首尾空格
    stock_col: Optional[str] = mappings.get('stock_code')
    if stock_col and stock_col in df.columns:
        std_df['stock_code'] = df[stock_col].astype(str).str.strip()

    # 3. close: 转为数值
    close_col: Optional[str] = mappings.get('close')
    if close_col and close_col in df.columns:
        std_df['close'] = pd.to_numeric(df[close_col], errors='coerce')

    # 4. adj_close (可选)
    adj_col: Optional[str] = mappings.get('adj_close')
    if adj_col and adj_col in df.columns:
        std_df['adj_close'] = pd.to_numeric(df[adj_col], errors='coerce')

    # 5. volume (可选)
    vol_col: Optional[str] = mappings.get('volume')
    if vol_col and vol_col in df.columns:
        std_df['volume'] = pd.to_numeric(df[vol_col], errors='coerce')

    # 6. amount (可选)
    amt_col: Optional[str] = mappings.get('amount')
    if amt_col and amt_col in df.columns:
        std_df['amount'] = pd.to_numeric(df[amt_col], errors='coerce')

    # 7. 因子列（可多选）：保留原值，加 factor_ 前缀
    #    说明见 README：因子列不进行类型强制转换，保留原始数据类型
    factor_cols: List[str] = mappings.get('factors', []) or []
    for fcol in factor_cols:
        if fcol in df.columns:
            std_df[f'factor_{fcol}'] = df[fcol]

    return std_df
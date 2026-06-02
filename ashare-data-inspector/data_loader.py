"""
数据加载模块：负责根据文件类型读取 CSV / Excel 文件为 pandas DataFrame。
仅处理基础读取异常，不做业务清洗。
CSV 优先尝试 utf-8-sig 编码，失败时尝试常见中文编码。
"""

import pandas as pd
from io import BytesIO
from typing import BinaryIO


def load_data(uploaded_file: BinaryIO) -> pd.DataFrame:
    """
    加载上传文件为 DataFrame。

    Args:
        uploaded_file: Streamlit 上传的文件对象

    Returns:
        pandas DataFrame

    Raises:
        ValueError: 当文件类型不支持或解码/解析失败时，抛出清晰错误信息。
    """
    if uploaded_file is None:
        raise ValueError("未提供文件。")

    file_name = uploaded_file.name.lower()

    if file_name.endswith('.csv'):
        bytes_data = uploaded_file.getvalue()
        # 常见编码尝试顺序（优先 utf-8-sig 以正确处理 BOM）
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
        last_error = None
        for enc in encodings:
            try:
                df = pd.read_csv(BytesIO(bytes_data), encoding=enc)
                return df
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                # 其他解析错误（如分隔符问题）
                raise ValueError(f"CSV 文件解析失败: {str(e)}。请检查文件格式是否正确。")
        raise ValueError(
            "无法使用常见编码解码 CSV 文件。"
            "请将文件另存为 UTF-8（带 BOM）或 UTF-8 编码后重试。"
        )

    elif file_name.endswith('.xlsx'):
        try:
            # engine='openpyxl' 为 requirements.txt 中指定依赖
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            return df
        except Exception as e:
            raise ValueError(f"Excel (.xlsx) 文件读取失败: {str(e)}。")

    elif file_name.endswith('.xls'):
        raise ValueError(
            "暂不支持 .xls 格式（需要额外依赖 xlrd 或其他引擎）。"
            "请将文件另存为 .xlsx 或 .csv 格式后重新上传。"
        )

    else:
        raise ValueError(
            f"不支持的文件类型: {file_name}。"
            "请上传 .csv 或 .xlsx 文件。"
        )
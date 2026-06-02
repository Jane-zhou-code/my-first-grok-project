"""
配置模块：定义常量、默认值和标准字段。
"""

# 默认预览行数
DEFAULT_PREVIEW_ROWS = 10

# 支持的文件类型（扩展名小写）
SUPPORTED_FILE_TYPES = ['csv', 'xlsx']

# 标准输出字段（v0.1 核心）
STANDARD_FIELDS = ['trade_date', 'stock_code', 'close', 'adj_close', 'volume', 'amount']

# 默认导出文件名
DEFAULT_EXPORT_FILENAME = "standardized_ashare_data.csv"

# 字段自动猜测候选（支持中英文常见命名）
DATE_CANDIDATES = ['trade_date', 'date', '日期', '交易日期', 'dt', 'time', 'datetime', '日期时间']
STOCK_CODE_CANDIDATES = ['stock_code', 'code', '股票代码', 'sec_code', 'ticker', 'symbol', '证券代码']
CLOSE_CANDIDATES = ['close', '收盘价', 'close_price', '收盘', 'adj_close']
ADJ_CLOSE_CANDIDATES = ['adj_close', '复权收盘价', 'adjclose', '复权价']
VOLUME_CANDIDATES = ['volume', '成交量', 'vol', 'volume']
AMOUNT_CANDIDATES = ['amount', '成交额', 'amt', 'amount']
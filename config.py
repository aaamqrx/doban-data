# -*- coding: utf-8 -*-
from pathlib import Path

# 豆瓣电影类型配置
MOVIE_TYPES = {
    "comedy": {"type_id": 24, "name": "喜剧"},
    "action": {"type_id": 5, "name": "动作"},
    "romance": {"type_id": 13, "name": "爱情"},
}

# 中国地区关键词（包含大陆、香港、台湾）
CHINA_KEYWORDS = ["中国大陆", "大陆", "中国香港", "香港", "中国台湾", "台湾"]

# 目标数量（每个类型）
TARGET_CHINA_COUNT = 2000

# 分页配置
LIMIT_PER_PAGE = 20

# 常规请求延时
DELAY_MIN = 3
DELAY_MAX = 5

# HTML下载相关配置
REQUEST_TIMEOUT = 20
BATCH_SIZE = 50
BATCH_PAUSE_MIN = 120
BATCH_PAUSE_MAX = 300
BLOCK_RETRY_COUNT = 2
BLOCK_RETRY_PAUSES = (30, 90)
BLOCKED_THRESHOLD = 3
BLOCK_PAUSE_MIN = 300
BLOCK_PAUSE_MAX = 900
STOP_BLOCKED_THRESHOLD = 5

# 目录配置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = BASE_DIR / "html_cache"
RAW_DIR = DATA_DIR / "raw"
FILTERED_DIR = DATA_DIR / "filtered"
SRC_DIR = BASE_DIR / "src"

# 确保目录存在
for d in [DATA_DIR, HTML_DIR, RAW_DIR, FILTERED_DIR, SRC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Cookie配置（需定期更新）
COOKIES = {
    "ll": "\"108088\"",
    "bid": "d5-y7eKV_vE",
    "push_noty_num": "0",
    "push_doumail_num": "0",
    "__utmz": "30149280.1775135882.1.1.utmcsr=accounts.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/",
    "__utmv": "30149280.26739",
    "_pk_id.100001.4cf6": "f09015deaff7fc27.1775634915.",
    "__utmz": "223695111.1775634918.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
    "_vwo_uuid_v2": "DFB79D041033068060DCE0A6C88B576D1|2d5a6f8edf69b80896c69adcf753be13",
    "__yadk_uid": "aPg4kCjsi3PexCQJbKPO2up5pacWFxEp",
    "__utma": "30149280.1995096768.1775135882.1775735784.1775787110.6",
    "__utma": "223695111.556340732.1775634918.1775735784.1775787110.5",
    "_pk_ses.100001.4cf6": "1",
    "ap_v": "0,6.0",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://movie.douban.com/chart",
    "Accept": "application/json, text/plain, */*",
}

# -*- coding: utf-8 -*-
from pathlib import Path

# 豆瓣电影类型配置（type_id已全部补全）
MOVIE_TYPES = {
    "documentary": {"type_id": 1, "name": "纪录片"},
    "biography": {"type_id": 2, "name": "传记"},
    "crime": {"type_id": 3, "name": "犯罪"},
    "history": {"type_id": 4, "name": "历史"},
    "action": {"type_id": 5, "name": "动作"},
    "erotic": {"type_id": 6, "name": "情色"},
    "musical": {"type_id": 7, "name": "歌舞"},
    "children": {"type_id": 8, "name": "儿童"},
    "drama": {"type_id": 11, "name": "剧情"},
    "disaster": {"type_id": 12, "name": "灾难"},
    "romance": {"type_id": 13, "name": "爱情"},
    "music": {"type_id": 14, "name": "音乐"},
    "adventure": {"type_id": 15, "name": "冒险"},
    "fantasy": {"type_id": 16, "name": "奇幻"},
    "scifi": {"type_id": 17, "name": "科幻"},
    "sports": {"type_id": 18, "name": "运动"},
    "thriller": {"type_id": 19, "name": "惊悚"},
    "horror": {"type_id": 20, "name": "恐怖"},
    "war": {"type_id": 22, "name": "战争"},
    "short": {"type_id": 23, "name": "短片"},
    "comedy": {"type_id": 24, "name": "喜剧"},
    "western": {"type_id": 27, "name": "西部"},
    "family": {"type_id": 28, "name": "家庭"},
    "wuxia": {"type_id": 29, "name": "武侠"},
    "costume": {"type_id": 30, "name": "古装"},
    "noir": {"type_id": 31, "name": "黑色电影"},
    "suspense": {"type_id": 10, "name": "悬疑"},
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
FINAL_DIR = DATA_DIR / "final"
SRC_DIR = BASE_DIR / "src"

# 确保目录存在
for d in [DATA_DIR, HTML_DIR, RAW_DIR, FILTERED_DIR, FINAL_DIR, SRC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Cookie配置（需定期更新）
COOKIES = {
    "bid": "a1yHC4aayTs",
    "_pk_id.100001.4cf6": "df41304922613660.1775634952.",
    "ll": "118172",
    "__yadk_uid": "7gQtuuk687gJZw8mg0sg9cGWTyzQoAPA",
    "_vwo_uuid_v2": "D0B6E805B637BA894C5D783068C4FA7B9|e80f47eca6ece73fe02aed573033e635",
    "__utmz": "30149280.1776921303.11.10.utmcsr=cn.bing.com|utmccn=(referral)|utmcmd=referral|utmcct=/",
    "__utmc": "223695111",
    "push_noty_num": "0",
    "push_doumail_num": "0",
    "ap_v": "0,6.0",
    "_pk_ref.100001.4cf6": "%5B%22%22%2C%22%22%2C1776951404%2C%22https%3A%2F%2Fsec.douban.com%2F%22%5D",
    "_pk_ses.100001.4cf6": "1",
    "__utma": "223695111.1953892667.1775634957.1776744242.1776951404.11",
    "__utmb": "223695111.0.10.1776951404",
    "dbcl2": "294776582:P1LY2fevSBc",
    "ck": "lfkA",
    "frodotk_db": "ef9dffe09308f914ced9ffa1b91aeb3c",
    "__utmt": "1",
    "__utmv": "30149280.29477",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://movie.douban.com/chart",
    "Accept": "application/json, text/plain, */*",
}

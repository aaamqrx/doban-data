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

# 百度指数配置
BAIDU_INDEX_COOKIE = r"ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf%2B4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq%2FXx%2BRgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGkz2D6Cjm%2Bvcw2e7spDhnGYGEimjy3MrXEpSuItnI4KD18UkbhVZ5Ime9zYtV6t%2BOxGiLfCCzyAMyMh%2F1GUTmdVqOaGDbas0IRVTMjBA63lOMHESZf5NfdodBRbpGtTZfnGgLbz7OSojK1zRbqBESR5Pdk2R9IA3lxxOVzA%2BIw1TYBZPHzfoK%2BUHS%2F6G3TixLN7QDojBND8DBFz4NgW3Pg8GWhocXrPp5Y8evA8e3q50eTix2abnMaxFIIJ85t1EZ%2BmCwUuI3T4UUrPhqYA1RgK0I7ZAk%2Biiy%2FYrTP73G27JkU71kNF2dsvqfwovIEcoISv7msTc8aP3xqe8%2Beb8S1bryv0vRX%2BUbSw3GoYPEAqqj%2FyVGQOwUQRYevLqg0GsddIH14BsQjX90sfHuCl1Aa6lf4N4RBH%2FZbrvKD84kSMGpyCWNV2bqaj2YJn4fAS8E%2FWFLsnNLvESk4rcztt4UsBl%2B7COFNzOXHywcFV%2BZu%2BDb3mFDYuy4vO0vGW18t9XssQQyuCIgxpbdVRbMQyM9EbFR2bnXoEieM2GveXyzluNWF%2BUcHg6krT8DM3UvAE%2B%2BsoFYr%2B5ZxeMa2JIYEijZTEMD5D%2FOhnyGxgqrhgDmyXwkNmuWf0qeYv6YzHaS73rajtZnmoSCoPiQJ8fKzREezTiV3e1j%2BAyVqADa5%2FpNVQSi2u3pTzUllPaUj8GpkCVC31ZXXZco39g0jXRWpLHNOG%2F1VhMXwdvftP3IsboqOF6wv2ED23v3lzmJDlhAwg7rciLFwONBwyxtnGK%2BGMxyI2%2BCi4MIagWfRk2jdxclF98oIfXmZKhbrqojV32wcFNmIPvSWeHncTPON0OcZ3UW0ThlWBfBdYUs68Bfjfet0oTRjv5ii%2BuLg9FdQTz76laHhgWa2XYnL0I%2FyMaYOB1fXv8cSTQyUvg5bG6rt5%2BCOubpDRly8hJJQuMhC7lnfy1nB%2FbyDVtojV8VzprVRC2O%2BE8cSTQyUvg5bG6rt5%2BCOubomTY4K0wDrt8OFFV508V7i9BTP7hct8v25t214g385XJlf9dI0aUTGtVnNNQzVUXb7eN%2FzkKkCYY6R%2BXYT%2BZ82d0sIeyq9R1gs4TMyBREN1%2BCOzqWiD%2FJ%2Fi86HI7d4aVw%3D%3D; XFI=95d203d0-3f23-11f1-a09e-53463e73ca46; XFCS=24459667877873DC76C2F5A62D96231C4BFD3EFD36ABAC2F6CC921FD099803AF; XFT=4a5QLJ1TPqrLKN0Bva9lpLU5ENGz2PKfuWDjvJGEJaw=; BIDUPSID=37109A0E308A6B91EB955F80639ECD7A; PSTM=1757291803; BAIDUID=6A3D08FFEB1980FDF62E9D8F0E456E43:FG=1; BAIDUID_BFESS=6A3D08FFEB1980FDF62E9D8F0E456E43:FG=1; ZFY=PdU3GU57WNlD0lzKSvJM0D4:A2f344JTkklh5lcVQUZ4:C; __bid_n=199c6f994445312b1e8445; H_PS_PSSID=63141_67218_67316_67437_67479_67565_67553_67546_67602_67698_67720_67748_67756_67313_67730_67821_67822_67824_67826; Hm_lvt_d101ea4d2a5c67dab98251f0b5de24dc=1776955743; HMACCOUNT=536BADE043418DA0; ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf+4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq/Xx+RgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGkz2D6Cjm+vcw2e7spDhnGYGEimjy3MrXEpSuItnI4KD18UkbhVZ5Ime9zYtV6t+OxGiLfCCzyAMyMh/1GUTmdVqOaGDbas0IRVTMjBA63lOMHESZf5NfdodBRbpGtTZfnGgLbz7OSojK1zRbqBESR5Pdk2R9IA3lxxOVzA+Iw1TYBZPHzfoK+UHS/6G3TixLN7QDojBND8DBFz4NgW3Pg8GWhocXrPp5Y8evA8e3q50eTix2abnMaxFIIJ85t1EZ+mCwUuI3T4UUrPhqYA1RgK0I7ZAk+iiy/YrTP73G27JkU71kNF2dsvqfwovIEcoISv7msTc8aP3xqe8+eb8S1bryv0vRX+UbSw3GoYPEAqqj/yVGQOwUQRYevLqg0GsddIH14BsQjX90sfHuCl1Aa6lf4N4RBH/ZbrvKD84kSMGpyCWNV2bqaj2YJn4fAS8E/WFLsnNLvESk4rcztt4UsBl+7COFNzOXHywcFV+Zu+Db3mFDYuy4vO0vGW18t9XssQQyuCIgxpbdVRbMQyM9EbFR2bnXoEieM2GveXyzluNWF+UcHg6krT8DM3UvAE++soFYr+5ZxeMa2JIYEijZTEMD5D/OhnyGxgqrhgDmyXwkNmuWf0qeYv6YzHaS73rajtZnmoSCoPiQJ8fKzREezTiV3e1j+AyVqADa5/pNVQSi2u3pTzUllPaUj8GpkCVC31ZXXZco39g0jXRWpLHNOG/1VhMXwdvftP3IsboqOF6wv2ED23v3lzmJDlhAwg7rciLFwONBwyxtnGK+GMxyI2+Ci4MIagWfRk2jdxclF98oIfXmZKhbrqojV32wcFNmIPvSWeHncTPON0OcZ3UW0ThlWBfBdYUs68Bfjfet0oTRjv5ii+uLg9FdQTz76laHhgWa2XYnL0I/yMaYOB1fXv8cSTQyUvg5bG6rt5+COubpDRly8hJJQuMhC7lnfy1nB/byDVtojV8VzprVRC2O+E8cSTQyUvg5bG6rt5+COubomTY4K0wDrt8OFFV508V7i9BTP7hct8v25t214g385XJlf9dI0aUTGtVnNNQzVUXb7eN/zkKkCYY6R+XYT+Z82d0sIeyq9R1gs4TMyBREN1+COzqWiD/J/i86HI7d4aVw==; BDUSS=p-N1hDS2RScWJmTEJaa2lvUnd0TndvSWFPWEduRWYwRFlLTTY1eTctQ0V2aEZxSUFBQUFBJCQAAAAAAQAAAAEAAAA2Vgh9YWRvcmV0aGVhbGw5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIQx6mmEMeppTV; Hm_up_d101ea4d2a5c67dab98251f0b5de24dc=%7B%22uid_%22%3A%7B%22value%22%3A%226392665654%22%2C%22scope%22%3A1%7D%7D; bdindexid=ekvjob9k3pf88kprmajlht5sq1; SIGNIN_UC=70a2711cf1d3d9b1a82d2f87d633bd8a05270223711gyU8TibQvQRhqMGNDEO5mDuYoB6XmaA%2FnM3TTuWZyKF9W3ZRdRkMUV13Av0jkOh5V1864n8UAdD810EBWLw56pzMaKqqJJdLnHhpTn9w4IT4j4j6f7NHYSnUbrVY9VOn%2FrBHvZRmueIBc4aWhEwwkCGNEeyoB9J%2FOHEpxh1dK993lnFke9md6IKLyZXlm9dMzpW8kOQ9s40zKfQs2NDLBR8ACjv8S6JAsfact2Z9kYGRcTirGnc%2Fjn%2FrMrTa8%2FwTxwUpHNzsOi3kV136Z8%2BDdlWlxImsg6HDt0VMy9HzSTU%3D95574540256661984185289500341825; __cas__rn__=527022371; __cas__st__212=edceaa01815d61112e2fc82f9348d937c87b80343cff52974e700a1aa51f2a7924002ca3631079bab3fd7ace; __cas__id__212=81673374; CPTK_212=508186973; CPID_212=81673374; Hm_lpvt_d101ea4d2a5c67dab98251f0b5de24dc=1777009933; ab_sr=1.0.1_NDg2M2UzY2Q3OGViYjU1MTdmNDcxZGI0YTI3MmFmMDg2ODM0NjVhYmVjMzI2ODMyOWQ5ZjQ4YmM1MTk0MjgwYzFhMTViZTUyN2ZkOTRiYjRhZWVkNWJhYjQzNDAyNzdkNTUzMGI2NjRhYjY4YmI5MWNiMDQxOWI0ZWQ4ODRjMGQzMGY3Y2MwN2ZlZWFjZDVkZTI2M2VmZDUyNTZlZTdjNA==; BDUSS_BFESS=p-N1hDS2RScWJmTEJaa2lvUnd0TndvSWFPWEduRWYwRFlLTTY1eTctQ0V2aEZxSUFBQUFBJCQAAAAAAQAAAAEAAAA2Vgh9YWRvcmV0aGVhbGw5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIQx6mmEMeppTV; RT=\"z=1&dm=baidu.com&si=a7dc05c1-5cd0-40d0-be2e-a2b732c43138&ss=mochtsln&sl=1&tt=1au&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=956&ul=237i\""
BAIDU_INDEX_AREA = 0
BAIDU_INDEX_LOOKBACK_DAYS = 7
BAIDU_INDEX_DELAY_MIN = 1
BAIDU_INDEX_DELAY_MAX = 2
BAIDU_INDEX_RETRY_COUNT = 2
BAIDU_INDEX_RETRY_PAUSE = 3
BAIDU_INDEX_OUTPUT_FIELD = "上映前7天百度搜索指数均值"
BAIDU_INDEX_ALL_ZERO_WARN_THRESHOLD = 0.9
BAIDU_INDEX_ERROR_WARN_THRESHOLD = 0.8
BAIDU_TITLE_SPLIT_PATTERN = r"[：:（(【\[\-—·]"

# 目录配置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = BASE_DIR / "html_cache"
BAIDU_CACHE_DIR = BASE_DIR / "baidu_cache"
RAW_DIR = DATA_DIR / "raw"
FILTERED_DIR = DATA_DIR / "filtered"
BAIDU_DIR = DATA_DIR / "baidu"
FINAL_DIR = DATA_DIR / "final"
SRC_DIR = BASE_DIR / "src"

# 确保目录存在
for d in [DATA_DIR, HTML_DIR, BAIDU_CACHE_DIR, RAW_DIR, FILTERED_DIR, BAIDU_DIR, FINAL_DIR, SRC_DIR]:
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

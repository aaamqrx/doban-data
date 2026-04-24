# -*- coding: utf-8 -*-
import json
import re
from datetime import timedelta
from pathlib import Path

import pandas as pd

import config

from src.utils_dates import parse_release_date


INVALID_FILENAME_CHARS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']



def sanitize_filename(filename):
    """处理 Windows 非法字符"""
    text = str(filename or "").strip()
    for char in INVALID_FILENAME_CHARS:
        text = text.replace(char, "_")
    return text[:100]



def normalize_subject_id(value):
    """规范化 subject_id，兼容 Excel 读取后的数字格式"""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    match = re.search(r"(\d+)", text)
    return match.group(1) if match else text



def extract_subject_id_from_url(url):
    """从详情链接中提取豆瓣 subject id"""
    match = re.search(r"/subject/(\d+)/", str(url))
    return match.group(1) if match else ""



def clean_baidu_query_title(movie_name):
    """按配置规则清洗百度指数查询词，优先砍掉副标题"""
    raw_title = str(movie_name or "").strip()
    if not raw_title:
        return ""

    parts = re.split(config.BAIDU_TITLE_SPLIT_PATTERN, raw_title, maxsplit=1)
    cleaned_title = parts[0].strip() if parts else raw_title
    return cleaned_title if len(cleaned_title) >= 2 else raw_title



def build_pre_release_window(release_date):
    """构建上映前 7 天查询窗口，不包含上映当天"""
    release_day = parse_release_date(release_date) if not hasattr(release_date, "isoformat") else release_date
    if release_day is None:
        return None, None

    end_day = release_day - timedelta(days=1)
    start_day = release_day - timedelta(days=config.BAIDU_INDEX_LOOKBACK_DAYS)
    return start_day, end_day



def iter_date_strings(start_day, end_day):
    """生成闭区间日期字符串列表"""
    if start_day is None or end_day is None or end_day < start_day:
        return []

    current_day = start_day
    dates = []
    while current_day <= end_day:
        dates.append(current_day.isoformat())
        current_day += timedelta(days=1)
    return dates



def build_baidu_cache_path(type_dir, movie_name, subject_id=""):
    """生成百度指数缓存路径"""
    safe_name = sanitize_filename(movie_name) or "untitled"
    normalized_subject_id = normalize_subject_id(subject_id)
    if normalized_subject_id:
        return type_dir / f"{normalized_subject_id}_{safe_name}.json"
    return type_dir / f"{safe_name}.json"



def load_baidu_cache(cache_path):
    """读取百度指数缓存 JSON"""
    if cache_path is None or not cache_path.exists() or not cache_path.is_file():
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None



def is_baidu_cache_usable(cache_path):
    """判断缓存 JSON 是否可直接复用"""
    cache_data = load_baidu_cache(cache_path)
    if not isinstance(cache_data, dict):
        return False

    status = str(cache_data.get("百度指数状态", "")).strip()
    if status == "error":
        return False
    if status == "missing_release_date":
        return True

    daily_values = cache_data.get("百度指数日值列表")
    return isinstance(daily_values, list)



def find_existing_baidu_cache(type_dir, movie_name, subject_id=""):
    """查找可复用的百度指数缓存"""
    normalized_subject_id = normalize_subject_id(subject_id)
    if normalized_subject_id:
        for match in sorted(type_dir.glob(f"{normalized_subject_id}_*.json")):
            if is_baidu_cache_usable(match):
                return match

    safe_name = sanitize_filename(movie_name) or "untitled"
    direct_path = type_dir / f"{safe_name}.json"
    if is_baidu_cache_usable(direct_path):
        return direct_path

    for match in sorted(type_dir.glob(f"{safe_name}_*.json")):
        if is_baidu_cache_usable(match):
            return match

    return None



def find_any_baidu_cache(type_dir, movie_name, subject_id=""):
    """查找任意状态的百度指数缓存，供解析阶段保留错误状态"""
    normalized_subject_id = normalize_subject_id(subject_id)
    if normalized_subject_id:
        matches = sorted(type_dir.glob(f"{normalized_subject_id}_*.json"))
        if matches:
            return matches[0]

    safe_name = sanitize_filename(movie_name) or "untitled"
    direct_path = type_dir / f"{safe_name}.json"
    if direct_path.exists() and direct_path.is_file():
        return direct_path

    matches = sorted(type_dir.glob(f"{safe_name}_*.json"))
    if matches:
        return matches[0]

    return None



def count_non_zero_days(daily_values):
    """统计日值列表中非零天数"""
    count = 0
    for item in daily_values or []:
        try:
            value = float(item.get("value", 0))
        except Exception:
            value = 0
        if value != 0:
            count += 1
    return count

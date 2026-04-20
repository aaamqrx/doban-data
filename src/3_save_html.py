# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import random
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def sanitize_filename(filename):
    """处理Windows非法字符"""
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]


def extract_subject_id(url):
    """从详情链接中提取豆瓣subject id"""
    match = re.search(r"/subject/(\d+)/", str(url))
    return match.group(1) if match else ""


def normalize_subject_id(value):
    """规范化subject_id，兼容Excel读取后的数字格式"""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    match = re.search(r"(\d+)", text)
    return match.group(1) if match else text


def find_existing_html(type_dir, movie_name, url, subject_id=""):
    """查找已存在的HTML，确保断点续传判断和命名规则一致"""
    subject_id = normalize_subject_id(subject_id) or extract_subject_id(url)
    if subject_id:
        matches = sorted(type_dir.glob(f"{subject_id}_*.html"))
        if matches:
            return matches[0]

    safe_name = sanitize_filename(str(movie_name)) or "untitled"
    direct_path = type_dir / f"{safe_name}.html"
    if direct_path.exists():
        return direct_path

    matches = sorted(type_dir.glob(f"{safe_name}_*.html"))
    if matches:
        return matches[0]

    return None


def build_html_path(type_dir, movie_name, url, subject_id=""):
    """生成稳定的HTML保存路径"""
    safe_name = sanitize_filename(str(movie_name)) or "untitled"
    subject_id = normalize_subject_id(subject_id) or extract_subject_id(url)

    if subject_id:
        return type_dir / f"{subject_id}_{safe_name}.html"

    html_path = type_dir / f"{safe_name}.html"
    if not html_path.exists():
        return html_path

    counter = 2
    while True:
        candidate = type_dir / f"{safe_name}_{counter}.html"
        if not candidate.exists():
            return candidate
        counter += 1


def create_session():
    """创建带基础重试能力的会话"""
    session = requests.Session()
    session.headers.update(config.HEADERS)
    session.cookies.update(config.COOKIES)

    retry = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def classify_html_page(html_text):
    """将页面分为有效、风控拦截或普通无效页面"""
    if not html_text or not html_text.strip():
        return "invalid", "页面内容为空"

    blocked_keywords = ["禁止访问", "异常请求", "验证码", "登录豆瓣", "访问受限"]
    for keyword in blocked_keywords:
        if keyword in html_text:
            return "blocked", f"页面包含拦截提示：{keyword}"

    invalid_keywords = ["页面不存在", "条目不存在"]
    for keyword in invalid_keywords:
        if keyword in html_text:
            return "invalid", f"页面包含无效提示：{keyword}"

    soup = BeautifulSoup(html_text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    if "禁止访问" in title or "访问受限" in title:
        return "blocked", f"页面标题异常：{title[:30]}"
    if "豆瓣" not in title:
        return "invalid", f"页面标题异常：{title[:30] or '无标题'}"

    has_movie_signals = (
        soup.find("div", id="info")
        or soup.find("a", attrs={"rel": "v:directedBy"})
        or soup.find("span", attrs={"property": "v:runtime"})
        or soup.find("span", property="v:itemreviewed")
        or soup.find("script", attrs={"type": "application/ld+json"})
        or soup.find("meta", attrs={"property": "og:title"})
        or soup.find("meta", attrs={"name": "description"})
    )
    if has_movie_signals:
        return "valid", ""

    return "valid", "页面结构较简化，按正常电影页保存"


def sleep_normal_delay():
    time.sleep(random.uniform(config.DELAY_MIN, config.DELAY_MAX))


def sleep_batch_pause():
    pause_seconds = random.uniform(config.BATCH_PAUSE_MIN, config.BATCH_PAUSE_MAX)
    print(f"⏸️ 批次暂停 {pause_seconds:.0f} 秒，降低风控概率...")
    time.sleep(pause_seconds)


def sleep_block_pause():
    pause_seconds = random.uniform(config.BLOCK_PAUSE_MIN, config.BLOCK_PAUSE_MAX)
    print(f"⏸️ 连续命中风控，暂停 {pause_seconds:.0f} 秒后继续...")
    time.sleep(pause_seconds)


def fetch_movie_html(session, movie_name, url):
    """下载单个电影页面，遇到风控页时有限次退避重试"""
    for attempt in range(config.BLOCK_RETRY_COUNT + 1):
        response = session.get(url, timeout=config.REQUEST_TIMEOUT)
        response.encoding = "utf-8"
        print(f"   状态码: {response.status_code}")
        response.raise_for_status()

        page_type, reason = classify_html_page(response.text)
        if page_type == "valid":
            return "valid", response.text, ""

        if page_type == "blocked" and attempt < config.BLOCK_RETRY_COUNT:
            retry_pause = config.BLOCK_RETRY_PAUSES[min(attempt, len(config.BLOCK_RETRY_PAUSES) - 1)]
            print(f"   ⚠️ 命中风控：{reason}，{retry_pause} 秒后重试...")
            time.sleep(retry_pause)
            continue

        return page_type, "", reason

    return "invalid", "", "未知页面状态"


if __name__ == "__main__":
    print("=" * 50)
    print("第3步：下载电影详情页HTML")
    print("=" * 50)

    session = create_session()

    for excel_file in config.FILTERED_DIR.glob("china_*.xlsx"):
        movie_type = excel_file.stem.replace("china_", "")
        if movie_type not in config.MOVIE_TYPES:
            continue

        type_name = config.MOVIE_TYPES[movie_type]["name"]
        type_dir = config.HTML_DIR / movie_type
        type_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_excel(excel_file)
        df = df[df["详情链接"].notna()].reset_index(drop=True)

        print(f"\n正在下载 {type_name}，共 {len(df)} 部...")
        success_count = 0
        skip_count = 0
        fail_count = 0
        blocked_count = 0
        consecutive_blocked = 0

        for idx, row in df.iterrows():
            movie_name = row["电影名"]
            url = row["详情链接"]
            subject_id = normalize_subject_id(row.get("subject_id", "") if hasattr(row, "get") else "")
            existing_html = find_existing_html(type_dir, movie_name, url, subject_id)

            if existing_html is not None:
                print(f"⏩ [{idx + 1}/{len(df)}] 已存在，跳过：{movie_name} -> {existing_html.name}")
                skip_count += 1
                continue

            if idx > 0 and idx % config.BATCH_SIZE == 0:
                sleep_batch_pause()

            html_path = build_html_path(type_dir, movie_name, url, subject_id)

            try:
                print(f"🔍 [{idx + 1}/{len(df)}] 正在请求：{movie_name}")
                print(f"   URL: {url}")
                page_type, html_text, reason = fetch_movie_html(session, movie_name, url)

                if page_type == "valid":
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_text)

                    print(f"✅ [{idx + 1}/{len(df)}] 下载成功：{movie_name} -> {html_path.name}")
                    success_count += 1
                    consecutive_blocked = 0
                elif page_type == "blocked":
                    print(f"❌ [{idx + 1}/{len(df)}] 页面被拦截：{movie_name} - {reason}")
                    fail_count += 1
                    blocked_count += 1
                    consecutive_blocked += 1

                    if consecutive_blocked >= config.STOP_BLOCKED_THRESHOLD:
                        print("🛑 连续多次命中风控，建议更新 Cookie 后再继续运行。")
                        break
                    if consecutive_blocked >= config.BLOCKED_THRESHOLD:
                        sleep_block_pause()
                else:
                    print(f"❌ [{idx + 1}/{len(df)}] 页面无效：{movie_name} - {reason}")
                    fail_count += 1
                    consecutive_blocked = 0

            except Exception as e:
                print(f"❌ [{idx + 1}/{len(df)}] 下载失败：{movie_name} - {str(e)[:80]}")
                fail_count += 1
                consecutive_blocked = 0

            sleep_normal_delay()

        print(
            f"✅ {type_name} 完成：新增成功 {success_count} 部，已跳过 {skip_count} 部，失败 {fail_count} 部，其中风控拦截 {blocked_count} 部"
        )

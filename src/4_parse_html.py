# -*- coding: utf-8 -*-
import json
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import pandas as pd
from bs4 import BeautifulSoup


def extract_subject_id_from_url(url):
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



def extract_subject_id_from_filename(file_name):
    """从HTML文件名中提取豆瓣subject id"""
    match = re.match(r"(\d+)_", file_name)
    return match.group(1) if match else ""



def load_movie_json_ld(soup):
    """提取页面中的 Movie JSON-LD 数据"""
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for script in scripts:
        raw_text = script.string or script.get_text()
        if not raw_text:
            continue
        try:
            data = json.loads(raw_text.strip())
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            if item_type == "Movie" or (isinstance(item_type, list) and "Movie" in item_type):
                return item

    return {}



def extract_person_names(person_data):
    """从JSON-LD人物字段中提取姓名"""
    if isinstance(person_data, dict):
        return person_data.get("name", "")
    if isinstance(person_data, list):
        names = [item.get("name", "") for item in person_data if isinstance(item, dict) and item.get("name")]
        return " / ".join(names)
    return ""



def normalize_runtime(runtime_text):
    """统一片长格式，兼容JSON-LD的ISO8601时长"""
    text = str(runtime_text or "").strip()
    if not text:
        return ""

    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", text)
    if not match:
        return text

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    total_minutes = hours * 60 + minutes
    return f"{total_minutes}分钟" if total_minutes else text



def extract_movie_info(html_file_path):
    """从HTML提取电影信息"""
    if not html_file_path.exists() or html_file_path.stat().st_size == 0:
        return None

    with open(html_file_path, "r", encoding="utf-8") as f:
        html_text = f.read()
        if not html_text or not html_text.strip():
            return None
        soup = BeautifulSoup(html_text, "html.parser")

    blocked_keywords = ["禁止访问", "异常请求", "验证码", "登录豆瓣"]
    title_text = soup.title.get_text(strip=True) if soup.title else ""
    if "禁止访问" in title_text or any(keyword in html_text for keyword in blocked_keywords):
        return None

    movie_json = load_movie_json_ld(soup)

    movie_name = title_text if title_text else ""
    movie_name = movie_name.replace(" - 豆瓣电影", "").replace(" (豆瓣)", "").strip()
    if not movie_name:
        movie_name = str(movie_json.get("name", "") or "").strip()

    director_elem = soup.find("a", attrs={"rel": "v:directedBy"})
    director = director_elem.get_text(strip=True) if director_elem else ""
    if not director:
        director = extract_person_names(movie_json.get("director")) or "未提取到导演"

    runtime_elem = soup.find("span", attrs={"property": "v:runtime"})
    runtime = runtime_elem.get_text(strip=True) if runtime_elem else ""
    if not runtime:
        runtime = normalize_runtime(movie_json.get("duration")) or "未提取到片长"

    summary_elem = soup.find("span", attrs={"property": "v:summary"})
    summary = ""
    if summary_elem:
        summary = " ".join(summary_elem.get_text(" ", strip=True).split())
    if not summary:
        summary = " ".join(str(movie_json.get("description", "") or "").split())

    info_div = soup.find("div", id="info")
    imdb_id = ""
    if info_div:
        info_text = info_div.get_text("\n", strip=True)
        imdb_match = re.search(r"IMDb:\s*([A-Za-z]{2}\d+|tt\d+)", info_text, re.IGNORECASE)
        if imdb_match:
            imdb_id = imdb_match.group(1)

    subject_id = extract_subject_id_from_filename(html_file_path.name)
    if not subject_id:
        url_value = str(movie_json.get("url", "") or "")
        subject_id = extract_subject_id_from_url(url_value)

    return {
        "subject_id": subject_id,
        "电影名": movie_name,
        "导演": director,
        "片长": runtime,
        "剧情简介": summary,
        "IMDb编号": imdb_id,
    }


if __name__ == "__main__":
    print("=" * 50)
    print("第4步：解析HTML并合并数据")
    print("=" * 50)

    parsed_data = []
    for type_folder in config.HTML_DIR.iterdir():
        if not type_folder.is_dir():
            continue

        movie_type = type_folder.name
        if movie_type not in config.MOVIE_TYPES:
            continue

        type_name = config.MOVIE_TYPES[movie_type]["name"]
        html_files = list(type_folder.glob("*.html"))
        print(f"\n正在解析 {type_name}，共 {len(html_files)} 个HTML文件...")

        for idx, html_file in enumerate(html_files, 1):
            try:
                info = extract_movie_info(html_file)
                if info is None:
                    print(f"  ⏩ 跳过无效HTML：{html_file.name}")
                    continue
                parsed_data.append(info)

                if idx % 100 == 0:
                    print(f"  已解析 {idx}/{len(html_files)}...")
            except Exception:
                print(f"  ❌ 解析失败：{html_file.name}")

    df_parsed = pd.DataFrame(parsed_data)
    print(f"\n✅ 共解析 {len(df_parsed)} 条数据")

    excel_dfs = []
    for excel_file in config.FILTERED_DIR.glob("china_*.xlsx"):
        df = pd.read_excel(excel_file)
        if "subject_id" not in df.columns:
            df["subject_id"] = ""
        df["subject_id"] = df["subject_id"].apply(normalize_subject_id)
        missing_subject_mask = df["subject_id"] == ""
        df.loc[missing_subject_mask, "subject_id"] = df.loc[missing_subject_mask, "详情链接"].apply(extract_subject_id_from_url)
        excel_dfs.append(df)

    df_base = pd.concat(excel_dfs, ignore_index=True) if excel_dfs else pd.DataFrame()
    print(f"✅ 读取基础数据 {len(df_base)} 条")

    if not df_base.empty and not df_parsed.empty:
        parsed_with_id = df_parsed[df_parsed["subject_id"] != ""].copy()
        parsed_with_id = parsed_with_id.drop_duplicates(subset=["subject_id"])

        base_with_id = df_base[df_base["subject_id"] != ""].copy()
        base_without_id = df_base[df_base["subject_id"] == ""].copy()

        merged_with_id = pd.merge(
            base_with_id,
            parsed_with_id[["subject_id", "导演", "片长", "剧情简介", "IMDb编号"]],
            on=["subject_id"],
            how="left",
        )

        parsed_name_fallback = df_parsed.drop_duplicates(subset=["电影名"]).copy()
        merged_without_id = pd.merge(
            base_without_id,
            parsed_name_fallback[["电影名", "导演", "片长", "剧情简介", "IMDb编号"]],
            on=["电影名"],
            how="left",
        )

        df_final = pd.concat([merged_with_id, merged_without_id], ignore_index=True)
    else:
        df_final = df_base.copy()
        for column in ["导演", "片长", "剧情简介", "IMDb编号"]:
            if column not in df_final.columns:
                df_final[column] = pd.NA

    output_path = config.FINAL_DIR / "china_all.xlsx"
    df_final.to_excel(output_path, index=False)

    print(f"\n🎉 完成！最终数据 {len(df_final)} 条")
    print(f"💾 已保存至：{output_path}")
    print(f"\n📊 数据字段：{list(df_final.columns)}")

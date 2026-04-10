# -*- coding: utf-8 -*-
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



def extract_subject_id_from_filename(file_name):
    """从HTML文件名中提取豆瓣subject id"""
    match = re.match(r"(\d+)_", file_name)
    return match.group(1) if match else ""



def extract_movie_info(html_file_path):
    """从HTML提取电影信息"""
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_text = f.read()
        soup = BeautifulSoup(html_text, "html.parser")

    blocked_keywords = ["禁止访问", "异常请求", "验证码", "登录豆瓣"]
    title_text = soup.title.get_text(strip=True) if soup.title else ""
    if "禁止访问" in title_text or any(keyword in html_text for keyword in blocked_keywords):
        return None

    movie_name = title_text if title_text else ""
    movie_name = movie_name.replace(" - 豆瓣电影", "").replace(" (豆瓣)", "").strip()

    director_elem = soup.find("a", attrs={"rel": "v:directedBy"})
    director = director_elem.get_text(strip=True) if director_elem else "未提取到导演"

    runtime_elem = soup.find("span", attrs={"property": "v:runtime"})
    runtime = runtime_elem.get_text(strip=True) if runtime_elem else "未提取到片长"

    subject_id = extract_subject_id_from_filename(html_file_path.name)

    return {"subject_id": subject_id, "电影名": movie_name, "导演": director, "片长": runtime}


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
                info["影片类型"] = type_name
                parsed_data.append(info)

                if idx % 100 == 0:
                    print(f"  已解析 {idx}/{len(html_files)}...")
            except Exception:
                print(f"  ❌ 解析失败：{html_file.name}")

    df_parsed = pd.DataFrame(parsed_data)
    print(f"\n✅ 共解析 {len(df_parsed)} 条数据")

    excel_dfs = []
    for excel_file in config.FILTERED_DIR.glob("china_*.xlsx"):
        if excel_file.name == "china_all.xlsx":
            continue
        df = pd.read_excel(excel_file)
        df["subject_id"] = df["详情链接"].apply(extract_subject_id_from_url)
        excel_dfs.append(df)

    df_base = pd.concat(excel_dfs, ignore_index=True) if excel_dfs else pd.DataFrame()
    print(f"✅ 读取基础数据 {len(df_base)} 条")

    if not df_base.empty and not df_parsed.empty:
        parsed_with_id = df_parsed[df_parsed["subject_id"] != ""].copy()
        base_with_id = df_base[df_base["subject_id"] != ""].copy()
        base_without_id = df_base[df_base["subject_id"] == ""].copy()

        merged_with_id = pd.merge(
            base_with_id,
            parsed_with_id[["subject_id", "影片类型", "导演", "片长"]],
            on=["subject_id", "影片类型"],
            how="left",
        )

        parsed_name_fallback = df_parsed.drop_duplicates(subset=["电影名", "影片类型"]).copy()
        merged_without_id = pd.merge(
            base_without_id,
            parsed_name_fallback[["电影名", "影片类型", "导演", "片长"]],
            on=["电影名", "影片类型"],
            how="left",
        )

        df_final = pd.concat([merged_with_id, merged_without_id], ignore_index=True)
    else:
        df_final = df_base.copy()
        if "导演" not in df_final.columns:
            df_final["导演"] = pd.NA
        if "片长" not in df_final.columns:
            df_final["片长"] = pd.NA

    output_path = config.FILTERED_DIR / "china_all.xlsx"
    df_final.to_excel(output_path, index=False)

    print(f"\n🎉 完成！最终数据 {len(df_final)} 条")
    print(f"💾 已保存至：{output_path}")
    print(f"\n📊 数据字段：{list(df_final.columns)}")

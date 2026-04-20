# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import random
import time
from datetime import datetime

import pandas as pd
import requests


def get_interval_ranges():
    """生成豆瓣评分区间，按 100:90 到 10:0 遍历"""
    return [f"{high}:{high - 10}" for high in range(100, 0, -10)]



def fetch_movies_by_type(movie_type, type_id):
    """分页抓取单个类型的所有电影"""
    all_movies = []

    for interval_id in get_interval_ranges():
        print(f"  开始抓取评分区间：{interval_id}")
        start = 0
        interval_total = 0

        while True:
            url = (
                "https://movie.douban.com/j/chart/top_list"
                f"?type={type_id}&interval_id={interval_id}&action=&start={start}&limit={config.LIMIT_PER_PAGE}"
            )
            print(f"    正在请求：{url}")

            try:
                response = requests.get(
                    url,
                    headers=config.HEADERS,
                    cookies=config.COOKIES,
                    timeout=20,
                )
                response.encoding = "utf-8"
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, list):
                    print("    ❌ 接口返回的不是列表，返回内容如下：")
                    print(str(data)[:200])
                    break

                print(f"    本页返回 {len(data)} 条")

                if len(data) == 0:
                    print(f"    评分区间 {interval_id} 抓取结束")
                    break

                all_movies.extend(data)
                interval_total += len(data)
                start += config.LIMIT_PER_PAGE
                print(f"    区间累计 {interval_total} 条，总累计 {len(all_movies)} 条...")
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"    ❌ 请求失败：{str(e)}")
                break

    return all_movies


def deduplicate_movies(movies):
    """优先按subject_id去重，缺失时回退按详情链接去重"""
    seen = set()
    unique_movies = []

    for movie in movies:
        subject_id = str(movie.get("id", "") or "").strip()
        url = str(movie.get("url", "") or "").strip()
        dedupe_key = f"id:{subject_id}" if subject_id else f"url:{url}"

        if dedupe_key in seen or (not subject_id and not url):
            continue

        seen.add(dedupe_key)
        unique_movies.append(movie)

    return unique_movies


def save_to_excel(movies, output_path):
    """保存为Excel"""
    movie_list = []
    for item in movies:
        movie_list.append(
            {
                "subject_id": item.get("id", ""),
                "电影名": item.get("title", ""),
                "评分": item.get("score", ""),
                "评价人数": item.get("vote_count", ""),
                "主演": ",".join(item.get("actors", [])),
                "制片国家/地区": ",".join(item.get("regions", [])),
                "类型": ",".join(item.get("types", [])),
                "上映时间": item.get("release_date", ""),
                "详情链接": item.get("url", ""),
            }
        )

    df = pd.DataFrame(movie_list)
    print(f"  准备保存 {len(df)} 条数据到：{output_path}")

    try:
        df.to_excel(output_path, index=False)
    except PermissionError as e:
        raise PermissionError(
            f"无法写入文件：{output_path}。请先关闭正在打开的 Excel 文件后重试。"
        ) from e
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "缺少 openpyxl 依赖，请先执行：pip install openpyxl"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"保存 Excel 失败：{output_path}。请检查输出目录是否可写，或确认 openpyxl 是否安装正常。原始错误：{e}"
        ) from e

    return len(df)


if __name__ == "__main__":
    print("=" * 50)
    print("第1步：抓取豆瓣原始数据")
    print("=" * 50)

    for movie_type, cfg in config.MOVIE_TYPES.items():
        print(f"\n正在抓取 {cfg['name']} 片...")
        movies = fetch_movies_by_type(movie_type, cfg["type_id"])
        unique_movies = deduplicate_movies(movies)

        output_path = config.RAW_DIR / f"{movie_type}.xlsx"
        count = save_to_excel(unique_movies, output_path)
        print(f"✅ {cfg['name']} 抓取完成，共 {count} 条，保存至 {output_path}")

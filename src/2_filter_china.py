# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import pandas as pd


def is_china_movie(regions):
    """判断是否为中国地区电影（大陆/香港/台湾）"""
    if pd.isna(regions):
        return False
    regions_str = str(regions)
    return any(keyword in regions_str for keyword in config.CHINA_KEYWORDS)


if __name__ == "__main__":
    print("=" * 50)
    print("第2步：筛选中国地区电影")
    print("=" * 50)

    for excel_file in config.RAW_DIR.glob("*.xlsx"):
        movie_type = excel_file.stem
        if movie_type not in config.MOVIE_TYPES:
            print(f"⏩ 跳过未配置类型文件：{excel_file.name}")
            continue

        type_name = config.MOVIE_TYPES[movie_type]["name"]
        print(f"\n正在处理 {type_name}...")

        df = pd.read_excel(excel_file)
        china_mask = df["制片国家/地区"].apply(is_china_movie)
        china_df = df[china_mask].copy()
        china_df["影片类型"] = type_name

        if "类型" in china_df.columns:
            china_df = china_df.drop(columns=["类型"])

        cols = ["电影名", "主演", "制片国家/地区", "影片类型", "上映时间", "详情链接"]
        china_df = china_df[[column for column in cols if column in china_df.columns]]

        output_path = config.FILTERED_DIR / f"china_{movie_type}.xlsx"
        china_df.to_excel(output_path, index=False)
        print(f"✅ 筛选完成，中国地区 {type_name} 共 {len(china_df)} 部")

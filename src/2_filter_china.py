# -*- coding: utf-8 -*-
import sys
from datetime import timedelta
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import chinese_calendar as calendar
import pandas as pd

from src.utils_dates import parse_release_date

try:
    from lunardate import LunarDate
except ModuleNotFoundError:
    LunarDate = None


HOLIDAY_CALENDAR_MIN_YEAR = 2004
HOLIDAY_CALENDAR_MAX_YEAR = 2026


def is_china_movie(regions):
    """判断是否为中国地区电影（大陆/香港/台湾）"""
    if pd.isna(regions):
        return False
    regions_str = str(regions)
    return any(keyword in regions_str for keyword in config.CHINA_KEYWORDS)


def matches_holiday_window(release_day, holiday_names):
    """向前侦测3天，判断是否命中目标节假日档期"""
    if release_day is None:
        return 0

    for offset in range(4):
        check_day = release_day + timedelta(days=offset)
        if check_day.year < 2004 or check_day.year > 2026:
            continue

        try:
            is_holiday, holiday_name = calendar.get_holiday_detail(check_day)
        except NotImplementedError:
            continue

        if is_holiday and holiday_name in holiday_names:
            return 1
    return 0


def is_out_of_holiday_calendar_range(release_date):
    """判断上映日期是否超出 chinesecalendar 支持年份范围"""
    release_day = parse_release_date(release_date)
    if release_day is None:
        return False
    return release_day.year < HOLIDAY_CALENDAR_MIN_YEAR or release_day.year > HOLIDAY_CALENDAR_MAX_YEAR



def build_release_window_flags(release_date):
    """生成档期布尔特征"""
    release_day = parse_release_date(release_date)
    if release_day is None:
        return {
            "是否春节档": 0,
            "是否国庆档": 0,
            "是否五一档": 0,
            "是否暑期档": 0,
            "是否普通周末": 0,
        }

    spring_festival = matches_holiday_window(release_day, {"Spring Festival", "Chinese New Year", "春节"})
    national_day = matches_holiday_window(release_day, {"National Day", "国庆节"})
    labour_day = matches_holiday_window(release_day, {"Labour Day", "Labor Day", "劳动节"})
    summer_vacation = 1 if (release_day.month == 7 or release_day.month == 8) else 0

    is_weekend = 1 if release_day.weekday() >= 5 else 0
    normal_weekend = 1 if is_weekend and not any([spring_festival, national_day, labour_day, summer_vacation]) else 0

    return {
        "是否春节档": spring_festival,
        "是否国庆档": national_day,
        "是否五一档": labour_day,
        "是否暑期档": summer_vacation,
        "是否普通周末": normal_weekend,
    }


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

        out_of_range_count = int(china_df["上映时间"].apply(is_out_of_holiday_calendar_range).sum())
        release_flags = china_df["上映时间"].apply(build_release_window_flags)
        release_flags_df = pd.DataFrame(list(release_flags), index=china_df.index)
        china_df = pd.concat([china_df, release_flags_df], axis=1)

        if "类型" in china_df.columns:
            china_df = china_df.drop(columns=["类型"])

        cols = [
            "subject_id",
            "电影名",
            "评分",
            "评价人数",
            "主演",
            "制片国家/地区",
            "影片类型",
            "上映时间",
            "是否春节档",
            "是否国庆档",
            "是否五一档",
            "是否暑期档",
            "是否普通周末",
            "详情链接",
        ]
        china_df = china_df[[column for column in cols if column in china_df.columns]]

        output_path = config.FILTERED_DIR / f"china_{movie_type}.xlsx"
        china_df.to_excel(output_path, index=False)
        print(f"✅ 筛选完成，中国地区 {type_name} 共 {len(china_df)} 部")
        print(f"ℹ️ 其中有 {out_of_range_count} 部电影因上映年份超出 chinesecalendar 支持范围，跳过了节假日档期判断")

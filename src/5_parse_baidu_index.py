# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import pandas as pd

from src.utils_baidu import (
    count_non_zero_days,
    extract_subject_id_from_url,
    find_any_baidu_cache,
    load_baidu_cache,
    normalize_subject_id,
)


DIAGNOSTIC_COLUMNS = [
    "百度指数状态",
    "百度指数错误信息",
    "百度指数查询词原始",
    "百度指数查询词清洗后",
    "百度指数样本天数",
    "百度指数非空天数",
]


def normalize_numeric_value(value):
    if value is None:
        return 0.0
    try:
        if pd.isna(value):
            return 0.0
    except Exception:
        pass

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0
    if text.lower() in {"nan", "none", "null", "na", "n/a"}:
        return 0.0
    if "未收录" in text or "暂无" in text:
        return 0.0

    text = text.replace(",", "")
    try:
        return float(text)
    except Exception:
        return 0.0


def build_baidu_features(cache_data):
    default_result = {
        config.BAIDU_INDEX_OUTPUT_FIELD: pd.NA,
        "百度指数状态": "missing_cache",
        "百度指数错误信息": "未找到缓存文件",
        "百度指数查询词原始": "",
        "百度指数查询词清洗后": "",
        "百度指数样本天数": 0,
        "百度指数非空天数": 0,
    }
    if not isinstance(cache_data, dict):
        return default_result

    status = str(cache_data.get("百度指数状态", "") or "").strip() or "missing_cache"
    error_message = str(cache_data.get("百度指数错误信息", "") or "").strip()
    query_raw = str(cache_data.get("百度指数查询词原始", "") or "").strip()
    query_clean = str(cache_data.get("百度指数查询词清洗后", "") or "").strip()
    daily_values = cache_data.get("百度指数日值列表")
    if not isinstance(daily_values, list):
        daily_values = []

    sample_count = len(daily_values)
    non_zero_days = count_non_zero_days(daily_values)

    if status == "missing_release_date":
        return {
            config.BAIDU_INDEX_OUTPUT_FIELD: pd.NA,
            "百度指数状态": "missing_release_date",
            "百度指数错误信息": error_message or "上映日期缺失或无法解析",
            "百度指数查询词原始": query_raw,
            "百度指数查询词清洗后": query_clean,
            "百度指数样本天数": sample_count,
            "百度指数非空天数": non_zero_days,
        }

    if status == "error":
        return {
            config.BAIDU_INDEX_OUTPUT_FIELD: pd.NA,
            "百度指数状态": "error",
            "百度指数错误信息": error_message,
            "百度指数查询词原始": query_raw,
            "百度指数查询词清洗后": query_clean,
            "百度指数样本天数": sample_count,
            "百度指数非空天数": non_zero_days,
        }

    if not daily_values:
        return {
            config.BAIDU_INDEX_OUTPUT_FIELD: pd.NA,
            "百度指数状态": status or "missing_cache",
            "百度指数错误信息": error_message or "缓存缺少日值数据",
            "百度指数查询词原始": query_raw,
            "百度指数查询词清洗后": query_clean,
            "百度指数样本天数": sample_count,
            "百度指数非空天数": non_zero_days,
        }

    numeric_values = [normalize_numeric_value(item.get("value", 0) if isinstance(item, dict) else 0) for item in daily_values]
    mean_value = sum(numeric_values) / len(numeric_values) if numeric_values else pd.NA
    normalized_status = "zero_valid" if numeric_values and all(value == 0 for value in numeric_values) else status

    return {
        config.BAIDU_INDEX_OUTPUT_FIELD: mean_value,
        "百度指数状态": normalized_status,
        "百度指数错误信息": error_message,
        "百度指数查询词原始": query_raw,
        "百度指数查询词清洗后": query_clean,
        "百度指数样本天数": sample_count,
        "百度指数非空天数": non_zero_days,
    }


if __name__ == "__main__":
    print("=" * 50)
    print("第5步：解析百度指数缓存并生成中间表")
    print("=" * 50)

    for excel_file in config.FILTERED_DIR.glob("china_*.xlsx"):
        movie_type = excel_file.stem.replace("china_", "")
        if movie_type not in config.MOVIE_TYPES:
            continue

        type_name = config.MOVIE_TYPES[movie_type]["name"]
        type_cache_dir = config.BAIDU_CACHE_DIR / movie_type

        df = pd.read_excel(excel_file)
        if "subject_id" not in df.columns:
            df["subject_id"] = ""
        df["subject_id"] = df["subject_id"].apply(normalize_subject_id)
        missing_subject_mask = df["subject_id"] == ""
        df.loc[missing_subject_mask, "subject_id"] = df.loc[missing_subject_mask, "详情链接"].apply(extract_subject_id_from_url)

        print(f"\n正在处理 {type_name}，共 {len(df)} 部...")
        feature_rows = []
        matched_count = 0
        missing_cache_count = 0
        error_count = 0
        zero_valid_count = 0

        for _, row in df.iterrows():
            movie_name = str(row.get("电影名", "") if hasattr(row, "get") else "").strip()
            subject_id = normalize_subject_id(row.get("subject_id", "") if hasattr(row, "get") else "")
            cache_path = find_any_baidu_cache(type_cache_dir, movie_name, subject_id)
            cache_data = load_baidu_cache(cache_path) if cache_path is not None else None
            features = build_baidu_features(cache_data)
            feature_rows.append(features)

            status = features["百度指数状态"]
            if cache_path is None:
                missing_cache_count += 1
            else:
                matched_count += 1
            if status == "error":
                error_count += 1
            if status == "zero_valid":
                zero_valid_count += 1

        feature_df = pd.DataFrame(feature_rows, index=df.index)
        result_df = pd.concat([df, feature_df], axis=1)
        output_path = config.BAIDU_DIR / excel_file.name
        result_df.to_excel(output_path, index=False)

        print(
            f"✅ {type_name} 完成：匹配缓存 {matched_count} 部，缺失缓存 {missing_cache_count} 部，"
            f"错误缓存 {error_count} 部，全零有效 {zero_valid_count} 部"
        )
        print(f"💾 已保存至：{output_path}")

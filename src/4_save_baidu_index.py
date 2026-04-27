# -*- coding: utf-8 -*-
import importlib
import inspect
import json
import random
import sys
import time
from pathlib import Path

# 设置UTF-8编码并保持日志及时刷新
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
            write_through=True,
        )
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
            write_through=True,
        )

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config

import pandas as pd

from src.utils_baidu import (
    build_baidu_cache_write_path,
    build_pre_release_window,
    classify_baidu_result,
    clean_baidu_query_title,
    extract_subject_id_from_url,
    find_existing_baidu_cache,
    iter_date_strings,
    normalize_subject_id,
)
from src.utils_dates import parse_release_date


QDATA_FUNCTION_CANDIDATES = [
    ("qdata.baidu_index", "get_search_index"),
    ("qdata.baidu_index", "search_index"),
    ("qdata.baidu_index", "get_index"),
    ("qdata", "get_search_index"),
    ("qdata", "search_index"),
]

QDATA_CLASS_CANDIDATES = [
    ("qdata.baidu_index", "BaiduIndex", ["get_search_index", "search_index", "get_index"]),
]

QUERY_PARAM_NAMES = {"keyword", "keywords", "keywords_list", "word", "words", "query", "queries", "name", "names"}
START_PARAM_NAMES = {"start_date", "start", "begin_date", "begin", "startdate", "date_start", "from_date", "starttime", "stime"}
END_PARAM_NAMES = {"end_date", "end", "stop_date", "stop", "enddate", "date_end", "to_date", "endtime", "etime"}
COOKIE_PARAM_NAMES = {"cookie", "cookies", "ck"}
AREA_PARAM_NAMES = {"area", "area_code", "region", "province"}


def get_baidu_index_min_day():
    min_date = parse_release_date(getattr(config, "BAIDU_INDEX_MIN_DATE", "2011-01-01"))
    if min_date is None:
        raise RuntimeError("BAIDU_INDEX_MIN_DATE 配置无效")
    return min_date


def is_unsupported_baidu_date_window(start_day, end_day):
    min_day = get_baidu_index_min_day()
    return start_day is not None and end_day is not None and start_day < min_day


def is_bad_request_error(exc):
    error_text = str(exc).lower()
    return "10002" in error_text or "bad request" in error_text


def is_request_limited_error(exc):
    """判断 qdata/百度指数接口是否返回请求频率限制。"""
    error_text = str(exc)
    lowered_text = error_text.lower()
    limited_markers = [
        "request_limited",
        "rate limit",
        "too frequent",
        "请求过于频繁",
        "降低请求频率",
    ]
    return any(marker in lowered_text or marker in error_text for marker in limited_markers)


def materialize_baidu_result(raw_result):
    if raw_result is None:
        return []
    if isinstance(raw_result, list):
        return raw_result
    if isinstance(raw_result, pd.DataFrame):
        return raw_result.to_dict("records")
    if isinstance(raw_result, dict):
        return raw_result
    if hasattr(raw_result, "__iter__") and not isinstance(raw_result, (str, bytes, bytearray)):
        return list(raw_result)
    return raw_result



def write_json_atomically(cache_path, data):
    temp_path = cache_path.with_name(f".{cache_path.name}.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
        temp_path.replace(cache_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()



def sleep_baidu_delay():
    time.sleep(random.uniform(config.BAIDU_INDEX_DELAY_MIN, config.BAIDU_INDEX_DELAY_MAX))


def sleep_baidu_batch_pause():
    pause_seconds = random.uniform(config.BATCH_PAUSE_MIN, config.BATCH_PAUSE_MAX)
    print(f"⏸️ 百度指数批次暂停 {pause_seconds:.0f} 秒，降低风控概率...")
    time.sleep(pause_seconds)


def sleep_baidu_block_pause():
    pause_seconds = random.uniform(config.BLOCK_PAUSE_MIN, config.BLOCK_PAUSE_MAX)
    print(f"⏸️ 连续命中百度指数限流，暂停 {pause_seconds:.0f} 秒后继续...")
    time.sleep(pause_seconds)


def normalize_baidu_value(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        try:
            if pd.isna(value):
                return 0.0
        except Exception:
            pass
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    lowered = text.lower()
    if lowered in {"nan", "none", "null", "na", "n/a"}:
        return 0.0
    if "未收录" in text or "暂无" in text:
        return 0.0

    cleaned_text = text.replace(",", "")
    try:
        return float(cleaned_text)
    except Exception:
        match = pd.Series([cleaned_text]).str.extract(r"([-+]?\d+(?:\.\d+)?)")[0].iloc[0]
        if pd.isna(match):
            return 0.0
        return float(match)



def normalize_baidu_date(value):
    if value is None:
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()



def maybe_build_daily_item(node):
    if not isinstance(node, dict):
        return None

    date_keys = ["date", "日期", "day", "time", "datetime", "startDate", "start_date"]
    date_value = ""
    date_key = ""
    for key in date_keys:
        if key in node:
            date_value = normalize_baidu_date(node.get(key))
            if date_value:
                date_key = key
                break
    if not date_value:
        return None

    preferred_value_keys = [
        "value",
        "index",
        "all",
        "all_index",
        "search_index",
        "searchIndex",
        "count",
        "pc",
        "wise",
    ]
    for key in preferred_value_keys:
        if key in node and key != date_key and not isinstance(node.get(key), (dict, list, tuple, set)):
            return {"date": date_value, "value": normalize_baidu_value(node.get(key))}

    for key, value in node.items():
        if key == date_key or isinstance(value, (dict, list, tuple, set)):
            continue
        if key in {"keyword", "keywords", "word", "name", "type"}:
            continue
        return {"date": date_value, "value": normalize_baidu_value(value)}

    return None



def collect_daily_items(node, collected=None):
    if collected is None:
        collected = []

    if node is None:
        return collected

    if isinstance(node, pd.DataFrame):
        return collect_daily_items(node.to_dict("records"), collected)

    if isinstance(node, dict):
        item = maybe_build_daily_item(node)
        if item is not None:
            collected.append(item)

        for value in node.values():
            if isinstance(value, (dict, list, tuple, set, pd.DataFrame)):
                collect_daily_items(value, collected)
        return collected

    if isinstance(node, (list, tuple, set)):
        for item in node:
            collect_daily_items(item, collected)
        return collected

    if hasattr(node, "__iter__") and not isinstance(node, (str, bytes, bytearray)):
        for item in list(node):
            collect_daily_items(item, collected)
        return collected

    return collected



def filter_baidu_raw_items(raw_items):
    """优先保留 qdata 返回中的 all 日值"""
    if not isinstance(raw_items, list):
        return raw_items

    all_items = [item for item in raw_items if isinstance(item, dict) and str(item.get("type", "") or "").strip().lower() == "all"]
    return all_items if all_items else raw_items



def normalize_daily_values(raw_result, start_day, end_day):
    expected_dates = iter_date_strings(start_day, end_day)
    collected = collect_daily_items(raw_result)
    value_by_date = {}
    for item in collected:
        date_value = item.get("date", "")
        if date_value in expected_dates:
            value_by_date[date_value] = normalize_baidu_value(item.get("value", 0))

    return [{"date": date_value, "value": value_by_date.get(date_value, 0.0)} for date_value in expected_dates]



def build_cache_payload(subject_id, movie_name, query_raw, query_clean, release_day, start_day, end_day, daily_values, status, error_message):
    return {
        "subject_id": subject_id,
        "电影名": movie_name,
        "百度指数查询词原始": query_raw,
        "百度指数查询词清洗后": query_clean,
        "上映日期": release_day.isoformat() if release_day else "",
        "百度指数起始日期": start_day.isoformat() if start_day else "",
        "百度指数结束日期": end_day.isoformat() if end_day else "",
        "百度指数日值列表": daily_values,
        "百度指数状态": status,
        "百度指数错误信息": error_message,
    }



def build_call_kwargs(function_obj, query, start_date, end_date, cookie, area):
    signature = inspect.signature(function_obj)
    keyword_mapping = {
        "keyword": query,
        "keywords": [query],
        "keywords_list": [[query]],
        "word": query,
        "words": [query],
        "query": query,
        "queries": [query],
        "name": query,
        "names": [query],
        "start_date": start_date,
        "start": start_date,
        "begin_date": start_date,
        "begin": start_date,
        "startdate": start_date,
        "date_start": start_date,
        "from_date": start_date,
        "starttime": start_date,
        "stime": start_date,
        "end_date": end_date,
        "end": end_date,
        "stop_date": end_date,
        "stop": end_date,
        "enddate": end_date,
        "date_end": end_date,
        "to_date": end_date,
        "endtime": end_date,
        "etime": end_date,
        "cookie": cookie,
        "cookies": cookie,
        "ck": cookie,
        "area": area,
        "area_code": area,
        "region": area,
        "province": area,
    }

    has_var_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values())
    if has_var_kwargs:
        return {
            "keywords_list": [[query]],
            "start_date": start_date,
            "end_date": end_date,
            "cookies": cookie,
            "area": area,
        }

    kwargs = {}
    for param_name, param in signature.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        lower_name = param_name.lower()
        if lower_name in keyword_mapping:
            kwargs[param_name] = keyword_mapping[lower_name]

    return kwargs



def describe_callable(function_obj):
    module = inspect.getmodule(function_obj)
    module_name = module.__name__ if module else "<unknown>"
    try:
        file_path = inspect.getfile(function_obj)
    except Exception:
        file_path = "<unavailable>"

    try:
        signature = inspect.signature(function_obj)
        signature_text = str(signature)
    except Exception:
        signature = None
        signature_text = "<unavailable>"

    if inspect.ismethod(function_obj):
        callable_kind = "bound_method"
    elif inspect.isfunction(function_obj):
        callable_kind = "function"
    else:
        callable_kind = type(function_obj).__name__

    return {
        "module_name": module_name,
        "file_path": file_path,
        "signature": signature,
        "signature_text": signature_text,
        "callable_kind": callable_kind,
    }



def is_signature_compatible(function_obj):
    try:
        signature = inspect.signature(function_obj)
    except Exception as exc:
        return False, f"无法读取签名：{exc}"

    parameters = list(signature.parameters.values())
    if not parameters:
        return False, "签名无参数，无法绑定查询词和日期窗口"

    lower_names = {param.name.lower() for param in parameters}
    has_var_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters)
    has_query_param = bool(lower_names & QUERY_PARAM_NAMES)
    has_start_param = bool(lower_names & START_PARAM_NAMES)
    has_end_param = bool(lower_names & END_PARAM_NAMES)

    if has_var_kwargs:
        return True, "签名包含 **kwargs，可尝试关键字调用"
    if has_query_param and has_start_param and has_end_param:
        return True, "签名包含查询词和日期窗口参数"

    return False, f"签名不兼容：{signature}"



def print_qdata_package_diagnostics():
    try:
        qdata_package = importlib.import_module("qdata")
        package_file = getattr(qdata_package, "__file__", "<unavailable>")
        package_name = getattr(qdata_package, "__package__", "<unknown>")
        package_version = getattr(qdata_package, "__version__", "<unknown>")
        print(f"ℹ️ qdata 包：{package_name}")
        print(f"ℹ️ qdata 路径：{package_file}")
        print(f"ℹ️ qdata 版本：{package_version}")
    except Exception as exc:
        print(f"⚠️ 无法输出 qdata 包诊断信息：{exc}")



def print_fetcher_diagnostics(fetcher, fetcher_name, adapter_label=""):
    callable_info = describe_callable(fetcher)
    print(f"✅ 已加载 qdata 接口：{fetcher_name}")
    print(f"ℹ️ qdata callable 类型：{callable_info['callable_kind']}")
    print(f"ℹ️ qdata 模块：{callable_info['module_name']}")
    print(f"ℹ️ qdata 文件：{callable_info['file_path']}")
    print(f"ℹ️ qdata 签名：{callable_info['signature_text']}")
    if adapter_label:
        print(f"ℹ️ qdata 适配方式：{adapter_label}")



def call_baidu_function(function_obj, query, start_date, end_date, cookie, area):
    kwargs = build_call_kwargs(function_obj, query, start_date, end_date, cookie, area)
    if not kwargs:
        raise RuntimeError("qdata 百度指数接口签名不兼容：无法构造关键字参数")

    last_error = None
    
    # qdata 0.3.0+ 版本使用 keywords_list（嵌套列表）和 cookies 参数
    call_variants = [
        kwargs,
        {"keywords_list": [[query]], "start_date": start_date, "end_date": end_date, "cookies": cookie, "area": area},
        {"keywords": [[query]], "start_date": start_date, "end_date": end_date, "cookies": cookie, "area": area},
        {"keyword": query, "start_date": start_date, "end_date": end_date, "cookie": cookie, "area": area},
        {"keywords": [query], "start_date": start_date, "end_date": end_date, "cookie": cookie, "area": area},
        {"word": query, "start_date": start_date, "end_date": end_date, "cookie": cookie, "area": area},
        {"query": query, "start_date": start_date, "end_date": end_date, "cookie": cookie, "area": area},
        {"keyword": query, "start": start_date, "end": end_date, "cookie": cookie, "area": area},
    ]
    for candidate_kwargs in call_variants:
        try:
            return function_obj(**candidate_kwargs)
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"qdata 百度指数接口调用失败：{last_error}")



def resolve_qdata_fetcher():
    errors = []

    for module_name, attr_name in QDATA_FUNCTION_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
            candidate = getattr(module, attr_name, None)
            if not callable(candidate):
                continue

            is_compatible, reason = is_signature_compatible(candidate)
            if is_compatible:
                return candidate, f"{module_name}.{attr_name}", "direct_function"
            errors.append(f"{module_name}.{attr_name}: {reason}")
        except Exception as exc:
            errors.append(f"{module_name}.{attr_name}: {exc}")

    for module_name, class_name, methods in QDATA_CLASS_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
            class_obj = getattr(module, class_name, None)
            if not callable(class_obj):
                continue
        except Exception as exc:
            errors.append(f"{module_name}.{class_name}: {exc}")
            continue

        for init_args, init_kwargs in (((), {"cookie": config.BAIDU_INDEX_COOKIE}), ((), {"cookies": config.BAIDU_INDEX_COOKIE}), ((config.BAIDU_INDEX_COOKIE,), {}), ((), {})):
            try:
                client = class_obj(*init_args, **init_kwargs)
            except Exception as exc:
                errors.append(f"{module_name}.{class_name} init {init_args or init_kwargs}: {exc}")
                continue

            for method_name in methods:
                method = getattr(client, method_name, None)
                if not callable(method):
                    continue

                is_compatible, reason = is_signature_compatible(method)
                if is_compatible:
                    adapter_label = f"class_adapter: {module_name}.{class_name}.{method_name}"
                    return method, f"{module_name}.{class_name}.{method_name}", adapter_label
                errors.append(f"{module_name}.{class_name}.{method_name}: {reason}")

    raise ImportError("未找到 qdata 百度指数接口，请确认已安装 qdata 且版本支持百度指数。" + ("；" + " | ".join(errors) if errors else ""))



def fetch_baidu_result(fetcher, query, start_date, end_date):
    last_error = None
    for attempt in range(config.BAIDU_INDEX_RETRY_COUNT + 1):
        try:
            return call_baidu_function(
                fetcher,
                query,
                start_date,
                end_date,
                config.BAIDU_INDEX_COOKIE,
                config.BAIDU_INDEX_AREA,
            )
        except Exception as exc:
            last_error = exc
            if attempt < config.BAIDU_INDEX_RETRY_COUNT:
                time.sleep(config.BAIDU_INDEX_RETRY_PAUSE)
    raise last_error



def build_query_candidates(query_raw, query_clean):
    candidates = []
    for candidate in [query_clean, query_raw]:
        text = str(candidate or "").strip()
        if text and text not in candidates:
            candidates.append(text)
    return candidates



def try_fetch_baidu_result(fetcher, query_candidates, start_date, end_date):
    last_error = None
    last_empty_result = None
    for query_text in query_candidates:
        try:
            raw_result = fetch_baidu_result(fetcher, query_text, start_date, end_date)
            raw_items = materialize_baidu_result(raw_result)
            filtered_raw_items = filter_baidu_raw_items(raw_items)
            if not collect_daily_items(filtered_raw_items):
                last_empty_result = (query_text, raw_items)
                continue
            return query_text, raw_items, None
        except Exception as exc:
            last_error = exc
    if last_empty_result is not None:
        query_text, raw_items = last_empty_result
        return query_text, raw_items, None
    return "", None, last_error



def run_baidu_preflight(fetcher):
    query = config.BAIDU_INDEX_PREFLIGHT_QUERY
    start_date = config.BAIDU_INDEX_PREFLIGHT_START_DATE
    end_date = config.BAIDU_INDEX_PREFLIGHT_END_DATE
    print(f"🔎 百度指数预检：{query} {start_date}~{end_date}")
    try:
        raw_result = fetch_baidu_result(fetcher, query, start_date, end_date)
        raw_items = materialize_baidu_result(raw_result)
        filtered_raw_items = filter_baidu_raw_items(raw_items)
        extracted_count = len(collect_daily_items(filtered_raw_items))
        if extracted_count <= 0:
            raise RuntimeError("预检未提取到任何真实日期样本")
    except Exception as exc:
        raise RuntimeError(f"百度指数预检失败，请先检查 Cookie、qdata 或百度指数接口：{exc}") from exc
    print(f"✅ 百度指数预检通过，提取样本 {extracted_count} 条")


def evaluate_batch(batch_outcomes):
    if not batch_outcomes:
        return

    total = len(batch_outcomes)
    error_count = sum(1 for outcome in batch_outcomes if outcome in {"error", "request_limited"})
    error_ratio = error_count / total
    zero_ratio = batch_outcomes.count("zero") / total

    if error_ratio >= config.BAIDU_INDEX_ERROR_WARN_THRESHOLD:
        print("⚠️ 最近一批百度指数请求错误占比过高，Cookie 可能已失效。")
    if total >= 5 and zero_ratio >= config.BAIDU_INDEX_ALL_ZERO_WARN_THRESHOLD:
        print("⚠️ 最近一批百度指数结果几乎全为 0，请检查 Cookie 或查询词是否异常。")



if __name__ == "__main__":
    print("[bootstrap] 4_save_baidu_index.py started", flush=True)
    print("=" * 50)
    print("第4步：抓取并缓存百度指数")
    print("=" * 50)

    print_qdata_package_diagnostics()
    fetcher, fetcher_name, adapter_label = resolve_qdata_fetcher()
    print_fetcher_diagnostics(fetcher, fetcher_name, adapter_label)
    run_baidu_preflight(fetcher)

    for excel_file in config.FILTERED_DIR.glob("china_*.xlsx"):
        movie_type = excel_file.stem.replace("china_", "")
        if movie_type not in config.MOVIE_TYPES:
            continue

        type_name = config.MOVIE_TYPES[movie_type]["name"]
        type_dir = config.BAIDU_CACHE_DIR / movie_type
        type_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_excel(excel_file)
        print(f"\n正在处理 {type_name}，共 {len(df)} 部...")

        success_count = 0
        skip_count = 0
        fail_count = 0
        zero_count = 0
        empty_count = 0
        bad_request_count = 0
        request_limited_count = 0
        unsupported_date_count = 0
        missing_release_date_count = 0
        real_request_count = 0
        consecutive_limited = 0
        batch_outcomes = []

        for idx, row in df.iterrows():
            movie_name = str(row.get("电影名", "") if hasattr(row, "get") else row["电影名"]).strip()
            detail_url = row.get("详情链接", "") if hasattr(row, "get") else ""
            subject_id = normalize_subject_id(row.get("subject_id", "") if hasattr(row, "get") else "")
            if not subject_id:
                subject_id = extract_subject_id_from_url(detail_url)

            existing_cache = find_existing_baidu_cache(type_dir, movie_name, subject_id)
            if existing_cache is not None:
                print(f"⏩ [{idx + 1}/{len(df)}] 已存在可用缓存，跳过：{movie_name} -> {existing_cache.name}")
                skip_count += 1
                continue

            cache_path = build_baidu_cache_write_path(type_dir, movie_name, subject_id)
            query_raw = movie_name
            query_clean = clean_baidu_query_title(movie_name)
            release_day = parse_release_date(row.get("上映时间", "") if hasattr(row, "get") else "")
            start_day, end_day = build_pre_release_window(release_day)

            if release_day is None or start_day is None or end_day is None:
                cache_payload = build_cache_payload(
                    subject_id,
                    movie_name,
                    query_raw,
                    query_clean,
                    None,
                    None,
                    None,
                    [],
                    "missing_release_date",
                    "上映日期缺失或无法解析",
                )
                write_json_atomically(cache_path, cache_payload)
                print(f"⏩ [{idx + 1}/{len(df)}] 上映日期缺失，已写入占位缓存：{movie_name}")
                missing_release_date_count += 1
                consecutive_limited = 0
                continue

            start_date = start_day.isoformat()
            end_date = end_day.isoformat()
            query_candidates = build_query_candidates(query_raw, query_clean)
            if is_unsupported_baidu_date_window(start_day, end_day):
                error_message = f"查询窗口早于百度指数最早支持日期 {config.BAIDU_INDEX_MIN_DATE}"
                cache_payload = build_cache_payload(
                    subject_id,
                    movie_name,
                    query_raw,
                    query_clean,
                    release_day,
                    start_day,
                    end_day,
                    [],
                    "unsupported_date_range",
                    error_message,
                )
                cache_payload["百度指数原始提取样本数"] = 0
                write_json_atomically(cache_path, cache_payload)
                unsupported_date_count += 1
                batch_outcomes.append("skip")
                consecutive_limited = 0
                print(f"⏩ [{idx + 1}/{len(df)}] 日期范围不支持，已写入占位缓存：{movie_name} - {error_message}")
                continue

            if real_request_count > 0 and real_request_count % config.BATCH_SIZE == 0:
                sleep_baidu_batch_pause()
            real_request_count += 1

            try:
                print(f"🔍 [{idx + 1}/{len(df)}] 正在抓取：{movie_name} | 查询词候选：{' -> '.join(query_candidates)}")
                used_query, raw_items, fetch_error = try_fetch_baidu_result(
                    fetcher,
                    query_candidates,
                    start_date,
                    end_date,
                )
                if raw_items is None:
                    raise fetch_error if fetch_error is not None else RuntimeError("百度指数请求未返回结果")

                filtered_raw_items = filter_baidu_raw_items(raw_items)
                extracted_items = collect_daily_items(filtered_raw_items)
                extracted_count = len(extracted_items)
                expected_dates = iter_date_strings(start_day, end_day)
                daily_values = normalize_daily_values(filtered_raw_items, start_day, end_day)
                result_type, result_reason = classify_baidu_result(
                    daily_values,
                    expected_dates=expected_dates,
                    extracted_count=extracted_count,
                )

                if result_type == "empty":
                    empty_count += 1
                    batch_outcomes.append("empty")
                    cache_payload = build_cache_payload(
                        subject_id,
                        movie_name,
                        query_raw,
                        used_query,
                        release_day,
                        start_day,
                        end_day,
                        [],
                        "empty_index",
                        result_reason,
                    )
                    cache_payload["百度指数原始提取样本数"] = extracted_count
                    write_json_atomically(cache_path, cache_payload)
                    print(f"⏩ [{idx + 1}/{len(df)}] 无可用指数样本，已写入占位缓存：{movie_name} - {result_reason} | 实际查询词：{used_query}")
                    consecutive_limited = 0
                elif result_type == "invalid":
                    fail_count += 1
                    batch_outcomes.append("error")
                    cache_payload = build_cache_payload(
                        subject_id,
                        movie_name,
                        query_raw,
                        used_query,
                        release_day,
                        start_day,
                        end_day,
                        daily_values,
                        "invalid",
                        result_reason,
                    )
                    cache_payload["百度指数原始提取样本数"] = extracted_count
                    write_json_atomically(cache_path, cache_payload)
                    print(f"❌ [{idx + 1}/{len(df)}] 数据无效：{movie_name} - {result_reason} | 实际查询词：{used_query}")
                    consecutive_limited = 0
                else:
                    cache_payload = build_cache_payload(
                        subject_id,
                        movie_name,
                        query_raw,
                        used_query,
                        release_day,
                        start_day,
                        end_day,
                        daily_values,
                        "ok",
                        "",
                    )
                    cache_payload["百度指数原始提取样本数"] = extracted_count
                    write_json_atomically(cache_path, cache_payload)

                    if daily_values and all(float(item.get("value", 0)) == 0 for item in daily_values):
                        zero_count += 1
                        batch_outcomes.append("zero")
                        success_count += 1
                        print(f"✅ [{idx + 1}/{len(df)}] 缓存成功（全0有效）：{movie_name} -> {cache_path.name} | 实际查询词：{used_query}")
                    else:
                        batch_outcomes.append("ok")
                        success_count += 1
                        print(f"✅ [{idx + 1}/{len(df)}] 缓存成功：{movie_name} -> {cache_path.name} | 实际查询词：{used_query}")
                    consecutive_limited = 0
            except Exception as exc:
                request_limited = is_request_limited_error(exc)
                status = (
                    "request_limited"
                    if request_limited
                    else ("bad_request" if is_bad_request_error(exc) else "cookie_or_api_error")
                )
                error_message = str(exc)[:300]
                cache_payload = build_cache_payload(
                    subject_id,
                    movie_name,
                    query_raw,
                    query_clean,
                    release_day,
                    start_day,
                    end_day,
                    [],
                    status,
                    error_message,
                )
                cache_payload["百度指数原始提取样本数"] = 0
                write_json_atomically(cache_path, cache_payload)
                if status == "bad_request":
                    bad_request_count += 1
                    batch_outcomes.append("bad_request")
                    print(f"⏩ [{idx + 1}/{len(df)}] 请求被拒绝，已写入诊断缓存：{movie_name} - {error_message}")
                    consecutive_limited = 0
                elif status == "request_limited":
                    fail_count += 1
                    request_limited_count += 1
                    consecutive_limited += 1
                    batch_outcomes.append("request_limited")
                    print(f"❌ [{idx + 1}/{len(df)}] 百度指数请求被限流：{movie_name} - {error_message[:120]}")

                    if consecutive_limited >= config.STOP_BLOCKED_THRESHOLD:
                        print("🛑 连续多次命中百度指数限流，建议更新 Cookie 或稍后再继续运行。")
                        break
                    if consecutive_limited >= config.BLOCKED_THRESHOLD:
                        sleep_baidu_block_pause()
                else:
                    fail_count += 1
                    batch_outcomes.append("error")
                    print(f"❌ [{idx + 1}/{len(df)}] 抓取失败：{movie_name} - {error_message[:120]}")
                    consecutive_limited = 0

            if batch_outcomes and len(batch_outcomes) % config.BATCH_SIZE == 0:
                evaluate_batch(batch_outcomes[-config.BATCH_SIZE:])

            sleep_baidu_delay()

        evaluate_batch(batch_outcomes[-config.BATCH_SIZE:])
        print(
            f"✅ {type_name} 完成：新增成功 {success_count} 部，已跳过 {skip_count} 部，失败 {fail_count} 部，"
            f"其中全 0 成功 {zero_count} 部，空样本 {empty_count} 部，"
            f"bad request {bad_request_count} 部，限流 {request_limited_count} 部，日期不支持 {unsupported_date_count} 部，"
            f"缺失上映日期 {missing_release_date_count} 部"
        )

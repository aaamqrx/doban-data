# 豆瓣电影爬虫项目

一个面向课程作业、项目展示和数据预处理场景的豆瓣电影采集项目。项目围绕“**中国地区电影（大陆 / 香港 / 台湾）**”构建了一套结构清晰、可重复执行的数据流水线：抓取豆瓣榜单、筛选中国地区电影、缓存详情页 HTML、缓存百度指数日值、解析生成特征，并最终输出结构化 Excel 数据集。

---

## 项目简介

当前流程共 **6 步**：

1. 抓取豆瓣分类榜单原始数据
2. 筛选中国地区电影（大陆 / 香港 / 台湾）
3. 下载电影详情页 HTML 到本地缓存
4. 抓取并缓存上映前 7 天百度指数日级数据
5. 解析百度指数缓存并生成中间特征表
6. 解析 HTML 并生成最终总表

项目采用 `config.py + src/分步脚本 + data/中间结果 + cache/缓存目录` 的结构，便于维护、调试、断点续跑和后续扩展。

---

## 项目特点

- **结构清晰**：配置、脚本、数据、缓存分目录组织
- **多类型支持**：按 [config.py](config.py) 中的 `MOVIE_TYPES` 批量抓取
- **评分区间完整遍历**：第 1 步自动遍历 `100:90` 到 `10:0`
- **HTML 支持断点续传**：第 3 步自动复用可用缓存
- **百度指数支持先缓存再解析**：第 4、5 步延续当前项目的缓存式工程模式
- **标题清洗可追溯**：百度缓存同时保留原始查询词和清洗后查询词
- **合并更准确**：最终汇总优先按 `subject_id` 合并，缺失时再按 `电影名` 兜底
- **适合后续分析 / 建模**：最终输出为结构化 Excel 数据表

---

## 项目目录结构

```text
movie_prediction_data/
│
├── config.py
├── requirements.txt
├── README.md
├── 项目说明.md
├── 快速说明.md
│
├── src/
│   ├── 1_get_raw_data.py
│   ├── 2_filter_china.py
│   ├── 3_save_html.py
│   ├── 4_save_baidu_index.py
│   ├── 5_parse_baidu_index.py
│   ├── 6_parse_html.py
│   ├── utils_dates.py
│   └── utils_baidu.py
│
├── data/
│   ├── raw/
│   ├── filtered/
│   ├── baidu/
│   └── final/
│
├── html_cache/
├── baidu_cache/
│
├── get_original_all.py
├── save_china_movie_html.py
└── parse_html_to_excel.py
```

---

## 核心流程说明

### Step 1. 抓取原始榜单数据
脚本：[src/1_get_raw_data.py](src/1_get_raw_data.py)

功能：
- 按类型请求豆瓣榜单接口
- 遍历评分区间 `100:90` 到 `10:0`
- 每个评分区间继续分页抓取
- 汇总所有结果后去重
- 输出到 `data/raw/*.xlsx`

原始输出字段包括：
- `subject_id`
- `电影名`
- `评分`
- `评价人数`
- `主演`
- `制片国家/地区`
- `类型`
- `上映时间`
- `详情链接`

### Step 2. 筛选中国地区电影
脚本：[src/2_filter_china.py](src/2_filter_china.py)

功能：
- 读取 `data/raw/*.xlsx`
- 根据 `制片国家/地区` 筛选中国地区电影（大陆 / 香港 / 台湾）
- 基于 `上映时间` 生成 `是否春节档 / 是否国庆档 / 是否五一档 / 是否暑期档 / 是否普通周末`
- 删除原始 `类型` 列，保留 `影片类型`
- 输出到 `data/filtered/china_*.xlsx`

### Step 3. 下载详情页 HTML
脚本：[src/3_save_html.py](src/3_save_html.py)

功能：
- 读取 `data/filtered/china_*.xlsx`
- 下载豆瓣详情页 HTML 并缓存到 `html_cache/<类型>/`
- 文件名优先使用 `subject_id_电影名.html`
- 自动跳过已下载文件，支持断点续传
- 拦截异常页、验证码页、登录页、禁止访问页等无效 HTML

### Step 4. 抓取并缓存百度指数
脚本：[src/4_save_baidu_index.py](src/4_save_baidu_index.py)

功能：
- 读取 `data/filtered/china_*.xlsx`
- 批量抓取前按 `config.py` 中的预检关键词与日期窗口请求一次；失败则退出，避免 Cookie 失效时写满失败缓存
- 上映前 7 天窗口早于 `BAIDU_INDEX_MIN_DATE` 时跳过请求，写入 `unsupported_date_range`（该日期为可配置的经验阈值，可按实测调整）
- 基于 `上映时间` 计算上映前 7 天窗口
- 查询词按「清洗后 → 原始片名」依次尝试；`qdata` 返回生成器时会在候选词循环内消费，保证回退生效
- 使用 `qdata` 拉取百度指数日级数据
- 将结果缓存到 `baidu_cache/<类型>/`
- 缓存中保留：原始查询词、清洗后查询词、日期窗口、日值列表、状态、错误信息、原始提取样本数等；失败类情况会写入 `empty_index`、`bad_request`、`cookie_or_api_error` 等诊断状态

### Step 5. 解析百度指数缓存
脚本：[src/5_parse_baidu_index.py](src/5_parse_baidu_index.py)

功能：
- 读取 `data/filtered/china_*.xlsx`，并为每行匹配 `baidu_cache/<类型>/` 下对应 JSON
- 生成 `上映前7天百度搜索指数均值`（仅当缓存状态为可用于建模时；`unsupported_date_range`、`empty_index`、`bad_request` 等终态下均值为空）
- 同时保留若干排障列：
  - `百度指数状态`
  - `百度指数错误信息`
  - `百度指数查询词原始`
  - `百度指数查询词清洗后`
  - `百度指数样本天数`
  - `百度指数非空天数`
- 输出到 `data/baidu/china_*.xlsx`

### Step 6. 解析 HTML 并合并最终结果
脚本：[src/6_parse_html.py](src/6_parse_html.py)

功能：
- 遍历 `html_cache/` 下全部 HTML 文件
- 解析 `电影名 / 导演 / 片长 / 剧情简介 / IMDb编号`
- 读取 `data/baidu/china_*.xlsx` 作为基础表
- 优先按 `subject_id` 合并，缺失时按 `电影名` 兜底
- 输出最终总表 `data/final/china_all.xlsx`

---

## 运行方法

建议按顺序执行：

```bash
python src/1_get_raw_data.py
python src/2_filter_china.py
python src/3_save_html.py
python src/4_save_baidu_index.py
python src/5_parse_baidu_index.py
python src/6_parse_html.py
```

如果是新环境，先执行：

```bash
pip install -r requirements.txt
```

---

## 输出结果

### 1. 原始数据目录 `data/raw/`
保存从豆瓣榜单接口抓取并汇总后的原始结构化数据。

### 2. 筛选结果目录 `data/filtered/`
保存中国地区电影筛选结果与档期布尔特征。

### 3. 百度特征目录 `data/baidu/`
保存加入百度指数均值与排障字段后的中间结果。

### 4. 最终总表目录 `data/final/`
最终总表：`data/final/china_all.xlsx`

### 5. HTML 缓存目录 `html_cache/`
按类型保存豆瓣详情页缓存。

### 6. 百度缓存目录 `baidu_cache/`
按类型保存每部电影的百度指数 JSON 缓存。

---

## 最终总表字段

`data/final/china_all.xlsx` 主要包含：

- `subject_id`
- `电影名`
- `评分`
- `评价人数`
- `主演`
- `制片国家/地区`
- `影片类型`
- `上映时间`
- `是否春节档`
- `是否国庆档`
- `是否五一档`
- `是否暑期档`
- `是否普通周末`
- `详情链接`
- `上映前7天百度搜索指数均值`
- `百度指数状态`
- `百度指数错误信息`
- `百度指数查询词原始`
- `百度指数查询词清洗后`
- `百度指数样本天数`
- `百度指数非空天数`
- `导演`
- `片长`
- `剧情简介`
- `IMDb编号`

---

## 配置说明

配置文件：[config.py](config.py)

可集中调整：
- 电影类型与 `type_id`
- 中国地区关键词（大陆 / 香港 / 台湾）
- 分页大小
- HTML 下载延时、批次暂停与风控退避阈值
- 百度指数 Cookie、`BAIDU_INDEX_MIN_DATE`、预检关键词与日期窗口、地区、重试与预警阈值
- 数据目录与缓存目录
- 豆瓣请求头与 Cookie

---

## 环境依赖

项目运行依赖：
- requests
- pandas
- openpyxl
- beautifulsoup4
- chinesecalendar
- qdata

安装命令：

```bash
pip install -r requirements.txt
```

如需手动安装，也可执行：

```bash
pip install requests pandas openpyxl beautifulsoup4 chinesecalendar qdata
```

---

## 使用注意事项

1. **Cookie 可能过期**  
   如果豆瓣或百度指数请求异常，优先检查 [config.py](config.py) 中对应站点的 Cookie。第 4 步开头有百度指数预检，预检失败时应先更新百度 Cookie 或检查网络与 `qdata`。

2. **榜单接口不是豆瓣全站电影库**  
   即使遍历全部评分区间，得到的数据仍然受豆瓣榜单接口返回范围限制。

3. **百度指数 0 值是有效信号**  
   第 5 步会把成功请求但 7 天全为 0 的记录标记为 `zero_valid`，这表示低热度而不是抓取失败。

4. **标题清洗会影响查询词**  
   第 4 步会优先截断副标题，缓存中会同时保留原始词和清洗后词，便于排查。

5. **运行时不要打开输出 Excel**  
   如果 `data/raw/`、`data/filtered/`、`data/baidu/` 或 `data/final/` 中的 Excel 文件正在被本地程序占用，写入可能失败。

6. **HTML 与百度指数步骤都可能较慢**  
   这是因为脚本包含随机延时、批次暂停和失败重试，用于降低风控风险。

7. **建议抽样检查最终结果**  
   建议至少抽样检查一两部电影，确认百度指数均值、导演、片长等字段都正常。

---

## 适用场景

本项目适用于：
- Python 课程作业
- 数据采集与预处理练习
- 电影数据分析项目
- 电影票房预测相关数据准备

---

## 总结

本项目已经从原本的单用途脚本集合，升级为一套结构清晰、流程明确、支持缓存重跑和特征扩展的豆瓣电影采集流程。它在原始抓取、中国地区筛选、HTML 缓存、百度指数缓存、特征解析和最终汇总等环节形成了完整闭环，适合作为后续分析和建模的数据准备基础。

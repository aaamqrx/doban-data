# 豆瓣电影爬虫项目

一个面向课程作业、项目展示和数据预处理场景的豆瓣电影采集项目。项目围绕“**中国地区电影（大陆 / 香港 / 台湾）**”构建了一套结构清晰、可重复执行的数据流水线，可按类型抓取榜单数据、筛选中国地区电影、下载详情页 HTML，并补充导演和片长等字段，最终生成结构化 Excel 数据集。

---

## 项目简介

本项目当前聚焦 3 个电影类型：

- 喜剧
- 动作
- 爱情

完整流程分为 4 步：

1. 抓取豆瓣分类榜单原始数据
2. 筛选中国地区电影（大陆 / 香港 / 台湾）
3. 下载电影详情页 HTML 到本地缓存
4. 解析 HTML 并生成最终总表

项目采用 `config.py + src/四步脚本 + data/html_cache` 的结构，便于维护、调试和扩展。

---

## 项目特点

- **结构清晰**：配置、脚本、数据、缓存分目录组织
- **多类型支持**：支持喜剧、动作、爱情三类电影抓取
- **评分区间完整遍历**：第 1 步会自动遍历 `100:90` 到 `10:0`
- **支持断点续传**：第 3 步遇到已下载 HTML 会自动跳过
- **HTML 命名更稳定**：优先使用 `subject_id_电影名.html`
- **合并更准确**：第 4 步优先按 `subject_id` 合并，可复用同一电影在多个类型中的 HTML 解析结果
- **适合后续分析**：最终输出为结构化 Excel 数据表

---

## 项目目录结构

```text
movie_prediction_data/
│
├── config.py
├── README.md
├── 项目说明.md
├── 快速说明.md
│
├── src/
│   ├── 1_get_raw_data.py
│   ├── 2_filter_china.py
│   ├── 3_save_html.py
│   └── 4_parse_html.py
│
├── data/
│   ├── raw/
│   ├── filtered/
│   └── final/
│
├── html_cache/
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
- 遍历评分区间：`100:90` 到 `10:0`
- 每个评分区间继续分页抓取
- 汇总所有结果后按 `详情链接` 去重
- 输出到 `data/raw/*.xlsx`

原始输出字段：

- `subject_id`
- 电影名
- `评分`
- `评价人数`
- 主演
- 制片国家/地区
- 类型
- 上映时间
- 详情链接

### Step 2. 筛选中国地区电影
脚本：[src/2_filter_china.py](src/2_filter_china.py)

功能：

- 读取 `data/raw/*.xlsx`
- 根据 `制片国家/地区` 筛选中国地区电影（大陆 / 香港 / 台湾）
- 基于 `上映时间` 生成 `是否春节档 / 是否国庆档 / 是否五一档 / 是否暑期档 / 是否普通周末`
- 采用 `chinesecalendar` + 向前侦测 3 天识别节前抢跑影片
- 增加 `影片类型` 列
- 删除原始 `类型` 列，避免语义重复
- 输出到 `data/filtered/china_*.xlsx`

### Step 3. 下载详情页 HTML
脚本：[src/3_save_html.py](src/3_save_html.py)

功能：

- 读取 `data/filtered/china_*.xlsx`
- 根据 `详情链接` 下载电影详情页
- 优先使用表内已有的 `subject_id`
- 仅在 `subject_id` 缺失时才从链接中兜底提取
- 缓存到 `html_cache/<类型>/`
- 文件名优先保存为 `subject_id_电影名.html`
- 自动跳过已下载文件，支持断点续传
- 拦截异常页、验证码页、登录页等无效 HTML
- 命中风控页时自动退避重试，并在连续拦截时长暂停或中止

### Step 4. 解析 HTML 并合并
脚本：[src/4_parse_html.py](src/4_parse_html.py)

功能：

- 遍历 `html_cache/` 下全部 HTML 文件
- 解析 `电影名`、`导演`、`片长`、`剧情简介`、`IMDb编号`
- 从 HTML 文件名中提取 `subject_id`
- 优先直接使用基础表已有的 `subject_id`
- 仅在 `subject_id` 缺失时从 `详情链接` 兜底提取
- 优先按 `subject_id` 合并，同一部电影可在多个类型中复用同一份 HTML 解析结果
- 输出最终总表 `data/final/china_all.xlsx`

---

## 运行方法

建议按顺序执行：

```bash
python src/1_get_raw_data.py
python src/2_filter_china.py
python src/3_save_html.py
python src/4_parse_html.py
```

---

## 输出结果

### 1. 原始数据目录 `data/raw/`
示例：

- `comedy.xlsx`
- `action.xlsx`
- `romance.xlsx`

### 2. 筛选结果目录 `data/filtered/`
示例：

- `china_comedy.xlsx`
- `china_action.xlsx`
- `china_romance.xlsx`

### 3. 最终总表目录 `data/final/`
示例：

- `china_all.xlsx`

### 4. HTML 缓存目录 `html_cache/`
示例：

- `html_cache/comedy/34950184_困兽.html`
- `html_cache/action/36193118_西游记之七十二变.html`

### 4. 最终总表字段
`china_all.xlsx` 主要包含：

- `subject_id`
- 电影名
- `评分`
- `评价人数`
- 主演
- 制片国家/地区
- 影片类型
- 上映时间
- `是否春节档`
- `是否国庆档`
- `是否五一档`
- `是否暑期档`
- `是否普通周末`
- 详情链接
- 导演
- 片长
- `剧情简介`
- `IMDb编号`

---

## 配置说明

配置文件：[config.py](config.py)

可集中调整：

- 电影类型与 `type_id`
- 中国地区关键词（大陆 / 香港 / 台湾）
- 分页大小
- 请求延时
- 批次暂停与风控退避阈值
- 数据目录
- 请求头与 Cookie

当前电影类型配置：

```python
MOVIE_TYPES = {
    "comedy": {"type_id": 24, "name": "喜剧"},
    "action": {"type_id": 5, "name": "动作"},
    "romance": {"type_id": 13, "name": "爱情"}
}
```

---

## 环境依赖

项目运行依赖：

- requests
- pandas
- openpyxl
- beautifulsoup4
- chinesecalendar

安装命令：

```bash
pip install -r requirements.txt
```

如果你只想手动安装，也可以执行：

```bash
pip install requests pandas openpyxl beautifulsoup4 chinesecalendar
```

---

## 使用注意事项

1. **Cookie 可能过期**  
   如果接口返回异常或 HTML 下载失败，优先检查 [config.py](config.py) 中的 Cookie。

2. **榜单接口不是豆瓣全站电影库**  
   当前项目基于豆瓣分类榜单接口抓取。即使遍历了全部评分区间，得到的数据仍然受该接口返回范围限制。

3. **中国地区筛选已包含大陆 / 香港 / 台湾**  
   第 2 步当前不再只保留大陆电影，而是会保留 `中国大陆`、`中国香港`、`中国台湾` 相关影片。

4. **运行时不要打开输出 Excel**  
   如果 `data/raw/`、`data/filtered/` 或 `data/final/` 中的 Excel 文件正在被本地程序占用，写入可能失败。

5. **HTML 下载耗时较长**  
   第 3 步包含随机延时、批次暂停和风控退避重试，耗时较长属于正常现象。

6. **出现“禁止访问”时的处理**  
   若连续出现风控拦截，脚本会自动长暂停；达到连续拦截阈值后会中止并提示更新 Cookie。

7. **建议抽样检查最终结果**  
   虽然第 4 步已优先按 `subject_id` 合并，但仍建议抽样检查 `导演`、`片长` 字段是否正常。

---

## 适用场景

本项目适用于：

- Python 课程作业
- 数据采集与预处理练习
- 电影数据分析项目
- 电影预测相关数据准备

---

## 后续可扩展方向

- 增加更多电影类型
- 将评分区间配置外置
- 增加失败重试机制
- 增加日志文件
- 增加评论数、评分、简介等字段
- 输出为 CSV 或数据库格式

---

## 总结

本项目已经从原本的 3 个单用途脚本，升级为一套结构清晰、流程明确、适合课程展示和后续分析的豆瓣电影采集流程。它在原始抓取、数据筛选、本地缓存、HTML 解析和结果合并等环节形成了完整闭环，适合作为数据分析、机器学习或电影预测任务的数据准备基础。
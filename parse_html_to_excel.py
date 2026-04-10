# -*- coding: utf-8 -*-
import os
import pandas as pd
from bs4 import BeautifulSoup

# ===================== 【配置区（完全适配你的文件，无需修改）】=====================
# 1. 你的HTML文件所在文件夹（截图中的 movie_html_china）
HTML_FOLDER = r"G:\DateAll\douban\movie_html_china"
# 2. 最终Excel的保存路径
EXCEL_SAVE_PATH = r"G:\DateAll\douban\douban_china_movies_final.xlsx"
# ==============================================================================

def extract_movie_info(html_file_path):
    """
    从单个HTML文件提取：电影名、导演、片长
    复用你之前100%成功的解析逻辑，精准提取不越界
    """
    try:
        # 读取本地HTML文件
        with open(html_file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # 1. 提取电影名（双重兜底：优先从title提取，失败则从h1提取）
        movie_name = ""
        # 方法1：从<title>标签提取（格式：「电影名 - 豆瓣电影」）
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            movie_name = title_text.replace(" - 豆瓣电影", "").strip()
        # 方法2：如果title提取失败，从<h1>标签提取（豆瓣电影页的主标题）
        if not movie_name:
            h1_tag = soup.find("h1")
            if h1_tag:
                movie_name = h1_tag.get_text(strip=True)
        # 兜底：用文件名（防止极端情况提取失败）
        if not movie_name:
            movie_name = os.path.basename(html_file_path).replace(".html", "")

        # 2. 提取导演（豆瓣标准属性rel="v:directedBy"，页面改版也稳定）
        director = "未提取到导演"
        director_elem = soup.find("a", attrs={"rel": "v:directedBy"})
        if director_elem:
            director = director_elem.get_text(strip=True)

        # 3. 提取片长（精准截断，绝对不提取「又名」等多余内容）
        runtime = "未提取到片长"
        runtime_span = soup.find("span", attrs={"property": "v:runtime"})
        if runtime_span:
            runtime = runtime_span.get_text(strip=True)
            # 遍历后续节点，遇到<br/>就停止，只取片长行内容
            next_node = runtime_span.next_sibling
            while next_node:
                if next_node.name == "br":
                    break
                if next_node.name is None:
                    text = next_node.strip()
                    if text:
                        runtime += text
                next_node = next_node.next_sibling

        return {
            "电影名": movie_name,
            "导演": director,
            "片长": runtime
        }

    except Exception as e:
        print(f"❌ 解析失败：{os.path.basename(html_file_path)}，错误：{str(e)[:80]}")
        return None

if __name__ == "__main__":
    # 1. 获取文件夹内所有HTML文件
    html_files = [f for f in os.listdir(HTML_FOLDER) if f.endswith(".html")]
    total_count = len(html_files)
    if total_count == 0:
        print("😥 未找到任何HTML文件，请检查文件夹路径！")
        exit()

    print(f"📂 找到 {total_count} 个HTML文件，开始批量解析...\n")

    # 2. 逐个解析并收集数据
    result_list = []
    for idx, file_name in enumerate(html_files, 1):
        file_path = os.path.join(HTML_FOLDER, file_name)
        print(f"🔍 正在解析 ({idx}/{total_count})：{file_name}")
        
        info = extract_movie_info(file_path)
        if info:
            result_list.append(info)

    # 3. 保存为Excel
    if result_list:
        df = pd.DataFrame(result_list)
        df.to_excel(EXCEL_SAVE_PATH, index=False)
        print(f"\n🎉 全部解析完成！")
        print(f"✅ 成功提取 {len(df)} 部电影数据")
        print(f"💾 最终Excel已保存至：{EXCEL_SAVE_PATH}")
    else:
        print("😥 未提取到任何有效数据，请检查HTML文件！")

# -*- coding: utf-8 -*-
import requests
import pandas as pd
import os
import time
import random

# ===================== 【完全适配你的文件&成功配置！】=====================
# 1. 你的Excel源文件路径（和截图完全一致，不用改）
EXCEL_PATH = r"G:\DateAll\douban\douban_comedy_china_all.xlsx"
# 2. 保存HTML的文件夹（自动创建，不用手动建）
HTML_SAVE_DIR = r"G:\DateAll\douban\movie_html_china"
# 3. 防反爬延时（秒，随机，越慢越稳，2000条建议3-5秒）
DELAY_MIN = 3
DELAY_MAX = 5

# 🔴 你单页成功的Chrome请求头（一字不改，完全复用）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# 🔴 【必须替换】你最新的有效Cookie（从浏览器复制，用你之前成功的那套，过期了重新换）
cookies = {
    "bid": "-HbToxAXYEg",
    "dbcl2": "\"278744232:iDZq1/Klc3M\"",
    "ck": "wIuf",
    "_gid": "GA1.2.2028851912.1775399891",
    "ll": "\"108288\"",
    "_ga": "GA1.2.517265896.1775399891",
    "_ga_Y4GN1R87RG": "GS2.1.s1775399890$o1$g1$t1775399950$j60$l0$h0",
    "frodotk_db": "\"a302e9531bf5cd19e908bbf953e1674b\"",
    "_pk_ref.100001.4cf6": "%5B%22%22%2C%22%22%2C1775399951%2C%22https%3A%2F%2Fm.douban.com%2F%22%5D",
    "_pk_id.100001.4cf6": "de767b894f38b6fe.1775399951.",
    "_pk_ses.100001.4cf6": "1",
    "__utma": "223695111.517265896.1775399891.1775399951.1775399951.1",
    "__utmc": "223695111",
    "__utmz": "223695111.1775399951.1.1.utmcsr=m.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/",
    "__utmb": "30149280.2.10.1775399951",
    "push_noty_num": "0",
    "push_doumail_num": "0",
    "_vwo_uuid_v2": "DCFB2FD361F013CFBCBA8C01B29481D68|c08168e531a4a44c9f15c9dba322afa1",
    "__utmt": "1",
    "__utmv": "30149280.27874",
    "__yadk_uid": "hN128i5wOZ3ceIJneFLnXIITMNyeNaaX"
}
# ==================================================================

def sanitize_filename(filename):
    """处理Windows文件名非法字符，避免保存失败（核心！）"""
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # 限制文件名长度，避免超长报错
    return filename[:100]

if __name__ == "__main__":
    # 1. 创建保存HTML的文件夹（如果不存在）
    if not os.path.exists(HTML_SAVE_DIR):
        os.makedirs(HTML_SAVE_DIR)
        print(f"✅ 已创建HTML保存文件夹：{HTML_SAVE_DIR}")

    # 2. 读取Excel源数据（和你的表格列名完全匹配：电影名、详情链接）
    print("📖 正在读取Excel源数据...")
    df = pd.read_excel(EXCEL_PATH, sheet_name="Sheet1")
    # 过滤空链接，避免程序崩溃
    df = df[df["详情链接"].notna()].reset_index(drop=True)
    movie_names = df["电影名"].tolist()
    movie_urls = df["详情链接"].tolist()
    total_count = len(movie_names)
    print(f"✅ 读取完成，共{total_count}部中国喜剧电影待保存源码\n")

    # 3. 批量请求+保存HTML（完全复用你成功的单页逻辑）
    success_count = 0
    fail_count = 0
    for idx, (name, url) in enumerate(zip(movie_names, movie_urls), 1):
        print(f"[{idx}/{total_count}] 🔍 正在请求：{name}")
        try:
            # 👇 这行代码和你单页成功的代码**完全一致**！
            response = requests.get(url, headers=headers, cookies=cookies, timeout=20)
            response.raise_for_status()  # 检查请求是否成功
            response.encoding = "utf-8"  # 彻底解决中文乱码

            # 处理文件名，保存为「电影名.html」
            safe_name = sanitize_filename(name)
            save_path = os.path.join(HTML_SAVE_DIR, f"{safe_name}.html")

            # 保存HTML源码到本地
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"   ✅ 保存成功！路径：{save_path}")
            success_count += 1

        except Exception as e:
            print(f"   ❌ 保存失败：{str(e)[:100]}")
            fail_count += 1

        # 随机延时，模拟真人浏览，彻底防反爬
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        print("-" * 60)

    # 4. 最终统计
    print(f"\n🎉 批量保存完成！")
    print(f"✅ 成功：{success_count} 部 | ❌ 失败：{fail_count} 部")
    print(f"📂 所有HTML文件已保存到：{HTML_SAVE_DIR}")
    print("💡 后续可直接用本地HTML批量提取导演/片长，彻底告别网络请求！")

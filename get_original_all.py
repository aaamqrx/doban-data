# -*- coding: utf-8 -*-
import requests
import pandas as pd
import time

# ===================== 【完全复用你成功的配置！】=====================
# 豆瓣分类榜单接口（一次性拉取700条，type=24对应喜剧分类
base_url = "https://movie.douban.com/j/chart/top_list?type=24&interval_id=10:0&action=&start=0&limit=700"

# 你单页成功的Chrome请求头（一字不改）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "https://movie.douban.com/chart",
    "Accept": "application/json, text/plain, */*"
}

# 【必须替换】你最新的有效Cookie（用你之前成功的那套，过期了重新复制）
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

# 保存路径（适配你之前的文件目录）
save_path = r"G:\DateAll\douban\douban_comedy10_700.xlsx"
# ==================================================================

# 1. 发送请求，获取JSON数据
print("🔍 正在请求豆瓣电影接口...")
response = requests.get(base_url, headers=headers, cookies=cookies, timeout=20)
response.encoding = "utf-8"

# 2. 校验请求状态
if response.status_code != 200:
    print(f"❌ 请求失败！状态码：{response.status_code}，请检查Cookie是否过期")
    exit()

# 3. 解析JSON数据
data = response.json()
print(f"✅ 成功获取{len(data)}条电影数据！")

# 4. 提取目标字段
movie_list = []
for item in data:
    # 列表转逗号分隔字符串，适配Excel存储
    title = item.get("title", "")
    actors = ",".join(item.get("actors", []))
    regions = ",".join(item.get("regions", []))
    types = ",".join(item.get("types", []))
    release_date = item.get("release_date", "")
    detail_url = item.get("url", "")

    movie_list.append({
        "电影名": title,
        "主演": actors,
        "制片国家/地区": regions,
        "类型": types,
        "上映时间": release_date,
        "详情链接": detail_url
    })

# 5. 保存为Excel
df = pd.DataFrame(movie_list)
df.to_excel(save_path, index=False)

print(f"\n🎉 700条电影数据爬取完成！")
print(f"✅ 数据已保存到：{save_path}")
print("📌 后续可直接用详情链接批量补导演/片长")

#!/usr/bin/env python3
"""
黄金三因子数据采集脚本
采集：美元指数、WTI油价、黄金价格、避险情绪指标、滞胀数据
"""
import json
import subprocess
import sys
from datetime import datetime

# JIN10_DB: Path to your Jin10 SQLite database (set this in your local config)

def query_jin10(sql, limit=20):
    """查询金十数据库"""
    try:
        result = subprocess.run(
            ["sqlite3", JIN10_DB, sql],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return [line.split("|") for line in result.stdout.strip().split("\n") if line]
        return []
    except Exception as e:
        print(f"Jin10 DB error: {e}", file=sys.stderr)
        return []

def fetch_gold_news(hours=24):
    """采集过去N小时的黄金相关快讯"""
    import sqlite3
    conn = sqlite3.connect(JIN10_DB)
    cur = conn.cursor()
    since = datetime.now().strftime("%Y-%m-%d %H:00:00")
    cur.execute(
        "SELECT time, content FROM news WHERE time >= ? AND important = 1 ORDER BY time DESC LIMIT 50",
        (since,)
    )
    rows = cur.fetchall()
    conn.close()
    
    keywords = ["黄金", "gold", "XAU", "美元", "美联储", "CPI", "油价", "EIA", 
                "央行", "购金", "地缘", "伊朗", "停火", "WTI", "布伦特", "实际利率",
                "通胀", "滞胀", "TIPS", "DXY", "纳斯达克", "标普"]
    
    results = []
    for time, content in rows:
        for kw in keywords:
            if kw.lower() in content.lower():
                results.append({"time": time, "content": content[:500]})
                break
    return results

def get_current_prices():
    """从 Yahoo Finance 抓取实时价格（备用）"""
    import urllib.request
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?range=1d&interval=1m"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return {"gold": price}
    except Exception as e:
        print(f"Price fetch error: {e}", file=sys.stderr)
        return {"gold": None}

def main():
    print("=== 黄金三因子数据采集 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 黄金相关新闻
    print("【1. 最新快讯（黄金相关）】")
    news = fetch_gold_news(hours=24)
    for item in news[:15]:
        print(f"  [{item['time']}] {item['content'][:200]}")
    print()
    
    # 2. 关键数据汇总（手动更新，需要实时数据时执行）
    print("【2. 当前市场数据】")
    print("  ⚠️ 请手动输入以下实时数据：")
    print("  - 美元指数 DXY：____（参考值：99-108）")
    print("  - WTI 原油：____美元/桶")
    print("  - 现货黄金：____美元/盎司")
    print("  - 10年期TIPS收益率：____%")
    print("  - CPI 最新值：____%")
    print("  - SPDR 黄金ETF持仓变化：____吨")
    print()

if __name__ == "__main__":
    main()

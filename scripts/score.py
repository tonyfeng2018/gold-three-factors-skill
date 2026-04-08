#!/usr/bin/env python3
"""
黄金三因子打分脚本 v2
更新：VIX熔断、地缘动量扣分、亚洲现货溢价、沃什听证会
用法：python3 score.py [dxy] [wti] [tips] [cpi] [geo_level] [cb_gold] [vix] [china_prem] [india_disc] [warsh_signal] [geo_momentum_hours]
例：python3 score.py 99.0 93.79 0.35 3.2 5 4 18 25 0 0 72
"""
import sys

def score_usd_real_rate(dxy, tips_yield, fed_signal=0, warsh_signal=0):
    """
    美元/实际利率因子（满分40）
    dxy: 美元指数 (e.g. 99.5)
    tips_yield: 10年期TIPS收益率 (e.g. 0.35)
    fed_signal: Fed政策信号 (-10到+10, 正=偏鸽/降息预期)
    warsh_signal: 沃什听证会信号 (-8到+8)
      -8~-5: 鹰派（紧缩+缩表）
      -4~-1: 偏鹰
       0:    无重大事件
      +1~+4: 偏鸽
      +5~+8: 鸽派（支持当前政策）
    """
    # DXY 评分
    if dxy > 108:
        dxy_score = 3
    elif dxy > 103:
        dxy_score = 10
    elif dxy > 99:
        dxy_score = 22
    else:
        dxy_score = 35

    # 实际利率评分
    if tips_yield > 2:
        tips_score = -8
    elif tips_yield > 1:
        tips_score = 0
    elif tips_yield > 0:
        tips_score = 5
    else:
        tips_score = 12

    total = dxy_score + tips_score + fed_signal + warsh_signal
    return max(0, min(40, total))

def score_risk_sentiment(geopolitical_level, vix, market_indicators=None, geo_momentum_hours=0):
    """
    避险情绪因子（满分15）⚠️ v2版本
    geopolitical_level: 0-15 (地缘冲突级别)
      0-2:  完全和平
      3-4:  停火达成但脆弱
      5-7:  停火谈判中/不确定
      8-11: 区域冲突持续
      12-15:大规模战争升级

    vix: VIX恐慌指数
      < 20: 0分（市场平静）
      20-30: +2~+4（适度恐慌，避险利好）
      30-35: +1~+2（恐慌加剧，上限）
      >= 35: -8~-12 🚨 熔断！流动性危机，margin call，无差别抛售

    geo_momentum_hours: 距离地缘降级的小时数
      若24-48小时内发生"战争→停火"降级，额外扣5-10分
      若<24小时发生降级，额外扣8-10分
    """
    # VIX 熔断 ⚠️ 优先级最高
    if vix < 20:
        vix_score = 0
        vix_alert = None
    elif vix < 30:
        vix_score = 3
        vix_alert = None
    elif vix < 35:
        vix_score = 2  # 上限，恐慌加剧但尚可控
        vix_alert = None
    else:
        vix_score = -10  # 🚨 熔断阈值
        vix_alert = f"🚨 VIX熔断触发({vix})！警惕无差别抛售，若金价同步下跌则进入防御模式"

    # 地缘基础分
    base = geopolitical_level

    # 地缘动量衰减扣分 ⚠️ 新增
    momentum_penalty = 0
    momentum_note = ""
    if geo_momentum_hours > 0 and geo_momentum_hours <= 48:
        if geopolitical_level <= 5:  # 已在停火谈判或更低
            if geo_momentum_hours <= 24:
                momentum_penalty = -10
                momentum_note = f"⚡ 24h内停火降级，踩踏风险极高"
            else:
                momentum_penalty = -7
                momentum_note = f"⚡ 48h内停火降级，额外扣7分"
        elif geopolitical_level <= 8:
            momentum_penalty = -5
            momentum_note = f"⚡ 48h内冲突降级，避险溢价快速消退"

    total = base + vix_score + momentum_penalty
    signal = max(0, min(15, total))

    return signal, {
        "vix_score": vix_score,
        "vix_alert": vix_alert,
        "momentum_penalty": momentum_penalty,
        "momentum_note": momentum_note,
    }

def score_stagflation(wti, cpi, tips_yield, cb_gold_signal, china_prem=0, india_disc=0, etf_change_tons=0):
    """
    滞胀逻辑因子（满分35）⚠️ v2版本
    wti: WTI原油价格 (美元/桶)
    cpi: 最新CPI年率 (%)
    tips_yield: 实际利率 (%)
    cb_gold_signal: 央行购金信号 (0-5)
    china_prem: 中国现货溢价 (美元/盎司，0=持平，>0=溢价)
    india_disc: 印度现货贴水 (美元/盎司，<0=贴水，0=持平)
    etf_change_tons: ETF持仓单日变化（吨）（辅助参考）
    """
    # CPI评分
    if cpi > 5:
        cpi_score = 30
    elif cpi > 3:
        cpi_score = 20
    elif cpi > 2:
        cpi_score = 12
    else:
        cpi_score = 5

    # 油价评分
    if wti > 120:
        oil_score = 9
    elif wti > 100:
        oil_score = 6
    elif wti > 80:
        oil_score = 2
    elif wti > 60:
        oil_score = 0
    else:
        oil_score = -4

    # 滞胀情景加成
    if cpi > 3 and tips_yield < 0.5:
        stagflation_bonus = 5  # 负实际利率 + 高通胀
    elif cpi > 4 and wti > 100:
        stagflation_bonus = 3
    else:
        stagflation_bonus = 0

    # ETF变化（辅助参考）
    if etf_change_tons > 20:
        etf_score = 3
    elif etf_change_tons > 5:
        etf_score = 2
    elif etf_change_tons < -10:
        etf_score = -3
    else:
        etf_score = 0

    # 亚洲现货溢价 ⚠️ 替代SPDR成为主要指标
    asian_score = 0
    asian_note = ""
    if china_prem > 30:
        asian_score = 6
        asian_note = f"中国现货溢价+${china_prem}/oz，强劲实物需求"
    elif china_prem > 10:
        asian_score = 3
        asian_note = f"中国现货溢价+${china_prem}/oz，实物支撑"
    elif china_prem > 0:
        asian_score = 1
        asian_note = f"中国现货溢价+${china_prem}/oz"

    if india_disc < -50:
        asian_score -= 4
        asian_note += f" | 印度贴水${india_disc}/oz，消费崩塌⚠️"
    elif india_disc < -20:
        asian_score -= 2
        asian_note += f" | 印度贴水${india_disc}/oz"
    elif india_disc < 0:
        asian_note += f" | 印度贴水${india_disc}/oz（轻微）"

    total = cpi_score + oil_score + stagflation_bonus + cb_gold_signal + etf_score + asian_score
    return max(0, min(35, total)), {
        "cpi_score": cpi_score,
        "oil_score": oil_score,
        "asian_score": asian_score,
        "asian_note": asian_note,
    }

def generate_report(usd_score, usd_detail, risk_score, risk_detail, stagflation_score, stagflation_detail, event_note="", extra_alerts=None):
    total = usd_score + risk_score + stagflation_score

    # VIX警报
    vix_alert = risk_detail.get("vix_alert") or (extra_alerts.get("vix_alert") if extra_alerts else None)
    momentum_note = risk_detail.get("momentum_note", "")

    if total >= 80:
        signal = "🚨 极强买入"
        action = "满仓/加仓，止损设在 +5%"
    elif total >= 72:
        signal = "✅ 买入"
        action = "买入，止损设在 -3%"
    elif total >= 60:
        signal = "⏸ 观望"
        action = "不追高，等回调或等触发事件"
    elif total >= 45:
        signal = "➖ 中性"
        action = "轻仓或空仓观望"
    elif total >= 30:
        signal = "⚠️ 谨慎"
        action = "低配或止损"
    else:
        signal = "🔴 卖出/回避"
        action = "清仓或做空"

    report_lines = [
        "【黄金三因子打分 v2】",
        "",
        f"美元/实际利率：{usd_score}分 /40",
        f"　　{usd_detail}",
        "",
        f"避险情绪：{risk_score}分 /15",
        f"　　VIX信号：{risk_detail.get('vix_score', 'N/A')}",
    ]

    if vix_alert:
        report_lines.append(f"　　{vix_alert}")
    if momentum_note:
        report_lines.append(f"　　{momentum_note}")

    report_lines.extend([
        "",
        f"滞胀逻辑：{stagflation_score}分 /35",
        f"　　{stagflation_detail}",
        "",
        f"总分：{total}分 → 【{signal}】",
        "",
        f"操作建议：{action}",
    ])

    if event_note:
        report_lines.append(f"\n⚠️ {event_note}")

    return "\n".join(report_lines)

def main():
    args = sys.argv[1:]

    if len(args) >= 10:
        dxy, wti, tips, cpi, geopolitical, cb_gold = map(float, args[:6])
        vix = float(args[6])
        china_prem = float(args[7]) if len(args) > 7 else 0
        india_disc = float(args[8]) if len(args) > 8 else 0
        warsh_signal = float(args[9]) if len(args) > 9 else 0
        geo_momentum_hours = float(args[10]) if len(args) > 10 else 0
        fed_signal = float(args[11]) if len(args) > 11 else 0
    else:
        print("用法: python3 score.py dxy wti tips cpi geo cb_gold vix [china_prem] [india_disc] [warsh] [geo_hours] [fed]")
        print()
        print("参数说明:")
        print("  dxy            美元指数 DXY (e.g. 99.5)")
        print("  wti            WTI原油价格 (美元/桶)")
        print("  tips           10年期TIPS收益率 (%)")
        print("  cpi            最新CPI年率 (%)")
        print("  geopolitical   地缘冲突级别 (0-15)")
        print("  cb_gold        央行购金信号 (0-5)")
        print("  vix            VIX恐慌指数 (>=35触发熔断!)")
        print("  china_prem     中国现货溢价 (美元/盎司，0=持平)")
        print("  india_disc     印度现货贴水 (美元/盎司，负值=贴水)")
        print("  warsh          沃什听证会信号 (-8~+8)")
        print("  geo_hours      地缘降级距今小时数 (0=无降级)")
        print("  fed            Fed政策信号 (-10~+10)")
        print()
        print("地缘冲突级别参考：")
        print("  0-2:  完全和平")
        print("  3-4:  停火达成但脆弱")
        print("  5-7:  停火谈判中")
        print("  8-11: 区域冲突持续")
        print("  12-15: 大规模战争升级")
        print()
        print("沃什听证会信号参考：")
        print("  -8~-5: 鹰派（主张紧缩+缩表）")
        print("  -4~-1: 偏鹰")
        print("   0:    无重大事件")
        print("  +1~+4: 偏鸽")
        print("  +5~+8: 鸽派（支持当前政策）")
        print()
        print("VIX熔断阈值：")
        print("  <20: 0分（平静）")
        print("  20-30: +3分（适度恐慌）")
        print("  30-35: +2分（上限）")
        print("  >=35: -10分 🚨 熔断！")
        print()
        print("例: python3 score.py 99.0 93.79 0.35 3.2 5 4 18 25 0 0 72 5")
        return

    usd = score_usd_real_rate(dxy, tips, fed_signal, warsh_signal)
    risk, risk_detail = score_risk_sentiment(geopolitical, vix, {}, geo_momentum_hours)
    stagflation, stagflation_detail = score_stagflation(wti, cpi, tips, cb_gold, china_prem, india_disc, 0)

    # Build details
    usd_detail = f"DXY={dxy} + TIPS={tips}% + Fed偏鸽信号={fed_signal} + 沃什={warsh_signal}"
    stagflation_detail_str = (f"CPI={cpi}%({stagflation_detail['cpi_score']}) + "
                              f"WTI=${wti}({stagflation_detail['oil_score']}) + "
                              f"亚洲溢价{stagflation_detail['asian_note'] or '基本持平'}")

    extra_alerts = {}
    if vix >= 35:
        extra_alerts["vix_alert"] = f"🚨 VIX熔断触发({vix})！流动性危机预警"

    event_note = "4月22日伊美停火谈判倒计时（当前处于停火期间，两周谈判中）"

    print(generate_report(usd, usd_detail, risk, risk_detail, stagflation, stagflation_detail_str, event_note, extra_alerts))
    print()
    print(f"详细：美元{usd}/40 + 避险{risk}/15 + 滞胀{stagflation}/35 = {usd+risk+stagflation}/90")

if __name__ == "__main__":
    main()

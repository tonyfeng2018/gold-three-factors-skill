#!/bin/bash
# 黄金三因子定时推送脚本 v2
# 直接执行脚本，输出结果，不依赖 agent

WORKSPACE="/Users/tonyclaw/.openclaw/workspace-clawffff"
SKILL_DIR="$WORKSPACE/skills/gold-three-factors"
JIN10_DIR="/Users/tonyclaw/.npm-global/lib/node_modules/openclaw/skills/jin10"
PYTHON3="/usr/bin/python3"

# 动态获取最新数据
# DXY
DXY=$(curl -s "https://query1.finance.yahoo.com/v8/finance/chart/UBT?interval=1d&range=1d" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"chart\"][\"result\"][0][\"meta\"][\"currency\"].lower()}')" 2>/dev/null || echo "98.8")

# 最新市场数据（停火期间，地缘降级）
# DXY=98.8, WTI=$108(停火后反弹), TIPS=0.35%, CPI=3.2%
# 地缘5（停火谈判中），VIX=18，央行4，中国溢价$28
DXY=98.8
WTI=108
TIPS=0.35
CPI=3.2
GEO=5
CB_GOLD=4
VIX=18
CHINA_PREM=28
INDIA_DISC=0
WARSH=0
GEO_HOURS=0
FED=5

RESULT=$($PYTHON3 "$SKILL_DIR/scripts/score.py" \
  $DXY $WTI $TIPS $CPI $GEO $CB_GOLD $VIX $CHINA_PREM $INDIA_DISC $WARSH $GEO_HOURS $FED \
  0 0 8 5 2>&1)

# 输出到文件
echo "$RESULT" > /tmp/gold-score-latest.txt

# 追加到历史
DATE=$(date "+%Y-%m-%d %H:%M")
echo "## $DATE" >> "$WORKSPACE/memory/gold-scores.md"
echo "$RESULT" >> "$WORKSPACE/memory/gold-scores.md"
echo "" >> "$WORKSPACE/memory/gold-scores.md"

echo "$RESULT"
echo ""
echo "✅ 已追加到 memory/gold-scores.md"

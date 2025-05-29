#!/bin/bash

# 起始日期
start_date="2025-04-01"

# 当前日期（今天）
end_date=$(date +"%Y-%m-%d")

# 转换为时间戳（秒）
current_date="$start_date"

while [ "$current_date" != "$end_date" ]; do
  echo "运行日期：$current_date"
  echo "准备运行关键命令"
  #read -p "按回车继续..." dummy
  python main.py --date "$current_date"

  # 计算下一天
  current_date=$(date -I -d "$current_date + 1 day")
done

# 最后跑一次今天
echo "运行日期：$end_date"
python main.py --date "$end_date"

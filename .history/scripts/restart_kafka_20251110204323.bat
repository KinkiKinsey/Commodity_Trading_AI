@echo off
echo 正在停止旧的 kafka_to_clickhouse 进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq kafka*" 2>nul

echo 等待 2 秒...
timeout /t 2 /nobreak >nul

echo 正在启动新的 kafka_to_clickhouse 进程...
cd /d D:\360MoveData\Users\juiceNo3\Desktop\ringshellV1\scripts
call conda activate ringshell
start "Kafka Consumer" python kafka_to_clickhouse.py --brokers localhost:9094 --ch-url http://localhost:18123

echo 启动完成！
pause
#!/bin/bash
echo "🚀 Jett's Insight 스케줄러를 백그라운드에서 시작합니다..."
nohup python3 github_auto_factory.py schedule > factory.log 2>&1 &
echo "✅ 실행 완료! 로그는 factory.log 파일에서 확인할 수 있습니다."
echo "✅ 봇 중지 방법: pkill -f 'python3 github_auto_factory.py'"

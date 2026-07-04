import os
import json
from google import genai
from telegram_notifier import send_telegram_message
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = "seo_audit.log"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def read_latest_audit():
    if not os.path.exists(LOG_FILE):
        return None
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Get the latest run (split by "=====")
    latest_run = []
    for line in reversed(lines):
        latest_run.insert(0, line.strip())
        if "QA 시작" in line:
            break
            
    if not latest_run:
        return None
        
    return "\n".join(latest_run)

def expert_panel_roi_decision(audit_text):
    print("🤖 [전문가 집단 ROI 판단 중...] 수정에 따른 득실을 계산합니다.")
    prompt = f"""
    당신은 블로그 검색엔진 최적화(SEO) 마스터이자 데이터 사이언티스트입니다.
    다음은 우리 블로그의 최신 QA 감사 로그입니다.

    [SEO Audit Log]
    {audit_text}

    이미 퍼블리싱된 글을 반복해서 수정하면 구글 샌드박스 패널티(순위 하락)를 받을 위험이 있습니다.
    로그에 나타난 에러(❌)나 경고(⚠️)를 분석하고, 
    "이 오류를 당장 수정함으로써 얻는 트래픽 이득이, 글 수정으로 인한 샌드박스 패널티 위험보다 큰가?"를 판단하세요.
    (예: 썸네일 이미지 링크가 404로 깨졌거나, 본문이 아예 비어있다면 즉시 수정해야 함. 하지만 단순히 H2 태그 1개가 부족하거나 본문이 약간 짧은 정도면 수정하지 말고 다음 글부터 주의해야 함.)

    다음 JSON 포맷으로 정확히 답변하세요.
    {{
        "should_modify": true 또는 false,
        "reasoning": "결정에 대한 전문가적이고 날카로운 이유 (3줄 이내)",
        "action_plan": "구체적인 수정 지침 또는 향후 포스팅 가이드"
    }}
    """
    
    from google.genai import types
    config = types.GenerateContentConfig(response_mime_type="application/json")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ 전문가 패널 응답 실패: {e}")
        return None

def run_fix_bot():
    print("=========================================")
    print("🛠️ Jett's Insight 자가 치유(Fix) 봇 가동")
    print("=========================================")
    
    audit_text = read_latest_audit()
    if not audit_text:
        print("⚠️ 분석할 SEO Audit 로그가 없습니다.")
        return
        
    if "❌" not in audit_text and "⚠️" not in audit_text:
        print("✅ 모든 SEO 항목이 완벽합니다. 수정할 필요가 없습니다.")
        return
        
    decision = expert_panel_roi_decision(audit_text)
    if decision:
        should_modify = decision.get("should_modify", False)
        reasoning = decision.get("reasoning", "")
        action_plan = decision.get("action_plan", "")
        
        msg = f"🔍 <b>[전문가 패널 SEO 진단 보고서]</b>\n\n"
        if should_modify:
            msg += "🚨 <b>치명적 오류 발견! 즉각 수정 권고</b>\n"
        else:
            msg += "🛡️ <b>경미한 오류: 수정 패널티 방어 (현상 유지 권고)</b>\n"
            
        msg += f"\n💡 <b>판단 이유:</b>\n{reasoning}\n\n"
        msg += f"📋 <b>액션 플랜:</b>\n{action_plan}"
        
        print(msg.replace("<b>", "").replace("</b>", ""))
        send_telegram_message(msg)
    
if __name__ == "__main__":
    run_fix_bot()

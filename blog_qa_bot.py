import requests
import xml.etree.ElementTree as ET
import datetime
from bs4 import BeautifulSoup
import os

LOG_FILE = "seo_audit.log"
SITEMAP_URL = "https://jett-1993.github.io/blog/sitemap.xml"
BLOG_URL = "https://jett-1993.github.io/blog/"

def log_audit(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    print(log_line.strip())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def check_sitemap():
    try:
        response = requests.get(SITEMAP_URL)
        if response.status_code == 200:
            log_audit("✅ [SITEMAP] sitemap.xml 정상 접근 확인")
            root = ET.fromstring(response.content)
            urls = [elem.text for elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
            
            # 필터링: /blog/trend/ 형식의 글만 추출 (카테고리/페이지 제외)
            post_urls = [u for u in urls if "/blog/trend/" in u]
            
            if post_urls:
                # GitHub Pages 사이트맵은 대개 알파벳순/시간순 정렬. 
                # 여기서는 테스트를 위해 첫 번째 글을 가져옴 (실제론 최신 글을 찾는 로직 필요)
                # sitemap.xml에는 <lastmod>가 있으므로 그걸 기준으로 최신 글을 찾습니다.
                
                latest_url = post_urls[-1] # 임시로 리스트의 마지막 요소
                latest_mod = ""
                for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc is not None and "/blog/trend/" in loc.text:
                        lastmod = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
                        if lastmod is not None and lastmod.text > latest_mod:
                            latest_mod = lastmod.text
                            latest_url = loc.text

                log_audit(f"✅ [SITEMAP] 최신 포스트 발견: {latest_url}")
                return latest_url
            else:
                log_audit("⚠️ [SITEMAP] 포스트 URL을 찾을 수 없습니다.")
                return None
        else:
            log_audit(f"❌ [SITEMAP] sitemap.xml 접근 실패 (HTTP {response.status_code}). 메인 페이지에서 최신 글을 탐색합니다.")
            
            # 메인 홈페이지에서 직접 크롤링 (Fallback)
            res = requests.get(BLOG_URL)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                # Jekyll minima 테마의 기본 포스트 링크 클래스 'post-link'
                first_post = soup.find('a', class_='post-link')
                if first_post and first_post.get('href'):
                    # href가 상대경로일 경우 절대경로로 조립
                    href = first_post.get('href')
                    if href.startswith('/'):
                        latest_url = "https://jett-1993.github.io" + href
                    else:
                        latest_url = BLOG_URL + href
                    log_audit(f"✅ [FALLBACK] 메인 페이지에서 최신 글 발견: {latest_url}")
                    return latest_url
            return None
    except Exception as e:
        log_audit(f"❌ [SITEMAP] 에러 발생: {e}")
        return None

def audit_post(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            log_audit(f"❌ [SEO_POST] 포스트 접근 실패: {url} (HTTP {response.status_code})")
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. 타이틀 검사
        title = soup.find('title')
        if title and len(title.text) > 0:
            log_audit(f"✅ [SEO_TITLE] 타이틀 존재: {title.text}")
        else:
            log_audit(f"❌ [SEO_TITLE] 타이틀 태그 누락")

        # 2. 메타 디스크립션 검사
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            log_audit("✅ [SEO_META] Meta Description 존재")
        else:
            log_audit("❌ [SEO_META] Meta Description 누락")

        # 3. 모바일 Viewport 검사
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            log_audit("✅ [SEO_MOBILE] Viewport 설정 확인 (모바일 친화적)")
        else:
            log_audit("❌ [SEO_MOBILE] Viewport 누락")

        # 4. 본문 글자수 검사
        article_body = soup.find('div', class_='post-content') # Jekyll 기본 클래스
        if article_body:
            text_length = len(article_body.get_text(strip=True))
            if text_length >= 1000:
                log_audit(f"✅ [SEO_CONTENT] 본문 길이 양호 ({text_length}자)")
            else:
                log_audit(f"⚠️ [SEO_CONTENT] 본문 길이가 다소 짧음 ({text_length}자) - 애드센스 승인/체류시간 악영향 우려")
        else:
            log_audit("❌ [SEO_CONTENT] 본문 영역(.post-content)을 찾을 수 없음")

        # 5. 헤딩(H2, H3) 구조 및 이미지 ALT 태그
        h2_tags = soup.find_all('h2')
        if len(h2_tags) > 0:
            log_audit(f"✅ [SEO_HEADING] H2 태그 {len(h2_tags)}개 확인")
        else:
            log_audit("⚠️ [SEO_HEADING] H2 태그가 없습니다. 가독성 및 SEO 감점 우려")

        images = soup.find_all('img')
        missing_alt = [img for img in images if not img.get('alt')]
        if len(missing_alt) == 0:
            log_audit("✅ [SEO_IMAGE] 모든 이미지에 ALT 태그 적용 완료")
        else:
            log_audit(f"❌ [SEO_IMAGE] ALT 태그 누락 이미지 발견 ({len(missing_alt)}개)")

    except Exception as e:
        log_audit(f"❌ [SEO_POST] 오딧 중 에러 발생: {e}")

def run_qa():
    log_audit("=========================================")
    log_audit("🔍 Jett's Insight 블로그 SEO QA 시작")
    log_audit("=========================================")
    latest_url = check_sitemap()
    if latest_url:
        audit_post(latest_url)
    log_audit("✅ QA 검사 완료\n")
    
    # QA 종료 후 즉시 Fix 봇 가동하여 ROI 판단
    from blog_fix_bot import run_fix_bot
    run_fix_bot()

if __name__ == "__main__":
    run_qa()

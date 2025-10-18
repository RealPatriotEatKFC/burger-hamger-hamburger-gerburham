from huggingface_hub import InferenceClient
import sys
import requests
from bs4 import BeautifulSoup
import json

# Hugging Face Access Token
TOKEN = "insert_ur_hugging_face_access_token"

def search_burger_info(keyword):
    """검색을 통해 햄버거 정보 수집"""
    try:
        # 검색어 생성
        search_query = f"{keyword} 햄버거 추천 맘스터치 롯데리아 맥도날드 버거킹"
        url = f"https://search.naver.com/search.naver?query={requests.utils.quote(search_query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 검색 결과에서 텍스트 추출
        results = []
        for item in soup.select('.total_wrap, .api_txt_lines'):
            text = item.get_text(strip=True)
            if text and len(text) > 20:
                results.append(text)
                if len(results) >= 3:
                    break
        
        return "\n".join(results) if results else None
        
    except Exception as e:
        print(f"검색 오류: {str(e)}")
        return None

def get_franchise_menus():
    """주요 프랜차이즈 메뉴 데이터베이스"""
    menus = {
        "맘스터치": ["싸이버거", "언빌리버블버거", "화이트갈릭버거", "딥치즈버거", "싸이플렉스버거"],
        "롯데리아": ["불고기버거", "새우버거", "치킨버거", "리아버거", "한우불고기버거"],
        "맥도날드": ["빅맥", "상하이버거", "맥스파이시", "쿼터파운더치즈", "더블불고기버거"],
        "버거킹": ["와퍼", "통새우와퍼", "몬스터와퍼", "치즈와퍼", "콰트로치즈와퍼"],
        "KFC": ["징거버거", "업그레이비버거", "징거타워버거" ,"징거더블다운", "징거BLT버거", "커넬데리야끼버거", "칠리징거통다리버거", "클래식징거통다리버거", "치즈징거통다리버거"],
        "노브랜드버거": ["통새우버거", "더블엑스버거", "치즈버거"]
    }
    return menus

def recommend_burger(preference):
    """햄버거 추천 함수 - 실제 메뉴 기반"""
    try:
        # 1. 인터넷 검색으로 최신 정보 수집
        print("   📡 인터넷에서 정보 검색 중...")
        search_results = search_burger_info(preference)
        
        # 2. 프랜차이즈 메뉴 데이터 가져오기
        menus = get_franchise_menus()
        menu_list = []
        for franchise, items in menus.items():
            for item in items:
                menu_list.append(f"{franchise} - {item}")
        
        # 3. AI에게 프롬프트 전달
        client = InferenceClient(token=TOKEN)
        
        prompt = f"""당신은 한국의 햄버거 프랜차이즈 전문가입니다.

사용자 키워드: {preference}

다음은 실제 존재하는 한국 햄버거 프랜차이즈 메뉴 목록입니다:
{chr(10).join(menu_list[:30])}

{"인터넷 검색 결과:" + chr(10) + search_results[:500] if search_results else ""}

위 실제 메뉴 중에서 '{preference}' 키워드에 가장 적합한 햄버거를 1-2개 추천해주세요.
반드시 위 목록에 있는 실제 메뉴만 추천하고, 다음 형식으로 답변하세요:

추천: [프랜차이즈명] - [메뉴명]
이유: [1-2문장으로 키워드와 어울리는 이유 설명]

절대 목록에 없는 메뉴는 추천하지 마세요."""

        messages = [{"role": "user", "content": prompt}]
        
        response = client.chat_completion(
            messages=messages,
            model="google/gemma-2-2b-it",
            max_tokens=200,
            temperature=0.5
        )
        
        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            # AI 응답 실패시 간단한 매칭 알고리즘 사용
            return simple_menu_match(preference, menus)
            
    except Exception as e:
        # 오류 발생시 간단한 매칭 알고리즘으로 대체
        return simple_menu_match(preference, get_franchise_menus())

def simple_menu_match(keyword, menus):
    """간단한 키워드 매칭 알고리즘 (백업용)"""
    keyword = keyword.lower()
    
    # 키워드별 추천 로직
    recommendations = []
    
    for franchise, items in menus.items():
        for item in items:
            item_lower = item.lower()
            # 키워드 매칭
            if (keyword in item_lower or 
                ("매운" in keyword and ("싸이" in item or "스파이시" in item)) or
                ("치즈" in keyword and "치즈" in item) or
                ("새우" in keyword and "새우" in item) or
                ("불고기" in keyword and "불고기" in item) or
                ("치킨" in keyword and "치킨" in item)):
                recommendations.append(f"추천: {franchise} - {item}")
    
    if recommendations:
        return recommendations[0] + "\n이유: 키워드와 메뉴명이 일치합니다."
    else:
        return "추천: 맘스터치 - 싸이버거\n이유: 한국에서 가장 인기있는 메뉴입니다."

def main():
    """메인 챗봇 함수"""
    print("=" * 60)
    print("🍔 한국 햄버거 프랜차이즈 추천 챗봇 (실제 메뉴 기반) 🍔")
    print("=" * 60)
    
    if TOKEN == "hf_너의토큰여기붙여":
        print("\n⚠️  경고: Hugging Face 토큰을 설정해주세요!")
        print("코드의 TOKEN 변수에 실제 토큰을 입력하세요.")
        print("(토큰 없이도 기본 추천 기능은 작동합니다)\n")
    
    print("💡 팁: '매운맛', '치즈', '새우', '불고기' 등의 키워드 입력")
    print("종료하려면 'quit', 'exit', 'q' 를 입력하세요.\n")
    
    while True:
        try:
            user_input = input("🔍 원하는 햄버거 스타일이나 키워드를 입력하세요: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q', '종료', '나가기']:
                print("\n👋 챗봇을 종료합니다. 맛있는 햄버거 드세요!")
                break
            
            if not user_input:
                print("⚠️  키워드를 입력해주세요!\n")
                continue
            
            print("\n💭 실제 메뉴를 찾는 중입니다...")
            recommendation = recommend_burger(user_input)
            
            print("-" * 60)
            print("🍔 추천 결과 (실제 메뉴):")
            print("-" * 60)
            print(recommendation)
            print("-" * 60)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 챗봇을 종료합니다. 맛있는 햄버거 드세요!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 오류: {str(e)}\n")

if __name__ == "__main__":

    main()

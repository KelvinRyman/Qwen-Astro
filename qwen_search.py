import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# --- 1. 設定區：請將您申請的key填寫在這裡 ---


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyBTyArZ1qVZNVl12pIeDRiaMx3mkY-fGcM") 
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID", "30e35e58d395e4cfd")  # 您的 Google Custom Search Engine ID

# Ollama API 的位址和模型名稱
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:0.6b" 

# --- 2. 核心功能函式 ---
# Google_Search 函式用於使用 Google Search API 進行搜尋，並返回結果的網址列表。网页数量默认为10。 
def Google_Search(query: str, num_results: int = 10) -> list:
    """
    使用 Google Search API 進行搜尋。
    :param query: 搜尋的關鍵字。
    :param num_results: 需要返回的搜尋結果數量。
    :return: 包含網址的列表。
    """
    print(f"🔍 正在使用 Google 搜尋: {query}")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
        'num': num_results
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 如果請求失敗則拋出異常
        search_results = response.json()
        urls = [item['link'] for item in search_results.get('items', [])]
        print(f"✅ 成功獲取到 {len(urls)} 個搜尋結果。")
        return urls
    except Exception as e:
        print(f"❌ Google 搜尋失敗: {e}")
        return []

# Scrape_website_content 函式用於爬取指定網址的網頁文本內容，並返回純文本。這裡使用 BeautifulSoup 來解析 HTML。
def scrape_website_content(url: str) -> str:
    """
    爬取指定网址的网页文本内容，添加编码处理以避免中文乱码。
    :param url: 要爬取的网址。
    :return: 网页的纯文本内容，如果失败则返回空字串。
    """
    print(f"🕸️ 正在爬取網頁: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 尝试检测编码并正确设置
        if response.encoding.lower() == 'iso-8859-1':
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
            for enc in encodings:
                try:
                    response.encoding = enc
                    if '�' not in response.text and '锛' not in response.text:
                        break
                except:
                    continue
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除脚本、样式和其他非内容标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # 提取并清理文本，简化处理
        text = soup.body.get_text(separator=' ') if soup.body else soup.get_text(separator=' ')
        text = ' '.join(text.split())  # 替换所有连续空白字符为单个空格
        
        content_length = len(text)
        max_length = 3000  # 提高到5000字符，获取更多上下文
        print(text[:max_length])  # 输出前3000字符以供调试
        print(f"✅ 成功爬取网页内容，长度: {content_length} 字符，截取了前 {min(content_length, max_length)} 字符。")
        return text[:max_length]
    except Exception as e:
        print(f"❌ 爬取網頁失敗: {e}")
        return ""

def ask_qwen_with_context(question: str, context: str) -> str:
    """
    將問題和上下文提交給本地的 Qwen 模型進行分析和回答。
    :param question: 使用者的原始問題。
    :param context: 從網路上檢索到的參考資料。
    :return: Qwen 模型生成的回應。
    """
    print("🧠 正在呼叫 Qwen3 模型進行分析和回答...")
    
    today = datetime.now().strftime("%Y-%m-%d")
    # 這是一個關鍵的 Prompt Template，引導模型根據上下文回答
    prompt = f"""
請你扮演一個專業的資訊分析師。
今天的日期是：{today}
根據下面提供的「網路搜尋參考資料」，簡潔、準確地回答使用者的問題。
請不要使用參考資料以外的資訊。如果資料不足以回答，請誠實地說「根據現有資料，我無法回答這個問題」。

---
[網路搜尋參考資料]
{context}
---

[使用者的問題]
{question}

[你的回答]
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        response_data = response.json()
        print("✅ Qwen3 模型回答完畢。")
        return response_data.get('response', '模型沒有返回有效的回答。')
    except Exception as e:
        print(f"❌ 呼叫 Qwen3 模型失敗: {e}")
        return "無法連接到本地的 Qwen 模型。"

# --- 3. 主執行流程 ---
def main():
    user_question = input("您好！請輸入您想查詢的問題：")
    
    # 步驟一：搜尋
    search_urls = Google_Search(user_question)
    
    if not search_urls:
        print("無法獲取搜尋結果，程式終止。")
        return
        
    # 步驟二和三：抓取和整合
    all_context = ""
    count = 0
    # 限制抓取的網頁數量，最多3個
    for url in search_urls:
        if count >= 3:
            break
        content = scrape_website_content(url)
        if content:
            all_context += f"[來源: {url}]\n{content}\n\n---\n\n"
            count += 1
    if not all_context:
        print("無法從任何網頁上抓取到有效內容，程式終止。")
        return
        
    # 步驟四：生成
    final_answer = ask_qwen_with_context(user_question, all_context)
    
    print("\n==================== 最終答案 ====================\n")
    print(final_answer)
    print("\n==================================================")

if __name__ == "__main__":
    main()
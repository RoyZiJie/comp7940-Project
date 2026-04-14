import os
import re
import requests
import PyPDF2
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# ====================== Global Configuration ======================
# HKBU GenAI Platform Configuration
API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://genai.hkbu.edu.hk/api/v0/rest")
MODEL = os.getenv("MODEL", "gpt-5")
API_VERSION = os.getenv("API_VERSION", "2024-12-01-preview")

# SerpAPI Configuration (for web search)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
STORAGE_DIR = "./storage"
DATA_DIR = "./data"


# ====================== Web Search Function ======================
def search_web(query: str, max_results: int = 3) -> str:
    """Search the web using SerpAPI Google Search"""
    if not SERPAPI_KEY:
        return None

    try:
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "num": max_results
        }

        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            results = []

            for item in data.get("organic_results", [])[:max_results]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")

                if snippet:
                    results.append(f"**{title}**\n{snippet}\nSource: {link}")

            if results:
                return "🌐 **Internet Search Results:**\n\n" + "\n\n---\n\n".join(results)

        return None

    except Exception as e:
        print(f"Web search failed: {e}")
        return None


# ====================== Document Loading & Chunking ======================
def load_all_documents(data_dir: str = DATA_DIR):
    """Load all txt and pdf files from the data directory"""
    documents = []
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"📁 Created data directory: {data_dir}")
        print("⚠️ Please put HKBU related documents (.txt or .pdf) into data/ folder")
        return documents

    # Read all files
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)

        # Read .txt files
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    "file_name": filename,
                    "content": content
                })
                print(f"📄 Loaded document: {filename} ({len(content)} characters)")

        # Read .pdf files
        elif filename.endswith('.pdf'):
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    content = ''
                    for page in reader.pages:
                        content += page.extract_text()
                    if content.strip():
                        documents.append({
                            "file_name": filename,
                            "content": content
                        })
                        print(f"📄 Loaded PDF: {filename} ({len(content)} characters)")
                    else:
                        print(f"⚠️ No text extracted from PDF: {filename} (may be scanned)")
            except Exception as e:
                print(f"❌ Error reading PDF {filename}: {e}")

    return documents


def chunk_documents(documents: List, chunk_size: int = CHUNK_SIZE):
    """Split long documents into smaller chunks"""
    nodes = []
    for doc in documents:
        content = doc["content"]
        # Split by chunk_size
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            if chunk.strip():
                nodes.append({
                    "file_name": doc["file_name"],
                    "content": chunk
                })
    print(f"✅ Loaded {len(documents)} documents → {len(nodes)} chunks")
    return nodes


# Load documents and create chunks
documents = load_all_documents(DATA_DIR)
nodes = chunk_documents(documents)


# ====================== Keyword Retrieval with Course Code Extraction ======================
def extract_course_codes(text: str) -> List[str]:
    """Extract course codes like COMP7430, COMP 7430, COMP-7430 from text"""
    course_codes = []
    patterns = [
        r'COMP\s*(\d{4})',
        r'COMP[-_]\s*(\d{4})',
        r'comp\s*(\d{4})',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            course_codes.append(f"COMP{match}")
            course_codes.append(f"comp{match}")
            course_codes.append(f"COMP-{match}")
            course_codes.append(f"COMP {match}")
    return list(set(course_codes))


def extract_professor_keywords(text: str) -> List[str]:
    """Extract professor-related keywords from query"""
    keywords = []
    text_lower = text.lower()

    professor_patterns = [
        r'who\s+is\s+teaching',
        r'who\s+teaches',
        r'instructor',
        r'professor',
        r'prof\.',
        r'dr\.',
        r'teaching\s+staff',
        r'faculty'
    ]

    for pattern in professor_patterns:
        if re.search(pattern, text_lower):
            keywords.append('professor')
            keywords.append('instructor')
            keywords.append('teaching staff')

    return list(set(keywords))


def retrieve_context(
        nodes: List,
        query: str,
        method: str = "keyword",
        top_k: int = 5,
        use_web_search: bool = True
) -> List[Dict]:
    """Retrieve relevant document chunks - combines local + web search results"""
    results = []

    # 1. Try to get results from local documents
    if nodes:
        course_codes = extract_course_codes(query)
        professor_keywords = extract_professor_keywords(query)
        query_words = set(query.lower().split())

        for code in course_codes:
            query_words.add(code.lower())
            num_match = re.search(r'(\d{4})', code)
            if num_match:
                query_words.add(num_match.group(1))

        for kw in professor_keywords:
            query_words.add(kw)

        stop_words = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "也", "都", "说",
                      "a", "an", "the", "is", "are", "was", "were", "to", "of", "and", "or",
                      "in", "on", "at", "for", "with", "by", "tell", "me", "more", "about",
                      "what", "can", "you", "please", "course", "courses"}
        query_words = query_words - stop_words

        if query_words:
            scored_nodes = []
            for node in nodes:
                content_lower = node["content"].lower()
                score = 0
                for word in query_words:
                    if word in content_lower:
                        score += 1
                if score > 0:
                    scored_nodes.append((score, node))

            scored_nodes.sort(key=lambda x: x[0], reverse=True)
            local_results = [node for score, node in scored_nodes[:top_k]]

            if local_results:
                results.extend(local_results)
                print(f"📚 Retrieved {len(local_results)} relevant chunks from local documents")

    # 2. Also try web search (even if local results found)
    if use_web_search and SERPAPI_KEY:
        print(f"🌐 Also fetching web search results for: {query}")
        web_results = search_web(query)
        if web_results:
            results.append({
                "file_name": "Internet Search",
                "content": web_results
            })
            print(f"🌐 Added web search results")

    return results


# ====================== Prompt Generation ======================
def generate_prompt(context: str, history: str, query: str, use_cot: bool = True) -> str:
    """Generate the prompt to send to LLM"""
    cot_instruction = ""
    if use_cot:
        cot_instruction = """
First, show your thinking process inside <Thought> tags.
Then give your final answer inside <Answer> tags.
Keep your answer clear and concise.
"""

    return f"""You are a helpful HKBU study assistant. Answer based on the context below.

Context:
{context}

Conversation History:
{history}

User: {query}

{cot_instruction}

Assistant:"""


# ====================== Query Rewriting ======================
def rewrite_query(query: str, history: str):
    """Rewrite query to be standalone based on conversation history"""
    if not history.strip():
        return query, {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    prompt = f"""Rewrite this question into a standalone question based on history.
History: {history}
Question: {query}
Standalone Question:"""

    res = complete_document_sdk(prompt=prompt, temperature=1.0)
    rewritten = res["response"].strip()
    rewritten = rewritten.split('\n')[0] if '\n' in rewritten else rewritten
    return rewritten if rewritten else query, res


# ====================== HKBU GenAI Platform API Call ======================
def complete_document_sdk(
        prompt: str,
        model: str = None,
        num_predict: int = 2048,
        temperature: float = 1.0,
        stop_sequences: List[str] = None,
        stream_callback=None
) -> Dict[str, Any]:
    """Call HKBU GenAI Platform API (GPT-5) using Azure OpenAI format"""

    if not API_KEY:
        return {
            "response": "Error: API_KEY not set in .env file. Please add your API key.",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    model_name = model or MODEL

    url = f"{API_BASE_URL}/deployments/{model_name}/chat/completions?api-version={API_VERSION}"

    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "messages": [
            {"role": "system",
             "content": "You are a helpful HKBU study assistant. Answer based on the provided context."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": num_predict,
        "stream": False
    }

    if stop_sequences:
        data["stop"] = stop_sequences

    try:
        print(f"📡 Calling API: {model_name}")
        print(f"📡 URL: {url}")
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
            else:
                content = str(result)

            usage = result.get("usage", {})

            if stream_callback:
                stream_callback(content)

            print(f"✅ API call successful (tokens: {usage.get('total_tokens', 0)})")

            return {
                "response": content,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        else:
            error_msg = f"API Error: {response.status_code} - {response.text[:200]}"
            print(f"❌ {error_msg}")
            return {
                "response": f"Sorry, there was an API error. Please try again later.",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

    except requests.exceptions.Timeout:
        error_msg = "Request Timeout: API took too long to respond"
        print(f"❌ {error_msg}")
        return {
            "response": "Sorry, the request timed out. Please try again.",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    except Exception as e:
        error_msg = f"Request Error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "response": f"Sorry, an error occurred: {str(e)}",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }


# ====================== Conversation History Management ======================
class ConversationManager:
    """Manage conversation history"""

    def __init__(self):
        self.history = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_history_string(self, max_turns: int = 4):
        recent = self.history[-max_turns * 2:]
        return "\n".join([f"{item['role']}: {item['content']}" for item in recent])

    def clear_history(self):
        self.history = []
        print("🧹 Conversation history cleared")


# ====================== Greeting Detection ======================
def is_greeting(query: str) -> bool:
    q = query.strip().lower()
    greetings = {
        "hi", "hello", "hey", "hi!", "hello!", "hey!",
        "haha", "good morning", "good afternoon", "good evening",
        "how are you", "what's up", "sup", "greetings"
    }
    return q in greetings or any(g in q for g in greetings)


# ====================== Answer Extraction ======================
def extract_answer(response_text: str) -> str:
    import re
    pattern = r"<Answer>\s*(.*?)(?:</Answer>|$)"
    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    pattern2 = r"Answer:\s*(.*?)(?:\n\n|$)"
    match2 = re.search(pattern2, response_text, re.DOTALL | re.IGNORECASE)
    if match2:
        return match2.group(1).strip()

    return response_text.strip()


# ====================== Test Entry Point ======================
if __name__ == "__main__":
    print("=" * 50)
    print("RAG Engine Test")
    print("=" * 50)

    print("\n📡 Testing API connection...")
    test_response = complete_document_sdk(prompt="Say 'Hello, HKBU!'", temperature=1.0)

    if test_response.get("response") and "Error" not in test_response["response"]:
        print(f"\n✅ API test successful!")
        print(f"Response: {test_response['response'][:100]}...")
        print(f"Token usage: {test_response.get('total_tokens', 0)}")
    else:
        print(f"\n❌ API test failed: {test_response.get('response')}")
        print("\nPlease check:")
        print("1. API_KEY in .env file is correct")
        print("2. API_BASE_URL is correct")
        print("3. Network can access school API")

    print(f"\n📚 Loaded {len(documents)} documents, {len(nodes)} chunks")
import os
from typing import List, Dict, Any
import ollama
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings

# ====================== 全局配置 ======================
LLM_MODEL = "gemma3:4b"
EMBED_MODEL = "embeddinggemma"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
STORAGE_DIR = "./storage"
DATA_DIR = "./data"

#全局使用 Ollama 本地嵌入
Settings.embed_model = OllamaEmbedding(model_name=EMBED_MODEL)

# ====================== 文档加载与分块 ======================
def load_all_documents(data_dir: str = DATA_DIR) -> List:
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    print("📂 Loading documents...")
    documents = SimpleDirectoryReader(data_dir).load_data()
    return documents

def chunk_documents(documents: List) -> List:
    parser = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = parser.get_nodes_from_documents(documents)
    print(f"✅ Parsed {len(documents)} docs → {len(nodes)} chunks. Launching GUI...")
    return nodes

documents = SimpleDirectoryReader("data", recursive=True).load_data()
nodes = chunk_documents(documents)

# ====================== 向量索引 ======================
def load_or_create_index(nodes: List, persist_dir: str = STORAGE_DIR) -> VectorStoreIndex:
    if os.path.exists(persist_dir) and len(os.listdir(persist_dir)) > 0:
        try:
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            index = load_index_from_storage(storage_context)
            print("✅ 本地索引加载成功！")
            return index
        except Exception as e:
            print(f"⚠️ 索引加载失败，重新创建...")

    print("Creating index...This may take a while...")
    index = VectorStoreIndex(nodes)
    index.storage_context.persist(persist_dir=persist_dir)
    print("✅ 新索引创建完成！")
    return index

# ====================== 检索 ======================
def retrieve_context(
    nodes: List,
    query: str,
    method: str = "neural",
    top_k: int = 1000,
    neural_threshold: float = 0.3
) -> List[Dict]:
    try:
        index = load_or_create_index(nodes)
        retriever = index.as_retriever(similarity_top_k=top_k)
        results = retriever.retrieve(query)
        return [
            {
                "file_name": node.metadata.get("file_name", "unknown"),
                "content": node.get_content()
            }
            for node in results
        ]
    except:
        return []

# ====================== 提示词 ======================
def generate_prompt(context: str, history: str, query: str, use_cot: bool = True) -> str:
    cot_instruction = ""
    if use_cot:
        cot_instruction = """
First, show your thinking process inside <Thought> tags.
Then give your final answer inside <Answer> tags.
Keep your answer clear and concise.
"""

    return f"""
You are a helpful HKBU study assistant. Answer based on the context below.

Context:
{context}

Conversation History:
{history}

User: {query}

{cot_instruction}
"""

# ====================== 查询重写 ======================
def rewrite_query(query: str, history: str):
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

    res = complete_document_sdk(prompt=prompt, temperature=0.0, stop_sequences=["\n"])
    rewritten = res["response"].strip()
    return rewritten if rewritten else query, res

# ====================== LLM 调用 ======================
def complete_document_sdk(
    prompt: str,
    model: str = LLM_MODEL,
    num_predict: int = 2048,
    temperature: float = 0.0,
    stop_sequences: List[str] = None,
    stream_callback=None
) -> Dict[str, Any]:
    if stop_sequences is None:
        stop_sequences = ["</Thought>", "</Answer>"]

    full_response = ""
    prompt_tokens = 0
    completion_tokens = 0

    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            stream=True,
            options={
                "num_predict": num_predict,
                "temperature": temperature,
                "stop": stop_sequences
            }
        )

        for chunk in response:
            content = chunk.get("response", "")
            full_response += content
            if "prompt_eval_count" in chunk:
                prompt_tokens = chunk["prompt_eval_count"]
            if "eval_count" in chunk:
                completion_tokens = chunk["eval_count"]
            if stream_callback and content.strip():
                stream_callback(content)

    except Exception as e:
        error_msg = f"LLM Error: {str(e)}"
        print(error_msg)
        if stream_callback:
            stream_callback(error_msg)
        return {"response": error_msg, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    if not full_response.strip():
        full_response = "Sorry, I couldn't generate a response."

    return {
        "response": full_response,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }


# ====================== 对话历史 ======================
class ConversationManager:
    def __init__(self):
        self.history = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_history_string(self, max_turns: int = 4):
        recent = self.history[-max_turns:]
        return "\n".join([f"{item['role']}: {item['content']}" for item in recent])

    def clear_history(self):
        self.history = []

def is_greeting(query: str) -> bool:
    q = query.strip().lower()
    greetings = {"hi", "hello", "hey", "hi!", "hello!", "hey!", "haha", "good morning", "good afternoon"}
    return q in greetings
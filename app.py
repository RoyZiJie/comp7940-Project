import customtkinter as ctk
import threading
import sys
import re
from rag_engine import (
    load_or_create_index,
    retrieve_context,
    rewrite_query,
    generate_prompt,
    complete_document_sdk,
    ConversationManager,
    STORAGE_DIR,
    nodes
)

# Configure appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def extract_answer_section(full_response: str) -> str:
    pattern = r"<Answer>\s*(.*)"
    match = re.search(pattern, full_response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    pattern2 = r"Answer:\s*(.*)"
    match2 = re.search(pattern2, full_response, re.DOTALL | re.IGNORECASE)
    if match2:
        return match2.group(1).strip()
    return full_response.strip()

class HKBUChatbotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎓 HKBU Study Assistant")
        self.geometry("900x700")
        self.resizable(True, True)
        self.conversation_manager = ConversationManager()
        self.nodes = nodes
        self.index = None
        self.current_section = "none"
        self.load_index()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        print("Closing application...")
        self.conversation_manager.clear_history()
        self.destroy()
        sys.exit(0)

    def load_index(self):
        try:
            self.index = load_or_create_index(self.nodes, persist_dir=STORAGE_DIR)
            print("✅ Index loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading index: {e}")

    def create_widgets(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, height=60)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎓 HKBU Study Assistant",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=24, weight="bold")
        )
        self.title_label.pack(pady=15)

        # Chat display
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            font=ctk.CTkFont(family="Segoe UI Emoji", size=18),
            state="disabled"
        )
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_display.tag_config("thought", foreground="#888888")
        self.chat_display.tag_config("answer", foreground="#20A2C6")

        # Input area
        self.input_frame = ctk.CTkFrame(self, height=80)
        self.input_frame.pack(fill="x", padx=10, pady=10)
        self.input_box = ctk.CTkTextbox(self.input_frame, height=50, font=ctk.CTkFont(size=14))
        self.input_box.pack(fill="x", padx=5, pady=5)
        self.input_box.bind("<Return>", lambda e: self.send_message())

        # Button frame
        self.button_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=5, pady=5)

        self.rewrite_var = ctk.BooleanVar(value=True)
        self.rewrite_checkbox = ctk.CTkCheckBox(
            self.button_frame, text="🔄 Enable Query Rewrite", variable=self.rewrite_var,
            font=ctk.CTkFont(size=13, weight="bold"), checkbox_width=18, checkbox_height=18
        )
        self.rewrite_checkbox.pack(side="left", padx=10)

        self.cot_var = ctk.BooleanVar(value=True)
        self.cot_checkbox = ctk.CTkCheckBox(
            self.button_frame, text="🧠 Show Thinking (COT)", variable=self.cot_var,
            font=ctk.CTkFont(size=13, weight="bold"), checkbox_width=18, checkbox_height=18,
            hover_color="#FF6B35"
        )
        self.cot_checkbox.pack(side="left", padx=10)

        self.clear_button = ctk.CTkButton(
            self.button_frame, text="🗑️ Clear", command=self.clear_chat,
            width=100, fg_color="#666666", hover_color="#888888"
        )
        self.clear_button.pack(side="right", padx=5)

        self.send_button = ctk.CTkButton(
            self.button_frame, text="🚀 Send", command=self.send_message,
            width=100, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.send_button.pack(side="right", padx=5)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=12), text_color="gray")
        self.status_label.pack(pady=5)

    def add_to_chat(self, role, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{role}: {message}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        user_input = self.input_box.get("1.0", "end-1c").strip()
        if not user_input or self.index is None:
            return
        self.input_box.delete("1.0", "end")
        self.add_to_chat("You", user_input)
        self.status_label.configure(text="Processing...")
        self.current_section = "none"
        threading.Thread(target=self.get_bot_response, args=(user_input,), daemon=True).start()

    def get_bot_response(self, user_input):
        try:
            from rag_engine import is_greeting
            if is_greeting(user_input):
                clean_answer = "Hello! How can I assist you with your studies today?"
                self.conversation_manager.add_message("User", user_input)
                self.conversation_manager.add_message("Assistant", clean_answer)

                # UI 显示
                self.after(0, lambda: self.chat_display.configure(state="normal"))
                self.after(0, lambda: self.chat_display.delete("end-2l", "end"))
                self.after(0, lambda: self.chat_display.insert("end", "\n✅ Answer:\n" + clean_answer + "\n", "answer"))
                self.after(0, lambda: self.chat_display.configure(state="disabled"))
                self.after(0, lambda: self.status_label.configure(text="Ready"))
                return
            # =========================================================================
            history_str = self.conversation_manager.get_history_string()
            default_tokens = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0}

            if self.rewrite_var.get():
                standalone_query, rewrite_tokens = rewrite_query(user_input, history_str)
                print(f"🔄 Rewritten: {standalone_query}")
            else:
                standalone_query = user_input
                rewrite_tokens = default_tokens

            retrieval_context = retrieve_context(nodes=self.nodes, query=standalone_query, method="neural", top_k=6)
            context_str = "\n\n".join([f"[file: {i['file_name']}]\n{i['content']}" for i in retrieval_context])

            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", "🤔 Thinking...\n")
            self.chat_display.configure(state="disabled")

            def stream_cb(chunk):
                self.after(0, lambda: self.update_last_message(chunk))

            response = complete_document_sdk(
                prompt=generate_prompt(context=context_str, history=history_str, query=user_input, use_cot=self.cot_var.get()),
                temperature=0.0,
                stream_callback=stream_cb
            )

            answer_clean = extract_answer_section(response["response"])
            self.conversation_manager.add_message("User", user_input)
            self.conversation_manager.add_message("Assistant", answer_clean)

            total = {
                "p": response["prompt_tokens"] + rewrite_tokens["prompt_tokens"],
                "c": response["completion_tokens"] + rewrite_tokens["completion_tokens"],
                "t": response["total_tokens"] + rewrite_tokens["total_tokens"]
            }

            self.after(0, lambda: self.show_token_usage(total["p"], total["c"], total["t"], len(retrieval_context)))
            self.after(0, lambda: self.status_label.configure(text="Ready"))

        except Exception as e:
            self.after(0, lambda: self.add_to_chat("System", f"Error: {str(e)}"))
            self.after(0, lambda: self.status_label.configure(text="Error"))

    def update_last_message(self, chunk):
        self.chat_display.configure(state="normal")
        clean = chunk.replace("<Thought>", "").replace("</Thought>", "").replace("<Answer>", "").replace("</Answer>", "")

        if "<Thought" in chunk and self.current_section != "thought":
            self.current_section = "thought"
            self.chat_display.delete("end-2l", "end")
            self.chat_display.insert("end", "🤔 Thought Process:\n", "thought")

        elif "<Answer" in chunk and self.current_section != "answer":
            self.current_section = "answer"
            self.chat_display.insert("end", "\n✅ Answer:\n", "answer")

        if clean.strip():
            self.chat_display.insert("end", clean, self.current_section)

        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def show_token_usage(self, p, c, t, chunks):
        self.chat_display.configure(state="normal")
        info = (f"\n📊 Token Usage:\n"
                f"   • Prompt: {p}\n"
                f"   • Completion: {c}\n"
                f"   • Total: {t}\n"
                f"   • Retrieved Chunks: {chunks}\n")
        self.chat_display.insert("end", info + "\n" + "─"*50 + "\n\n", "thought")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def clear_chat(self):
        self.conversation_manager.clear_history()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.status_label.configure(text="Ready")

if __name__ == "__main__":
    app = HKBUChatbotGUI()
    app.mainloop()
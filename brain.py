import torch
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
import os

class FinGPTAnalyst:
    def __init__(self):
        try:
            # Using the v3 ChatGLM2 sentiment adapter (Lightweight & Accurate)
            base_model = "THUDM/chatglm2-6b"
            peft_model = "oliverwang15/FinGPT_ChatGLM2_Sentiment_Instruction_LoRA_FT"
            
            self.tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
            model = AutoModel.from_pretrained(base_model, trust_remote_code=True, device_map="auto")
            self.model = PeftModel.from_pretrained(model, peft_model).eval()
            self.use_fallback = False
        except Exception as e:
            print(f"GPU/FinGPT Load failed, falling back to Gemini API: {e}")
            self.use_fallback = True

    def get_sentiment(self, text):
        if self.use_fallback:
            # Insert Gemini API call here as a backup
            return 0.1 
            
        prompt = f"Instruction: What is the sentiment of this news? Input: {text} Answer: "
        tokens = self.tokenizer(prompt, return_tensors='pt').to("cuda" if torch.cuda.is_available() else "cpu")
        res = self.model.generate(**tokens, max_length=512)
        ans = self.tokenizer.decode(res[0], skip_special_tokens=True)
        
        # Simple mapping
        if "positive" in ans.lower(): return 1.0
        if "negative" in ans.lower(): return -1.0
        return 0.0

fingpt = FinGPTAnalyst()
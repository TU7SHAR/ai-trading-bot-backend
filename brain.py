import torch
from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
import os
import google.generativeai as genai

class FinGPTAnalyst:
    def __init__(self):
        self.use_fallback = False
        try:
            # Note: This requires ~12GB VRAM. 
            base_model = "THUDM/chatglm2-6b"
            peft_model = "oliverwang15/FinGPT_ChatGLM2_Sentiment_Instruction_LoRA_FT"
            
            self.tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
            model = AutoModel.from_pretrained(base_model, trust_remote_code=True, device_map="auto")
            self.model = PeftModel.from_pretrained(model, peft_model).eval()
        except Exception as e:
            print(f"FinGPT Load failed (likely VRAM). Using Gemini Fallback: {e}")
            self.use_fallback = True
            # Configure Gemini (Add your GOOGLE_API_KEY to .env)
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini = genai.GenerativeModel('gemini-pro')

    def get_sentiment(self, text):
        if self.use_fallback:
            prompt = f"Analyze financial sentiment for this text: '{text}'. Return ONLY a number between -1.0 (very bearish) and 1.0 (very bullish)."
            response = self.gemini.generate_content(prompt)
            try: return float(response.text.strip())
            except: return 0.0
            
        prompt = f"Instruction: What is the sentiment of this news? Input: {text} Answer: "
        tokens = self.tokenizer(prompt, return_tensors='pt').to("cuda" if torch.cuda.is_available() else "cpu")
        res = self.model.generate(**tokens, max_length=512)
        ans = self.tokenizer.decode(res[0], skip_special_tokens=True)
        
        if "positive" in ans.lower(): return 1.0
        if "negative" in ans.lower(): return -1.0
        return 0.0

fingpt = FinGPTAnalyst()
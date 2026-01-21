import torch
from transformers import AutoTokenizer, AutoModel

# 加載模型：這是一個專門理解資安領域語義的 BERT
tokenizer = AutoTokenizer.from_pretrained("jackaduma/CybersecurityBERT")
model = AutoModel.from_pretrained("jackaduma/CybersecurityBERT")

def get_log_embedding(log_entry):
    """
    運作邏輯：
    1. 將 JSON 的關鍵資訊（如：執行的指令、路徑）結合成一個字串。
    2. 透過 BERT 提取特徵，取 [CLS] Token 作為整條日誌的代表向量。
    """
    # 範例日誌格式處理
    text = f"cmd: {log_entry.get('command', 'N/A')} path: {log_entry.get('path', 'N/A')}"
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 返回一個 768 維的 numpy 陣列
    return outputs.last_hidden_state[0, 0, :].numpy()
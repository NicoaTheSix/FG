# Utils 資料夾程式碼說明

這個資料夾包含一組 Python 腳本，用於處理、分析日誌資料，並將其轉換為可供視覺化的圖譜格式。整個流程從原始日誌開始，最終生成一個專注於系統活動和潛在攻擊行為的溯源圖。

## 檔案功能摘要

- **`campaign_to_txt.py`**:
  此腳本將 JSON 格式的日誌資料轉換為以 tab 分隔的文字檔（TSV/TXT）。它提取來源節點、目標節點、關係及其他元數據，為後續分析做準備。

- **`log_to_prov.py`**:
  讀取 `.txt` 檔，並使用 `networkx` 函式庫建立一個「溯源圖」（provenance graph）。此圖以 `.pkl` 格式儲存，呈現系統元件（如行程、檔案等）之間的依賴關係。

- **`node_score.py`**:
  計算溯源圖中每個節點的分數。分數主要基於節點的「入度」與「出度」（連接數），並對與攻擊行為相關的節點進行加權。結果儲存於 `.csv` 檔。

- **`generate_graph.py`**:
  提供多種圖譜生成與匯出功能：
  - `generate_full_graph`: 建立完整的圖，並匯出為 `Cytoscape JSON` 格式，可用於網頁視覺化。
  - `generate_attack_graph`: 建立一個專注於攻擊活動的子圖，利用節點分數突顯關鍵的惡意行為。
  - 包含用於清理與縮寫標籤的輔助函式，以改善視覺化效果。

- **`pipeline.py`**:
  作為整個流程的總指揮，按順序調用其他腳本。`run_full_pipeline` 函式定義了主要的處理步驟。此外，它還包含 `reduce_cpr` 和 `reduce_fd` 等圖簡化函式，用於降低大型圖的複雜度。

- **`reduction_exp.ipynb`**:
  一個 Jupyter Notebook 檔案，用於實驗和評估 `pipeline.py` 中的圖簡化演算法。

## 整體工作流程

1.  **資料轉換**: 原始的 **JSON** 日誌被轉換為結構化的 **TSV (`.txt`)** 檔案 (`campaign_to_txt.py`)。
2.  **圖譜建立**: 從 `.txt` 檔建立一個 **溯源圖 (`.pkl`)** (`log_to_prov.py`)。
3.  **節點評分**: 計算圖中各節點的重要性分數，並存成 **CSV** (`node_score.py`)。
4.  **視覺化匯出**: 根據需求生成完整圖或攻擊子圖，並匯出為 **Cytoscape JSON** 格式 (`generate_graph.py`)。

整個流程由 `pipeline.py` 串連，旨在將原始日誌資料轉化為易於分析與視覺化的圖譜模型。

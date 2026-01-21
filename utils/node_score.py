# utils/node_score.py

import networkx as nx
import pandas as pd
import pickle
import os

def compute_node_scores(graph_pkl_path, output_csv_path):
    """
    計算 provenance graph 中每個節點的分數：
      1. base_score = indegree + outdegree
      2. 將 base_score 正規化到 [0, 1] 之間
      3. 如果有攻擊關聯（非 benign），最終分數再 +1
    並輸出為 CSV。
    """
    # 1. 載入圖
    with open(graph_pkl_path, "rb") as f:
        G = pickle.load(f)

    # --- 第一階段：計算所有節點的 base_score 和 has_attack ---
    node_info = []
    max_base_score = 0
    for node in G.nodes():
        indeg = G.in_degree(node)
        outdeg = G.out_degree(node)
        base_score = indeg + outdeg

        if base_score > max_base_score:
            max_base_score = base_score

        has_attack = any(
            d.get("label", "").lower() != "benign"
            for _, _, d in G.in_edges(node, data=True)
        ) or any(
            d.get("label", "").lower() != "benign"
            for _, _, d in G.out_edges(node, data=True)
        )
        
        node_info.append({
            "node_uuid": node,
            "indegree": indeg,
            "outdegree": outdeg,
            "base_score": base_score,
            "has_attack": has_attack
        })

    # --- 第二階段：正規化並計算 final_score ---
    node_scores = []
    # 防止 max_base_score 為 0 導致除錯
    if max_base_score == 0:
        max_base_score = 1

    for info in node_info:
        # 將 base_score 正規化到 [0, 1]
        normalized_score = info["base_score"] / max_base_score
        
        # 如果是攻擊節點，分數 +1
        final_score = normalized_score + 1 if info["has_attack"] else normalized_score
        
        # 取出節點屬性
        node_uuid = info["node_uuid"]
        label = G.nodes[node_uuid].get("label", "Unknown")
        ntype = G.nodes[node_uuid].get("type", "Unknown")

        node_scores.append({
            "node_uuid": node_uuid,
            "node_label": label,
            "node_type": ntype,
            "indegree": info["indegree"],
            "outdegree": info["outdegree"],
            "base_score": info["base_score"],
            "final_score": final_score
        })

    # 5. 輸出 CSV
    df = pd.DataFrame(node_scores)
    output_csv_path = os.path.join(output_csv_path)
    df.to_csv(output_csv_path, index=False, encoding="utf-8")
    print(f"✅ Final node scores saved to {output_csv_path}")
    # ... (計算完 node_scores 之後)

    # # 5. 轉換為 DataFrame 並依 final_score 排序
    # df = pd.DataFrame(node_scores)
    # # --- START: 加入這行來符合演算法 ---
    # df = df.sort_values(by="final_score", ascending=False)
    # # --- END: 加入這行來符合演算法 ---

    # # 6. 輸出 CSV
    # # (路徑計算的程式碼省略...)
    # output_csv_path = ... 
    # df.to_csv(output_csv_path, index=False, encoding="utf-8")
    # print(f"✅ Final node scores saved to {output_csv_path}")
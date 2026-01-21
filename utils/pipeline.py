import os
from campaign_to_txt import convert_json_to_txt
from log_to_prov import build_provenance_graph
from node_score import compute_node_scores
from generate_graph import generate_full_graph, generate_attack_graph


# utils/pipeline.py

import copy

def reduce_cpr(graph_json):
    out   = copy.deepcopy(graph_json)
    edges = sorted(out["edges"],
                   key=lambda e: e["data"].get("timestamp", float("inf")))

    new_edges      = []
    last_for_pair  = {}           # (src,tgt,label) ➜ {"edge":…, "idx":…}
    last_write_src = {}           # node ➜ idx (edge.target == node)
    last_send_tgt  = {}           # node ➜ idx (edge.source == node)

    for idx, e in enumerate(edges):
        d   = e["data"]
        src, tgt, lab = d["source"], d["target"], d["label"]
        ts  = d.get("timestamp")
        key = (src, tgt, lab)

        info = last_for_pair.get(key)
        can_merge = False
        if info:
            prev_idx = info["idx"]
            # 若兩種「干擾事件」的最近位置都在 prev_idx 之前 ➜ 安全合併
            can_merge = (
                last_write_src.get(src,  -1) < prev_idx and
                last_send_tgt.get(tgt,  -1) < prev_idx
            )
        if can_merge:
            prev_edge = info["edge"]
            pdata = prev_edge["data"]
            if ts is not None:
                pdata.setdefault("timestamps", [pdata["timestamp"]])
                pdata["timestamps"].append(ts)
                pdata["timestamp"] = min(pdata["timestamps"])
        else:
            # 新開一條邊
            new_edge = {"data": dict(d)}  # 若還要保留其他欄位可改 copy.deepcopy(e)
            if ts is not None:
                new_edge["data"]["timestamps"] = [ts]
            new_edges.append(new_edge)
            last_for_pair[key] = {"edge": new_edge, "idx": idx}

        # 無論合併與否，都要更新「最後一次發生位置」索引
        last_write_src[tgt]  = idx     # 這條邊寫入了 tgt
        last_send_tgt[src]   = idx     # 這條邊來自  src

    out["edges"] = new_edges
    return out



def reduce_fd(graph_json):
    out = copy.deepcopy(graph_json)
    sorted_edges = sorted(
        out['edges'],
        key=lambda e: e['data'].get('timestamp', float('inf'))
    )

    def is_reachable(adj, start, end):
        if start == end:
            return True
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            for nbr in adj.get(node, []):
                if nbr == end:
                    return True
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append(nbr)
        return False

    adjacency = {}
    new_edges = []

    for e in sorted_edges:
        src = e['data']['source']
        tgt = e['data']['target']

        # 仅当此边引入新的前向依赖时保留
        if not is_reachable(adjacency, src, tgt):
            new_edges.append(copy.deepcopy(e))
            adjacency.setdefault(src, set()).add(tgt)

    out['edges'] = new_edges
    return out




def run_full_pipeline(
    pathInput: str,
    pathOutput: str ,   
    dirTxt: str = "txt",
    dirPkl: str = "pkl",
    dirCsv: str = "csv",
    dirJson: str = "json",
    analysisType: str = 'source',
    fileName: str = "file"
) -> str:
    """
    主流程：上傳 JSON -> 轉 TXT -> 建立 provenance graph -> 計算分數 -> 輸出 Cytoscape JSON
    可以選擇分析類型：
      - 'source': 系統來源完整圖 (呼叫 generate_full_graph)
      - 'ttp':   攻擊子圖 (呼叫 generate_attack_graph)

    Args:
        json_path: 用戶上傳的 JSON 檔案絕對路徑
        temp_dir: 中間檔案資料夾，預設 backend/uploads
        output_dir: 最終輸出資料夾，預設 static/output
        analysis_type: 分析類型 'source' 或 'ttp'

    Returns:
        json_out: 輸出的 Cytoscape JSON 完整絕對路徑
    """
    pathDirTxt=os.path.join(pathOutput,dirTxt)
    pathDirPkl=os.path.join(pathOutput,dirPkl)
    pathDirJson=os.path.join(pathOutput,dirJson)
    pathDirCsv=os.path.join(pathOutput,dirCsv)
    
    # 確保資料夾存在
    os.makedirs(pathDirTxt, exist_ok=True)
    os.makedirs(pathDirPkl, exist_ok=True)
    os.makedirs(pathDirCsv, exist_ok=True)
    os.makedirs(pathDirJson, exist_ok=True)

    # 1) JSON -> TXT
    txt_path = os.path.join(pathDirTxt, f"{fileName}.txt")
    if not os.path.exists(txt_path):
        convert_json_to_txt(pathInput, txt_path)

    # 2) TXT -> provenance graph (pickle)
    graph_pkl = os.path.join(pathDirPkl, f"{fileName}graph.pkl")
    if not os.path.exists(f"{fileName}graph.pkl"):
        build_provenance_graph(txt_path, graph_pkl)
    
    # 3) 計算節點分數 -> CSV
    score_csv = os.path.join(pathDirCsv, f"{fileName}node_scores.csv")
    if not os.path.exists(f"{fileName}node_scores.csv"):
        compute_node_scores(graph_pkl, score_csv)

    # 4) 根據分析類型輸出不同 JSON
    if analysisType == 'ttp':
        json_out = os.path.join(pathDirJson
                                , f"{fileName}latest_attack.json")
        generate_attack_graph(
            graph_pkl_path=graph_pkl,
            score_csv_path=score_csv,
            json_out=json_out,
            image_out=None,
            top_k=5,
            layout="dot"
        )
    else:
        json_out = os.path.join(pathDirJson, f"{fileName}latest_graph.json")
        generate_full_graph(
            graph_pkl_path=graph_pkl,
            json_out=json_out,
            image_out=None,
            layout="dot"
        )

    return json_out

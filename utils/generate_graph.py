import os
import json
import pickle
import pandas as pd
import networkx as nx
from collections import defaultdict
import shlex
import re

def shorten_label(text, max_len=40):
    """把文字每 max_len 字元拆行"""
    return '\n'.join(text[i:i + max_len] for i in range(0, len(text), max_len))


def sanitize_label(text):
    """轉義特殊字元，保留換行"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', "'")
    text = text.replace("'", "\\'")
    return text.strip()

def abbreviate_by_shape(raw: str, shape: str) -> str:
    """
    根據節點 shape 做不同的縮寫：
     - pentagon (registry)：\ 切，保留第一跟最後
     - rectangle (file)：\ 切，保留最後；若只有 C:\，就回傳原本
     - ellipse (process)：先 shlex.split 取第一個 token，再取 basename
     - others：不動
    """
    txt = raw.strip().strip('"')
    
    # Registry
    if shape == "pentagon":
        parts = txt.split("\\")
        if len(parts) >= 2:
            return f"{parts[0]}\\{parts[-1]}"
        else:
            return txt

    # File
    if shape == "rectangle":
        parts = txt.split("\\")
        if len(parts) >= 2:
            return parts[-1]
        else:
            return txt

    # Process (command line or path)
    if shape == "ellipse":
        # 1) 拆 command-line tokens
        try:
            tokens = shlex.split(txt)
        except ValueError:
            tokens = txt.split()
        # 2) 找第一個看起來像可執行檔的 token
        exe = None
        for tok in tokens:
            t = tok.strip('"')
            if re.search(r'\.(exe|com|bat)$', t, flags=re.IGNORECASE):
                exe = t
                break
        # 3) fallback：找不到就用第一個 token
        if not exe and tokens:
            exe = tokens[0].strip('"')
        # 4) 取 basename
        return os.path.basename(exe) if exe else txt

    # 其它類型不動
    return txt


import os
import json
import pickle
import pandas as pd
import networkx as nx
from collections import defaultdict
import shlex
import re

def sanitize_label(text: str) -> str:
    """轉義特殊字元，保留換行"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', "'")
    text = text.replace("'", "\\'")
    return text.strip()

def abbreviate_by_shape(raw: str, shape: str) -> str:
    """
    根據節點 shape 做不同的縮寫：
     - pentagon (registry)：\ 切，保留第一跟最後
     - rectangle (file)：\ 切，保留最後；若只有 C:\，就回傳原本
     - ellipse (process)：先 shlex.split 取第一個 token，再取 basename
     - others：不動
    """
    txt = raw.strip().strip('"')
    
    # Registry
    if shape == "pentagon":
        parts = txt.split("\\")
        if len(parts) >= 2:
            return f"{parts[0]}\\{parts[-1]}"
        else:
            return txt

    # File
    if shape == "rectangle":
        parts = txt.split("\\")
        if len(parts) >= 2:
            return parts[-1]
        else:
            return txt

    # Process (command line or path)
    if shape == "ellipse":
        # 1) 拆 command-line tokens
        try:
            tokens = shlex.split(txt)
        except ValueError:
            tokens = txt.split()
        # 2) 找第一個看起來像可執行檔的 token
        exe = None
        for tok in tokens:
            t = tok.strip('"')
            if re.search(r'\.(exe|com|bat)$', t, flags=re.IGNORECASE):
                exe = t
                break
        # 3) fallback：找不到就用第一個 token
        if not exe and tokens:
            exe = tokens[0].strip('"')
        # 4) 取 basename
        return os.path.basename(exe) if exe else txt

    # 其它類型不動
    return txt

# --------------------------------------------------------------------------------

def export_cytoscape_json(G: nx.Graph, json_path: str):
    cy_nodes = []
    cy_edges = []

    # 節點改寫：sanitize + abbreviate_by_shape
    for n, d in G.nodes(data=True):
        if not n:
            continue

        raw = str(d.get("label", n))
        safe = sanitize_label(raw)
        shape = d.get("shape", "ellipse")  # pentagon/rectangle/ellipse/…
        abbr = abbreviate_by_shape(safe, shape)

        cy_nodes.append({
            "data": {
                "id": str(n),
                "label": abbr,
                "fullLabel": safe,
                "color": d.get("color", "skyblue"),
                "shape": shape
            }
        })

    # 邊 (不動)
    for u, v, d in G.edges(data=True):
        if not u or not v:
            continue
        rel = d.get("relation", "")
        ttp = d.get("label", "")
        if ttp and ttp.lower() != "benign":
            rel += f" [{ttp}]"
        edge_data = {"source": str(u), "target": str(v), "label": rel}
        if "timestamp" in d:
            edge_data["timestamp"] = d["timestamp"]
        cy_edges.append({"data": edge_data})

    cy_data = {"nodes": cy_nodes, "edges": cy_edges}
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cy_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported Cytoscape JSON to {json_path}")



def generate_full_graph(
    graph_pkl_path: str,
    json_out: str,
    image_out: str = None,
    layout: str = "dot"
):
    with open(graph_pkl_path, "rb") as f:
        G = pickle.load(f)

    for n in G.nodes():
        G.nodes[n].setdefault("label", G.nodes[n].get("label", n))
        G.nodes[n].setdefault("color", "skyblue")
        t = G.nodes[n].get("type", "").lower()
        G.nodes[n].setdefault("shape", {
            "process": "ellipse",
            "file":     "rectangle",
            "registry": "pentagon",
            "network":  "diamond"
        }.get(t, "ellipse"))

    export_cytoscape_json(G, json_out)

    if image_out:
        from networkx.drawing.nx_pydot import to_pydot
        def export_graphviz(G, path, layout, rankdir="LR"):
            H = nx.MultiDiGraph() if G.is_multigraph() else nx.DiGraph()
            old2new = {}
            for idx, (n, d) in enumerate(G.nodes(data=True)):
                raw = str(d.get("label", n))
                safe = sanitize_label(raw)
                label = shorten_label(safe)
                node_id = f"n{idx}"
                old2new[n] = node_id
                H.add_node(node_id, label=label, shape=d.get("shape"), fillcolor=d.get("color"), style="filled")
            for u, v, d in G.edges(data=True):
                rel = sanitize_label(d.get("relation", ""))
                H.add_edge(old2new[u], old2new[v], label=rel)
            pg = to_pydot(H)
            pg.set_prog(layout)
            pg.set_graph_defaults(
                dpi="300",
                overlap="false",
                splines="polyline",
                concentrate="true",
                rankdir=rankdir,
                nodesep="0.3",
                ranksep="0.5",
                margin="0.2"
            )
            ext = path.lower().rsplit('.', 1)[-1]
            if ext == "png": pg.write_png(path)
            elif ext == "svg": pg.write_svg(path, encoding='utf-8')
            else: raise ValueError("Only support .png or .svg")
            print(f"✅ Exported graph image to {path}")
        os.makedirs(os.path.dirname(image_out), exist_ok=True)
        export_graphviz(G, image_out, layout)


def generate_attack_graph(
    graph_pkl_path: str,
    score_csv_path: str,
    json_out: str,
    image_out: str = None,
    top_k: int = 5,
    layout: str = "dot"
):
    
    # 0. 先讀 enterprise_techniques.csv
    #    假設這份 CSV 放在專案根目錄下
    csv_path = os.path.join(os.path.dirname(__file__), os.pardir, "enterprise_techniques.csv")
    df_map = pd.read_csv(csv_path, encoding="utf-8")
    ttp_name_map = dict(zip(df_map["TTP ID"], df_map["TTP NAME"]))

    # 1. 讀原始圖與分數
    with open(graph_pkl_path, "rb") as f:
        G0 = pickle.load(f)
    df = pd.read_csv(score_csv_path)
    score = dict(zip(df["node_uuid"], df["final_score"]))

    # 2. 找到所有非 benign 的 edges 當 seeds
    attack = {u for u, v, d in G0.edges(data=True) if d.get("label") != "benign"} | {v for u, v, d in G0.edges(data=True) if d.get("label") != "benign"}
    seeds = set(attack)
    for a in list(attack):
        seeds |= nx.ancestors(G0, a)

    # 3. Top-K benign 節點擴散
    expanded = set()
    for u in seeds:
        nonb, ben = [], []
        for _, v, d in G0.out_edges(u, data=True):
            (nonb if d.get("label")!="benign" else ben).append((v, score.get(v,0)))
        nonb = [v for v, _ in dict.fromkeys(nonb)]
        ben = sorted(dict.fromkeys(ben), key=lambda x: score.get(x,0), reverse=True)
        chosen = nonb + [v for v in ben if v not in nonb][:top_k]
        expanded.update(chosen)

    keep = seeds | expanded
    G_sub = G0.subgraph(keep).copy()

    # 4. 不做任何合併，保留原始每一條 edge
    G_clean = nx.MultiDiGraph()
    G_clean.add_nodes_from(G_sub.nodes(data=True))
    for u, v, d in G_sub.edges(data=True):
        rel = d.get("relation", "")
        raw_ttp = d.get("label", "")       # e.g. "T1566.001_1afae…"
        
        # 如果這是一個攻擊 TTP，就做 mapping
        if raw_ttp and raw_ttp.lower() != "benign":
            # 先拆出前半段 ID
            ttp_id = raw_ttp.split("_", 1)[0]
            # 從 map 裡找 NAME，找不到就保留原 ID
            ttp_name = ttp_name_map.get(ttp_id, ttp_id)
            # 你可以決定要顯示 "ID_NAME" 或只顯示 "NAME"
            new_ttp_label = f"{ttp_id} {ttp_name}"
        else:
            new_ttp_label = raw_ttp

        attrs = {
            "relation": rel,
            # 用新字串
            "label": new_ttp_label
        }
        if "timestamp" in d and d["timestamp"] is not None:
            attrs["timestamp"] = d["timestamp"]

        G_clean.add_edge(u, v, **attrs)


    # 5. 重編號並設定節點屬性
    mapping = {old: f"n{i}" for i, old in enumerate(G_clean.nodes())}
    G = nx.relabel_nodes(G_clean, mapping, copy=True)
    inv = {v: k for k, v in mapping.items()}
    for n in G.nodes():
        old = inv[n]
        G.nodes[n]["label"] = str(G0.nodes[old].get("label", old))
        # G.nodes[n]["color"] = "red" if old in attack else ("orange" if old in expanded else "skyblue")
        G.nodes[n]["color"] = "skyblue"
        G.nodes[n]["attack_flag"] = old in attack
        G.nodes[n]["expanded_flag"] = old in expanded
        
        t = G0.nodes[old].get("type", "").lower()
        G.nodes[n]["shape"] = {"process":"ellipse","file":"rectangle","registry":"pentagon","network":"diamond"}.get(t, "ellipse")


    # 6. 輸出 Cytoscape JSON
    export_cytoscape_json(G, json_out)

    # 7. 可選輸出圖檔
    if image_out:
        from networkx.drawing.nx_pydot import to_pydot
        os.makedirs(os.path.dirname(image_out), exist_ok=True)
        def export_graphviz(G, path, layout, rankdir="LR"):
            H = nx.MultiDiGraph() if G.is_multigraph() else nx.DiGraph()
            old2new = {}
            for idx,(n,d) in enumerate(G.nodes(data=True)):
                raw = str(d.get("label",n))
                safe = sanitize_label(raw)
                label = shorten_label(safe)
                node_id = f"n{idx}";
                old2new[n] = node_id
                H.add_node(node_id, label=label, shape=d.get("shape"), fillcolor=d.get("color"), style="filled")
            for u,v,d in G.edges(data=True):
                rel = sanitize_label(d.get("relation",""))
                H.add_edge(old2new[u], old2new[v], label=rel)
            pg = to_pydot(H)
            pg.set_prog(layout)
            pg.set_graph_defaults(dpi="300", overlap="false", splines="polyline", concentrate="true", rankdir=rankdir, nodesep="0.3", ranksep="0.5", margin="0.2")
            ext = path.lower().rsplit('.',1)[-1]
            if ext == "png": pg.write_png(path)
            elif ext == "svg": pg.write_svg(path, encoding='utf-8')
            else: raise ValueError("Only support .png or .svg")
            print(f"✅ Exported graph image to {path}")
        export_graphviz(G, image_out, layout)

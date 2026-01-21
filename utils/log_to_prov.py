# utils/log_to_prov.py

import networkx as nx
import pickle

def build_provenance_graph(txt_path, pkl_path):
    """
    從 .txt 建立 provenance graph 並儲存為 .pkl。
    :param txt_path: 輸入檔案路徑（tab 分隔格式）
    :param pkl_path: 輸出圖檔路徑（pickle）
    """
    G = nx.MultiDiGraph()

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            fields = line.strip().split('\t')
            if len(fields) != 9:
                continue

            src_uuid, src_label, src_type, dst_uuid, dst_label, dst_type, relation, timestamp, label = fields

            if not G.has_node(src_uuid):
                G.add_node(src_uuid, label=src_label, type=src_type)
            if dst_uuid != "None" and not G.has_node(dst_uuid):
                G.add_node(dst_uuid, label=dst_label, type=dst_type)

            if dst_uuid != "None":
                G.add_edge(src_uuid, dst_uuid,
                           relation=relation,
                           timestamp=int(timestamp),
                           label=label)

    with open(pkl_path, "wb") as f:
        pickle.dump(G, f)

    print(f" Graph saved: {pkl_path}")
    print(f"節點數量: {G.number_of_nodes()}，邊數量: {G.number_of_edges()}")

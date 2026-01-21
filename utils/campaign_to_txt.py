import json
import pandas as pd
import os

def get_node_label(node_dict: dict) -> str:
    if node_dict is None:
        return None
    node_type = node_dict.get("Type", "").lower()
    if node_type == "process":
        return node_dict.get("Cmdline") or node_dict.get("UUID", "Unknown")
    elif node_type == "registry":
        return node_dict.get("Key") or node_dict.get("UUID", "Unknown")
    elif node_type == "file":
        return node_dict.get("Name") or node_dict.get("UUID", "Unknown")
    elif node_type == "network":
        return node_dict.get("Dstaddress") or node_dict.get("UUID", "Unknown")
    return node_dict.get("UUID", "Unknown")

def get_node_uuid(node_dict: dict) -> str:
    if node_dict is None:
        return None
    return node_dict.get("UUID")

def get_node_type(node_dict: dict) -> str:
    if node_dict is None:
        return None
    return node_dict.get("Type", "Unknown")

def convert_json_to_txt(input_path: str, output_path: str):
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            event = json.loads(line)
            src_node = event.get("srcNode")
            dst_node = event.get("dstNode")
            relation = event.get("relation")
            timestamp = event.get("timestamp")
            label = event.get("label")

            row = {
                "src_uuid": get_node_uuid(src_node),
                "src_label": get_node_label(src_node),
                "src_type": get_node_type(src_node),
                "dst_uuid": get_node_uuid(dst_node),
                "dst_label": get_node_label(dst_node),
                "dst_type": get_node_type(dst_node),
                "relation": relation,
                "timestamp": timestamp,
                "label": label
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, sep="\t", index=False, header=False, encoding="utf-8")
    print(f"✅ Converted to txt: {output_path}")

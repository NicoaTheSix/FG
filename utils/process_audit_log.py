import re
import pandas as pd
import networkx as nx
import pickle
import os
import argparse
from collections import defaultdict
import shlex

# Regular expression to parse the header of an audit log line
AUDIT_MSG_REGEX = re.compile(r'type=([^ ]+) msg=audit\((\d+\.\d+:\d+)\):(.*)')

def parse_audit_log(input_path: str):
    """
    Parses a Linux audit log file and yields structured event data.
    """
    events = defaultdict(dict)
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = AUDIT_MSG_REGEX.match(line)
            if not match:
                continue

            msg_type, msg_id, data_str = match.groups()
            
            # The event with the SYSCALL type is the root of the event
            if msg_type == 'SYSCALL':
                if msg_id in events:
                    # Process the completed event before starting a new one
                    yield process_event_group(events[msg_id])
                    del events[msg_id]
            
            events[msg_id]['type'] = msg_type
            
            # Store the data for the current message
            if 'data' not in events[msg_id]:
                events[msg_id]['data'] = []
            events[msg_id]['data'].append(data_str.strip())

    # Process any remaining events
    for event_id in events:
        yield process_event_group(events[event_id])

def process_event_group(event_group):
    """
    Processes a group of log lines that belong to the same event.
    """
    event_data = {'srcNode': None, 'dstNode': None, 'relation': None, 'timestamp': None, 'label': 'Unknown'}
    
    # Simple parsing of key-value pairs from the data string
    parsed_data = {}
    if 'data' in event_group:
        for item in event_group['data']:
            try:
                # This is a simplification; a more robust parser would be needed for all cases
                parts = shlex.split(item)
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        parsed_data[key] = value.strip('"')
            except ValueError:
                pass # Ignore lines that cannot be parsed

    # Extract timestamp from the message id
    if 'type' in event_group and event_group.get('type') == 'SYSCALL':
        try:
            syscall_data = [d for d in event_group['data'] if 'syscall=' in d][0]
            syscall_parts = shlex.split(syscall_data)
            syscall_info = {p.split('=', 1)[0]: p.split('=', 1)[1].strip('"') for p in syscall_parts if '=' in p}
            
            event_data['timestamp'] = int(float(event_group['msg_id'].split(':')[0]))
            event_data['relation'] = syscall_info.get('syscall')
            event_data['label'] = syscall_info.get('key', 'Unknown')
            
            # Create the source node (process)
            event_data['srcNode'] = {
                'UUID': f"process-{syscall_info.get('pid')}",
                'Type': 'process',
                'Cmdline': syscall_info.get('exe') or syscall_info.get('comm'),
                'pid': syscall_info.get('pid'),
                'ppid': syscall_info.get('ppid'),
            }

            # Find associated PATH data to create the destination node (file)
            path_data_list = [d for d in event_group['data'] if ' name=' in d and 'nametype=' in d]
            if path_data_list:
                path_data = path_data_list[0]
                path_parts = shlex.split(path_data)
                path_info = {p.split('=', 1)[0]: p.split('=', 1)[1].strip('"') for p in path_parts if '=' in p}
                
                event_data['dstNode'] = {
                    'UUID': f"file-{path_info.get('inode')}",
                    'Type': 'file',
                    'Name': path_info.get('name'),
                    'inode': path_info.get('inode'),
                }

        except (ValueError, IndexError) as e:
            # Not all syscalls will have the expected structure
            # print(f"Could not parse event group: {event_group}. Error: {e}")
            pass
            
    return event_data if event_data['srcNode'] else None

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

def convert_events_to_tsv(events_iterator, output_path: str):
    rows = []
    for event in events_iterator:
        if not event or not event.get("srcNode"):
            continue
            
        src_node = event.get("srcNode")
        dst_node = event.get("dstNode")
        
        row = {
            "src_uuid": get_node_uuid(src_node),
            "src_label": get_node_label(src_node),
            "src_type": get_node_type(src_node),
            "dst_uuid": get_node_uuid(dst_node),
            "dst_label": get_node_label(dst_node),
            "dst_type": get_node_type(dst_node),
            "relation": event.get("relation"),
            "timestamp": event.get("timestamp"),
            "label": event.get("label")
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, sep="\t", index=False, header=False, encoding="utf-8")
    print(f"✅ Converted to TSV: {output_path}")

def build_provenance_graph(txt_path, pkl_path):
    """
    Builds a provenance graph from a .txt file and saves it as a .pkl file.
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
                           timestamp=int(timestamp) if timestamp.isdigit() else timestamp,
                           label=label)

    with open(pkl_path, "wb") as f:
        pickle.dump(G, f)

    print(f"Graph saved: {pkl_path}")
    print(f"Number of nodes: {G.number_of_nodes()}, Number of edges: {G.number_of_edges()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Linux audit logs to generate a provenance graph.")
    parser.add_argument("input_log", help="Path to the input audit log file.")
    parser.add_argument("-t", "--tsv", help="Path to the output TSV file.", required=True)
    parser.add_argument("-p", "--pkl", help="Path to the output pickle file for the graph.", required=True)
    args = parser.parse_args()

    print(f"Starting to parse log file: {args.input_log}")
    events_iterator = parse_audit_log(args.input_log)
    
    convert_events_to_tsv(events_iterator, args.tsv)
    
    build_provenance_graph(args.tsv, args.pkl)

    print("✅ Processing complete.")

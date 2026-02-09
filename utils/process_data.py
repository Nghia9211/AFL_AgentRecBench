import json
import os
import pandas as pd
import collections
from tqdm import tqdm
from datetime import datetime


RAW_DIR = './output_data_all'  
OUTPUT_DIR = './data'          
GROUND_TRUTH_FILE = './ground_truth.json' 
MAX_SEQ_LEN = 50               
MIN_INTERACTION = 5  

def get_normalized_timestamp(data, source):
    try:
        if source == 'amazon': return int(data.get('timestamp', 0))
        elif source == 'yelp':
            date_str = data.get('date')
            if date_str:
                return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").timestamp())
        elif source == 'goodreads':
            date_str = data.get('date_added') or data.get('date_updated')
            if date_str:
                return int(datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y").timestamp())
        return 0
    except: return 0

def pad_seq(s, max_len, pad_val):
    s = s[-max_len:]
    return [pad_val] * (max_len - len(s)) + s

def process_source(target_source):
    print(f"\n⏩ ĐANG XỬ LÝ: {target_source.upper()}")
    save_dir = os.path.join(OUTPUT_DIR, target_source)
    os.makedirs(save_dir, exist_ok=True)


    gt_map = {}
    if os.path.exists(GROUND_TRUTH_FILE):
        with open(GROUND_TRUTH_FILE, 'r', encoding='utf-8') as f:
            gt_list = json.load(f)

            gt_map = {item["user_id"]: item["item_id"] for item in gt_list}
    print(f"📍 Target Test Users từ GT: {len(gt_map)}")


    item_file = os.path.join(RAW_DIR, 'item.json')
    raw_id_to_inner_id = {}
    id2name = {} 
    item_count = 1 
    title_key = 'name' if target_source == 'yelp' else 'title'
    
    with open(item_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('source') == target_source:
                    raw_id = data.get('item_id')
                    if raw_id not in raw_id_to_inner_id:
                        raw_id_to_inner_id[raw_id] = item_count
                        id2name[item_count] = data.get(title_key, "Unknown").strip()
                        item_count += 1
            except: continue
    
    with open(os.path.join(save_dir, 'id2name.txt'), 'w', encoding='utf-8') as f:
        for iid, name in id2name.items():
            clean_name = name.replace('\n', ' ').replace('\r', ' ')
            f.write(f"{iid}::{clean_name}\n")

   
    review_file = os.path.join(RAW_DIR, 'review.json')
    user_interactions = collections.defaultdict(list)
    

    review_count = 0
    with open(review_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('source') == target_source:
                    uid, iid_raw = data.get('user_id'), data.get('item_id')
                    ts = get_normalized_timestamp(data, target_source)
                    if iid_raw in raw_id_to_inner_id:
                        user_interactions[uid].append((ts, raw_id_to_inner_id[iid_raw], iid_raw))
                        review_count += 1
            except: continue
    print(f"📍 Tổng số interactions tìm thấy cho {target_source}: {review_count}")


    train_data, val_data, test_data = [], [], []
    gt_found_count = 0

    for uid, interactions in tqdm(user_interactions.items(), desc="Splitting"):
        interactions.sort(key=lambda x: x[0])
        inner_ids = [x[1] for x in interactions]
        raw_ids = [x[2] for x in interactions]

        if uid in gt_map:
            target_raw_iid = gt_map[uid]
            
            if target_raw_iid in raw_ids:
                idx = raw_ids.index(target_raw_iid)
                seq_before = inner_ids[:idx]

                test_data.append({
                    'uid': uid,
                    'seq': pad_seq(seq_before, MAX_SEQ_LEN, 0),
                    'len_seq': min(len(seq_before), MAX_SEQ_LEN),
                    'next': inner_ids[idx]
                })
                gt_found_count += 1
                continue
            else:
                pass

        if len(inner_ids) >= MIN_INTERACTION:
            val_data.append({
                'uid': uid,
                'seq': pad_seq(inner_ids[:-1], MAX_SEQ_LEN, 0),
                'len_seq': min(len(inner_ids)-1, MAX_SEQ_LEN),
                'next': inner_ids[-1]
            })
            train_data.append({
                'uid': uid,
                'seq': pad_seq(inner_ids[:-2], MAX_SEQ_LEN, 0),
                'len_seq': min(len(inner_ids)-2, MAX_SEQ_LEN),
                'next': inner_ids[-2]
            })

    pd.DataFrame({'seq_size': [MAX_SEQ_LEN], 'item_num': [item_count]}).to_pickle(os.path.join(save_dir, 'data_statis.df'))
    pd.DataFrame(train_data).to_pickle(os.path.join(save_dir, 'train_data.df'))
    pd.DataFrame(val_data).to_pickle(os.path.join(save_dir, 'Val_data.df'))
    pd.DataFrame(test_data).to_pickle(os.path.join(save_dir, 'Test_data.df'))
    
    print(f"✅ Hoàn tất {target_source.upper()}:")
    print(f"   - Test samples (Đã khớp GT): {gt_found_count} / {len(gt_map)}")
    print(f"   - Train samples: {len(train_data)}")
    print(f"   - Val samples: {len(val_data)}")

if __name__ == "__main__":
    for source in ['yelp', 'amazon', 'goodreads']:
        process_source(source)
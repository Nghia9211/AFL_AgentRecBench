# --- START OF FILE test.py (Final Version Sửa đổi) ---

import argparse
import os
import time
import json
import pandas as pd
from tqdm import tqdm
import random
from torch.utils.data import Dataset, DataLoader
import multiprocessing
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.dialogue_manager import recommend, error_handler
from utils.data_processor import load_candidate_map, load_item_name_map, prepare_merge_data
from AFL2.utils.save_result import save_final_metrics
from utils.rw_process import append_jsonl
from dataset.general_dataset import GeneralDataset 
from utils.agent import UserModelAgent,RecAgent

finish_num = 0
total = 0
correct_hit1 = 0 
correct_hit3 = 0
correct_hit5 = 0

# --- Hàm lấy Argument ---
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='', help='Thư mục chứa dữ liệu (ví dụ: ./data/amazon).')
    parser.add_argument('--model_path', type=str, default=None, help='Đường dẫn tới mô hình SASRec đã train (.pt).')
    
    # Argument mới thay thế prior_file
    parser.add_argument('--input_json_file', type=str, default='', help='Đường dẫn đến file JSON mới chứa user_id và item_id (Ground Truth).')
    
    # !!! ĐÃ THÊM DÒNG NÀY !!!
    parser.add_argument('--candidate_dir', type=str, default=None, help='Thư mục chứa các file Candidate List (task_i.json).')
    
    # Argument cho file mapping item ID sang Name/Title
    parser.add_argument('--item_mapping_file', type=str, default=None, help='Đường dẫn đến file item.jsonl (hoặc tương tự) chứa ánh xạ Item ID -> Item Name/Title.')

    parser.add_argument('--stage', type=str, default='test', choices=['train', 'val', 'test'], help='Giai đoạn dataset để lấy sequence của user.')
    parser.add_argument('--cans_num', type=int, default=20, help='Số lượng ứng viên (candidates) để mô hình chọn (bao gồm GT).')
    parser.add_argument('--max_samples', type=int, default=-1, help='Giới hạn số lượng mẫu cần dự đoán (-1 là tất cả).')
    parser.add_argument('--sep', type=str, default=', ', help='Ký tự phân tách cho chuỗi tên item.')
    parser.add_argument('--max_epoch', type=int, default=3, help='Số vòng lặp tối đa cho mỗi user trong cuộc hội thoại (LLM Dialogue).')
    parser.add_argument('--output_file', type=str, default='./output/dialogue_results.jsonl', help='Đường dẫn để lưu kết quả cuối cùng.')
    
    "LLM Argument"
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Tên model LLM.')
    parser.add_argument('--api_key', type=str, default=None, help='API Key cho LLM.')
    parser.add_argument('--max_retry_num', type=int, default=5, help='Số lần thử lại tối đa cho mỗi API call.')
    parser.add_argument('--temperature', type=float, default=0.0, help='Nhiệt độ cho sampling của LLM.')
    
    "Path Argument"
    parser.add_argument('--seed', type=int, default=333, help='Seed cho random.')
    parser.add_argument('--mp', type=int, default=4, help='Số lượng tiến trình con (multiprocessing).')
    parser.add_argument("--save_info", action="store_true", help='Lưu lại lịch sử hội thoại của từng user vào file riêng.')
    parser.add_argument("--save_rec_dir", type=str, default='./output/rec_logs', help='Thư mục lưu log của Rec Agent.')
    parser.add_argument("--save_user_dir", type=str, default='./output/user_logs', help='Thư mục lưu log của User Agent.')

    "Model Argument"
    parser.add_argument('--hidden_size', type=int, default=64, help='Kích thước ẩn của SASRec.')
    parser.add_argument('--dropout', type=float, default=0.1, help='Dropout rate cho SASRec.')

    "Output File path"
    parser.add_argument('--result_file', type=str, default='evaluation_summary.json', help='Tên file lưu kết quả Hit Rate (JSON).')
    
    return parser.parse_args()


def setcallback(x):
    global finish_num, total, correct_hit1, correct_hit3, correct_hit5
    data_list, hit_at_n, args = x
    for step in data_list: append_jsonl(args.output_file, step)
    finish_num += 1
    if hit_at_n[1]: correct_hit1 += 1
    if hit_at_n[3]: correct_hit3 += 1
    if hit_at_n[5]: correct_hit5 += 1
    print(f"[{finish_num}/{total}] Hit@1: {correct_hit1/finish_num*100:.2f}% | Hit@3: {correct_hit3/finish_num*100:.2f}% | Hit@5: {correct_hit5/finish_num*100:.2f}%")

def main(args):
    # 1. Load basic data
    dataset = GeneralDataset(args, stage=args.stage)
    data_map = {str(d['id']): d for d in dataset}
    
    with open(args.input_json_file, 'r', encoding='utf-8') as f:
        new_input_list = json.load(f)

    # 2. Load Mappings (Sử dụng hàm từ utils)
    candidate_map = load_candidate_map(args.candidate_dir)
    item_name_map = load_item_name_map(args.item_mapping_file)

    # 3. Init SASRec Agent for Prior
    temp_args = argparse.Namespace(**vars(args))
    temp_args.model = 'sasrec_inference'
    sasrec_tool = UserModelAgent(temp_args, mode='prior_rec')

    # 4. Prepare Data (Sử dụng hàm từ utils)
    merge_data_list, skipped = prepare_merge_data(new_input_list, data_map, candidate_map, item_name_map, sasrec_tool, args)
    
    if args.max_samples > 0: merge_data_list = merge_data_list[:args.max_samples]
    
    global total
    total = len(merge_data_list)
    print(f"Ready: {total} samples. Skipped: {skipped}")

    # 5. Multiprocessing
    pool = multiprocessing.Pool(args.mp)
    for data in merge_data_list:
        pool.apply_async(recommend, args=(data, args), callback=setcallback, error_callback=error_handler)
    pool.close()
    pool.join()

    # 6. Save Metrics
    save_final_metrics(args, total, correct_hit1, correct_hit3, correct_hit5)

if __name__ == '__main__':
    args = get_args()
    random.seed(args.seed)
    main(args)
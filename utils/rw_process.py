import json
import pickle
import csv
import os

# -------------------------------------------------------------
# Đã xóa import jsonlines
# Thay thế bằng logic: json.dumps(data) + '\n'
# -------------------------------------------------------------

def read_jsonl(file_path):
    data_list = []
    # Hàm này của bạn vốn đã dùng json chuẩn rồi, nên vẫn giữ nguyên
    with open(file_path, "r", encoding='utf-8') as file:
        for line in file:
            line = line.strip() # Xóa khoảng trắng thừa/xuống dòng nếu có
            if line: # Chỉ xử lý nếu dòng không rỗng
                json_data = json.loads(line)
                data_list.append(json_data)
    return data_list

def write_jsonl(file_path, data_list):
    with open(file_path, 'w', encoding='utf-8') as f:
        for data in data_list:
            # Chuyển dict thành string JSON, thêm xuống dòng (\n) ở cuối
            # ensure_ascii=False để hiển thị tiếng Việt đẹp, không bị mã hóa \uXXXX
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + '\n')
            
def append_jsonl(file_path, data):
    # Tạo thư mục cha nếu chưa tồn tại (giữ nguyên logic cũ)
    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    
    # Mở file chế độ 'a' (append)
    with open(file_path, 'a', encoding='utf-8') as f:
        line = json.dumps(data, ensure_ascii=False)
        f.write(line + '\n')

# -------------------------------------------------------------
# Các hàm dưới đây giữ nguyên vì không liên quan đến jsonlines
# -------------------------------------------------------------

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as json_file: # Nên thêm utf-8 để an toàn
        data_list = json.load(json_file)
    return data_list
            
def write_json(file_path, data_list):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data_list, file, ensure_ascii=False, indent=4)  

def read_pk(file_path):
    with open(file_path, 'rb') as f:
        data_list = pickle.load(f)
    return data_list

def write_pk(file_path, data_list):
    with open(file_path, 'wb') as file:
        pickle.dump(data_list, file)

def read_csv(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        data_reader = csv.DictReader(csvfile)
        data_list = [data for data in data_reader]
    return data_list

def write_csv(file_path, data_list):
    if not data_list: return # Tránh lỗi nếu list rỗng
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data_list[0].keys())
        writer.writeheader()
        for row in data_list:
            writer.writerow(row)
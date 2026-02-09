import re

def split_rec_reponse(response):
    if response is None:
        print("[split_rec_reponse] response is None")
        return None, None
    response = str(response) + '\n'
    pattern = r'Reason: (.*?)\nItem: (.*?)\n'
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) != 1:
        print("[split_rec_reponse]can not split, response = ", response)
        return None, None
    match = matches[0]
    return match[0].strip(), match[1].strip()

def split_user_response(response):
    if response is None:
        print("[split_user_response] response is None")
        return None, None
    response = str(response) + '\n'
    pattern = r'Reason: (.*?)\nDecision: (.*?)\n'
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) != 1:
        print("[split_user_response]can not split, response = ", response)
        return None, None

    match = matches[0]
    if match[1].lower().startswith('yes'):
        return match[0].strip(), True
    elif match[1].lower().startswith('no'):
        return match[0].strip(), False
    else:
        print("[split_user_reponse]can not find flag, response = ", response)
        return None, None
    

def split_user_rec_reponse(response):
    if response is None:
        print("[split_user_rec_reponse] response is None")
        return None, None
    response = str(response) + '\n'
    pattern = r'Reason: (.*?)\nItem: (.*?)\n'
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) != 1:
        print("[split_user_rec_reponse]can not split, response = ", response)
        return None, None
    match = matches[0]
    return match[0].strip(), match[1].strip()

def split_user_ab_response(response): 
    if response is None:
        print("[split_user_ab_response] response is None")
        return None, None
    response = str(response) + '\n'
    pattern = r'Reason: (.*?)\nDecision: (.*?)\n'
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) != 1:
        print("[split_user_ab_reponse]can not split, response = ", response)
        return None, None

    match = matches[0]
    if match[1].lower().startswith('yes'):
        return match[0].strip(), 1
    elif match[1].lower().startswith('no'):
        return match[0].strip(), 0
    else:
        print("[split_user_ab_reponse]can not find flag, response = ", response)
        return None, None
    
def split_prior_rec_response(response):
    if response is None:
        print("[split_prior_rec_response] response is None")
        return None
    response = str(response) + '\n'
    pattern = r'Item: (.*?)\n'
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) != 1:
        print("[split_prior_rec_response]can not split, response = ", response)
        return None
    match = matches[0]
    return match.strip()

def split_prior_llama3_response(response):
    if response is None:
        print("[split_prior_llama3_response] response is None")
        return None
    response = str(response)
    pattern = r'Item: (.*?)<\|eot_id\|>'
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) != 1:
        print("[split_prior_llama3_response]can not split,try split2,  response = ", response)
        return split_prior_rec_response(response)
    match = matches[0]
    return match.strip()

def split_rec_reponse_top_n(response):
    if response is None:
        return None, None
    response = str(response) + '\n'
    # Pattern mới để bắt danh sách Items
    pattern = r'Reason: (.*?)\nItems: (.*?)\n' 
    matches = re.findall(pattern, response, re.DOTALL)
    
    if not matches:
        # Fallback nếu dùng Item: (chỉ lấy 1 item)
        fallback_pattern = r'Reason: (.*?)\nItem: (.*?)\n'
        fallback_matches = re.findall(fallback_pattern, response, re.DOTALL)
        if fallback_matches:
            reason = fallback_matches[0][0].strip()
            item_list_str = fallback_matches[0][1].strip()
            
            # Khắc phục 1: Phải trả về list item ngay cả khi chỉ có 1
            return reason, [item_list_str]
        
        print("[split_rec_reponse_top_n]can not split, response = ", response)
        return None, None
        
    match = matches[0]
    reason = match[0].strip()
    item_list_str = match[1].strip()
    
    # --- KHẮC PHỤC 2: THÊM LỆNH RETURN VÀ LOGIC CHUYỂN CHUỖI SANG LIST ---
    # Tách chuỗi items thành list (vì nó là danh sách Top-N)
    item_list = [item.strip() for item in item_list_str.split(',') if item.strip()]
    
    return reason, item_list # <--- THÊM DÒNG NÀY VÀ ĐÂY LÀ KẾT QUẢ CUỐI CÙNG
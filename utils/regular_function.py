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

def extract_positive_mentions(user_reason, rec_item_list, max_items=2):
    """Extract items from the recommendation list that the user engaged with positively.

    During a dialogue round, the user rejects the overall list but may still show
    affinity toward specific items.  This function identifies those items so they
    can be used as pseudo-interactions to warm up the sequential reward model
    (Strategy 3 – Dynamic Sequence Augmentation).

    Extraction heuristic (ordered by signal strength):
    1. Items explicitly mentioned by name in ``user_reason`` without strong
       negative qualifiers are treated as *engaged* items.
    2. If no item is mentioned by name, the **top-1** item from ``rec_item_list``
       (which the RecAgent ranked highest) is used as a weak positive signal.

    Args:
        user_reason: The textual reason the user provided for rejecting the list.
        rec_item_list: The ordered list of recommended item **names** from the
            RecAgent (index 0 = highest ranked).
        max_items: Maximum number of items to return per round to avoid
            flooding the sequence.

    Returns:
        A list of item name strings (length <= ``max_items``).
    """
    if not user_reason or not rec_item_list:
        return []

    NEGATIVE_QUALIFIERS = [
        "not what i", "don't want", "not interested", "completely wrong",
        "irrelevant", "not relevant", "nothing to do", "not related",
        "dislike", "hate",
    ]

    reason_lower = user_reason.lower()
    mentioned_items = []

    for item_name in rec_item_list:
        item_lower = item_name.lower().strip()
        if not item_lower:
            continue

        # Check if item name (or a significant substring) appears in the reason
        if item_lower in reason_lower:
            # Look for strong negative qualifiers near the mention
            mention_pos = reason_lower.index(item_lower)
            # Examine a window around the mention (80 chars before, 40 after)
            window_start = max(0, mention_pos - 80)
            window_end = min(len(reason_lower), mention_pos + len(item_lower) + 40)
            context_window = reason_lower[window_start:window_end]

            is_negative = any(neg in context_window for neg in NEGATIVE_QUALIFIERS)
            if not is_negative:
                mentioned_items.append(item_name)

    # Deduplicate while preserving order
    seen = set()
    unique_items = []
    for item in mentioned_items:
        key = item.lower().strip()
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    if unique_items:
        return unique_items[:max_items]

    # Fallback: use the top-ranked recommended item as a weak positive signal
    return [rec_item_list[0]]


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
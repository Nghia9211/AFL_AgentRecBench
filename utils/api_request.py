import requests
import time
import json # Import thư viện json

def api_request(system_prompt, user_prompt, args, few_shot=None):
    if "gpt" in args.model:
        return gpt_api(system_prompt, user_prompt, args, few_shot)
    else:
        raise ValueError(f"Unsupported model: {args.model}") 


def gpt_api(system_prompt, user_prompt, args, few_shot=None):
    # Sử dụng biến đếm lùi để kiểm soát số lần thử
    retry_count = 0
    max_retry_num = args.max_retry_num
    
    url = "https://api.openai.com/v1/chat/completions"
    
    # Loại bỏ dấu ngoặc kép thừa từ API Key nếu nó được truyền từ file .bat
    api_key = args.api_key.strip('"') if args.api_key else ""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Insert few-shot examples if provided
    if few_shot is not None:
        if isinstance(few_shot, list):
            messages.extend(few_shot)
        elif isinstance(few_shot, str):
            messages.append({"role": "user", "content": few_shot})
        else:
            messages.append({"role": "user", "content": str(few_shot)})

    # finally add the current user prompt
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": args.model, 
        "messages": messages,
        "temperature": args.temperature,
    }
    
    # Thay đổi logic vòng lặp để sử dụng retry_count
    while retry_count < max_retry_num:
        request_result = None
        try:
            request_result = requests.post(url, headers=headers, json=payload, timeout=30) # Thêm timeout
            
            # KIỂM TRA LỖI TRỰC TIẾP TỪ HTTP STATUS CODE (4XX, 5XX)
            if request_result.status_code != 200:
                result_json = request_result.json()
                error_message = result_json.get('error', {}).get('message', f"Unknown HTTP error {request_result.status_code}")
                
                # IN LỖI CHI TIẾT VÀ TĂNG BIẾN ĐẾM
                print(f"[ERROR] API Call Failed (Status: {request_result.status_code}, Retry: {retry_count+1}/{max_retry_num}): {error_message}")
                
                # NẾU LỖI LÀ DO API KEY (401), THOÁT NGAY
                if request_result.status_code == 401:
                    print("[FATAL] API Key Unauthorized (401). Exiting retries.")
                    return None
                    
                raise Exception(error_message) # Bắt buộc vào khối except để xử lý retry
                
            # XỬ LÝ KHI STATUS CODE LÀ 200
            result_json = request_result.json()
            if 'error' not in result_json: 
                model_output = result_json['choices'][0]['message']['content']
                return model_output.strip()
            else:
                # Xử lý lỗi API (ví dụ: lỗi nội bộ của OpenAI) Mặc dù status_code=200, trường 'error' vẫn có thể tồn tại
                error_message = result_json.get('error', {}).get('message', "Internal API error with 'error' field.")
                print(f"[ERROR] API Response Error (Retry: {retry_count+1}/{max_retry_num}): {error_message}")
                raise Exception(error_message) # Bắt buộc vào khối except để xử lý retry

        except requests.exceptions.Timeout:
            print(f"[WARNING] Request Timeout (Retry: {retry_count+1}/{max_retry_num}). Retrying...")
            
        except requests.exceptions.RequestException as req_e:
            # Bắt lỗi kết nối, DNS, SSL, v.v.
            print(f"[WARNING] Network/Connection Error (Retry: {retry_count+1}/{max_retry_num}): {req_e}")
            
        except Exception as e:
            # Bắt các lỗi khác (lỗi JSON decode, lỗi từ khối if request_result.status_code != 200)
            print(f"[WARNING] General Error (Retry: {retry_count+1}/{max_retry_num}): {e}")
            
        
        # TĂNG BIẾN ĐẾM VÀ CHỜ (BACKOFF)
        retry_count += 1
        if retry_count < max_retry_num:
             # Sử dụng backoff theo lũy thừa (1s, 2s, 4s, 8s, ...)
            time.sleep(min(2 ** retry_count, 10)) 
        
    return None
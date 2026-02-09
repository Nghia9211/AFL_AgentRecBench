import time
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.regular_function import split_user_response, split_rec_reponse_top_n 
from utils.agent import RecAgent, UserModelAgent 

def error_handler(e):
    print(f"!!! LỖI TRONG TIẾN TRÌNH CON: {e}")
    import traceback
    traceback.print_exc()

def recommend(data, args):
    rec_agent = RecAgent(args, 'prior_rec')
    user_agent = UserModelAgent(args, 'prior_rec')
    
    flag = False 
    epoch = 1    
    rec_item_list = [] 
    new_data_list = []
    hit_at_n = {1: False, 3: False, 5: False}

    while flag == False and epoch <= args.max_epoch:
        # --- Rec Agent ---
        while True:
            rec_agent_response = rec_agent.act(data)
            if rec_agent_response is None:
                time.sleep(5)
                continue
            rec_reason, current_rec_list = split_rec_reponse_top_n(rec_agent_response) 
            if current_rec_list: 
                rec_item_list = current_rec_list 
                break
            time.sleep(1)

        # --- User Agent ---
        while True:
            user_agent_response = user_agent.act(data, rec_reason, rec_item_list) 
            user_reason, flag = split_user_response(user_agent_response)
            if user_reason is not None and flag is not None:
                break
            time.sleep(1)
            
        current_step_data = {
            'id': data['id'], 'epoch': epoch, 
            'rec_res': rec_agent_response, 'user_res': user_agent_response,
            'rec_items': rec_item_list, 'flag': flag 
        }
        new_data_list.append(current_step_data)

        if flag:
            gt_name = data.get('correct_answer', '').lower().strip()
            current_top_n_lower = [item.lower().strip() for item in rec_item_list]
            if gt_name in current_top_n_lower:
                rank = current_top_n_lower.index(gt_name) + 1
                if rank <= 1: hit_at_n[1] = True
                if rank <= 3: hit_at_n[3] = True
                if rank <= 5: hit_at_n[5] = True
            break

        rec_agent.update_memory({"epoch": epoch, "rec_reason": rec_reason, "rec_item_list": rec_item_list, "user_reason": user_reason})
        user_agent.update_memory({"epoch": epoch, "rec_reason": rec_reason, "rec_item_list": rec_item_list, "user_reason": user_reason})
        epoch += 1
    
    return new_data_list, hit_at_n, args
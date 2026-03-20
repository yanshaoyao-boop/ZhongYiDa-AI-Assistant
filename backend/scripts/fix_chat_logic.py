import os

file_path = r"d:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\backend\routers\chat.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 修改 1：意图识别加固
for i, line in enumerate(lines):
    if "intent, request.message = await classify_intent" in line:
        old_indent = line[:line.find("intent")]
        lines[i] = f"{old_indent}try:\n{old_indent}    intent, request.message = await classify_intent(request.message, request.history)\n{old_indent}except Exception as e:\n{old_indent}    print(f'Intent Error: {{e}}')\n{old_indent}    intent = 'document'\n"
        break

# 修改 2：RAG 逻辑加固和阈值放宽
for i, line in enumerate(lines):
    if "query_embedding = await get_embedding(search_query)" in line and "try:" not in lines[i-1]:
        old_indent = line[:line.find("query_embedding")]
        lines[i] = f"{old_indent}try:\n{old_indent}    query_embedding = await get_embedding(search_query)\n{old_indent}    top_k = int(get_config('ai_search_top_k', '5'))\n{old_indent}    similar_docs = await asyncio.to_thread(search_similar_documents, query_embedding, top_k)\n{old_indent}except Exception as e:\n{old_indent}    print(f'RAG Search failed: {{e}}')\n{old_indent}    similar_docs = []\n"
        # 同时清理掉后面原本重复的检索逻辑
        j = i + 1
        while j < len(lines) and ("top_k = int" in lines[j] or "search_similar_documents" in lines[j]):
            lines[j] = ""
            j += 1
    
    # 修改 3：放宽检索阈值 (0.58 -> 0.65)
    if "best_distance > 0.58" in line:
        lines[i] = line.replace("0.58", "0.65")

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Modification successful: Chat.py reinforced and RAG threshold loosened.")

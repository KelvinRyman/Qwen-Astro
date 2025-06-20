# ============================
#  1. 初始化和清理
# ============================
Write-Host "--- 1. Initializing & Cleaning Up ---" -ForegroundColor Yellow
$apiUrl = "http://127.0.0.1:5000/api"

# 获取并删除所有现有的组
$existingGroups = Invoke-RestMethod -Uri "$apiUrl/groups" -Method Get
foreach ($group in $existingGroups) {
    Write-Host "🗑️ Deleting existing group: $($group.name)"
    Invoke-RestMethod -Uri "$apiUrl/groups/$($group.id)" -Method Delete
}

# 获取并删除所有现有的会话
$existingConvs = Invoke-RestMethod -Uri "$apiUrl/conversations" -Method Get
foreach ($conv in $existingConvs) {
    Write-Host "🗑️ Deleting existing conversation: $($conv.title)"
    Invoke-RestMethod -Uri "$apiUrl/conversations/$($conv.id)" -Method Delete
}
Write-Host "✅ Cleanup complete."

# ============================
#  2. 创建知识库并添加文件
# ============================
Write-Host "`n--- 2. Creating Knowledge Base & Adding File ---" -ForegroundColor Yellow

# 创建一个新组
$groupBody = @{ name = "Test Docs"; description = "A group for end-to-end testing." } | ConvertTo-Json
$group = Invoke-RestMethod -Uri "$apiUrl/groups" -Method Post -Body $groupBody -ContentType "application/json"
$groupId = $group.id
Write-Host "✅ Created group 'Test Docs' with ID: $groupId"

# 上传文件到该组
Write-Host "📤 Uploading 'test.txt' to the group..."
Invoke-RestMethod -Uri "$apiUrl/groups/$groupId/files" -Method Post -Form @{ files = Get-Item -Path "./test.txt" }
Write-Host "⏳ Waiting for indexing..."
Start-Sleep -Seconds 5 # 等待索引

# ============================
#  3. 测试无状态和有状态对话
# ============================
Write-Host "`n--- 3. Testing Stateless and Stateful Chat ---" -ForegroundColor Yellow

# 3.1. 无状态查询 (RAG Query)
Write-Host "❓ Testing Stateless RAG Query..."
$statelessBody = @{
    query_text = "What does the fox do?"
    group_ids  = @($groupId)
} | ConvertTo-Json
$statelessResponse = Invoke-RestMethod -Uri "$apiUrl/query" -Method Post -Body $statelessBody -ContentType "application/json"
Write-Host "🤖 Stateless Answer: $($statelessResponse.answer)"

# 3.2. 有状态对话 (Stateful Chat)
# 创建一个新会话
$conversation = Invoke-RestMethod -Uri "$apiUrl/conversations" -Method Post
$convId = $conversation.id
Write-Host "✅ Created a new conversation with ID: $convId"

# 第一个问题: 纯聊天 (无 RAG)
Write-Host "💬 Stateful Chat (No RAG): Asking a general question..."
$chatBody1 = @{ query_text = "What is 2+2?" } | ConvertTo-Json
$chatResponse1 = Invoke-RestMethod -Uri "$apiUrl/conversations/$convId/messages" -Method Post -Body $chatBody1 -ContentType "application/json"
Write-Host "🤖 Chatbot Answer (No RAG): $($chatResponse1.answer.content)"

# 第二个问题: RAG 聊天
Write-Host "💬 Stateful Chat (With RAG): Asking about the document..."
$chatBody2 = @{
    query_text = "What animal is mentioned in my document?"
    group_ids  = @($groupId)
} | ConvertTo-Json
$chatResponse2 = Invoke-RestMethod -Uri "$apiUrl/conversations/$convId/messages" -Method Post -Body $chatBody2 -ContentType "application/json"
Write-Host "🤖 Chatbot Answer (With RAG): $($chatResponse2.answer.content)"

# ============================
#  4. 最终清理
# ============================
Write-Host "`n--- 4. Final Cleanup ---" -ForegroundColor Yellow

# 删除测试组
Write-Host "🗑️ Deleting group 'Test Docs'..."
Invoke-RestMethod -Uri "$apiUrl/groups/$groupId" -Method Delete

# 删除测试会话
Write-Host "🗑️ Deleting test conversation..."
Invoke-RestMethod -Uri "$apiUrl/conversations/$convId" -Method Delete

Write-Host "🎉 Test flow complete and all resources cleaned up." -ForegroundColor Green

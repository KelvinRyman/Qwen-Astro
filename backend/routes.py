import os
import uuid
import threading
from flask import Blueprint, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError, Field

from .models import (
    LegacyChatMessageRequest,
    GroupCreateRequest,
    QueryRequest,
    QueryResponse,
    SourceNodeModel,
    SourcesDeleteRequest,
    WebImportRequest,
    AskRequest,
    WebpagesDeleteRequest,
    FilesDeleteRequest,
    WebpagesAddRequest,
    ConversationCreationRequest,
    MessagePostRequest,
    ConversationRenameRequest,
    MessagesDeleteRequest,
    MessageRegenerateRequest,
    ConversationGroupsUpdateRequest,
)
from rag_engine import RAGPipeline


api = Blueprint("api", __name__, url_prefix="/api")


def get_rag_pipeline() -> RAGPipeline:
    """
    获取 RAGPipeline 实例，确保只创建一次。
    """
    return current_app.rag_pipeline


@api.errorhandler(ValidationError)
def handle_validation_error(error: ValidationError):
    """
    处理 Pydantic 验证错误。
    """
    return jsonify({"error": "无效的请求数据", "details": error.errors()}), 400


@api.errorhandler(Exception)
def handle_generic_error(error: Exception):
    """
    处理所有其他异常。
    """
    if isinstance(error, HTTPException):
        return error  # 直接返回 HTTP 异常
    # 只有是真正的未知异常时才记录为 500 错误
    current_app.logger.error(f"发生错误: {error}", exc_info=True)
    return jsonify({"error": "服务器内部错误"}), 500


# --- 组管理相关路由 ---


@api.route("/groups", methods=["POST"])
def create_group():
    """创建一个新的组"""
    try:
        data = GroupCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    pipeline = get_rag_pipeline()
    group = pipeline.group_manager.create_group(data.name, data.description)

    if group:
        return jsonify(group), 201
    else:
        return jsonify({"error": f"名为 '{data.name}' 的组已存在。"}), 409


@api.route("/groups", methods=["GET"])
def list_groups():
    """列出所有可用的组"""
    pipeline = get_rag_pipeline()
    groups = pipeline.list_all_groups()
    return jsonify(groups), 200


@api.route("/groups/<group_id>", methods=["DELETE"])
def delete_group(group_id: str):
    """
    完全删除一个知识库组和所有相关数据。
    这是一项不可逆操作。

    Keyword arguments:
    group_id -- 组的唯一标识符
    Return: 返回是否成功删除组
    """
    pipeline = get_rag_pipeline()

    # 验证组是否存在（虽然引擎内部也做，但在API层先做可以提供更快的反馈）
    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"Group with ID '{group_id}' not found."}), 404

    try:
        success = pipeline.delete_group(group_id)
        if success:
            return (
                jsonify(
                    {
                        "message": f"Group with ID '{group_id}' has been successfully deleted."
                    }
                ),
                200,
            )
        else:
            # 如果返回 False，说明在引擎层面发生了内部错误
            return (
                jsonify(
                    {
                        "error": "An internal error occurred while deleting the group. The system might be in an inconsistent state."
                    }
                ),
                500,
            )
    except Exception as e:
        # 捕获 pipeline 方法中未预料的异常
        current_app.logger.error(
            f"An unexpected error occurred during group deletion for ID {group_id}: {e}",
            exc_info=True,
        )
        return jsonify({"error": "An unexpected server error occurred."}), 500


# --- 文件管理和索引路由 ---


def _index_files_task(app, group_id, files_to_index):
    """
    在后台线程中执行文件索引的函数。
    """
    with app.app_context():
        pipeline = get_rag_pipeline()
        group_dir = pipeline.group_manager.get_group_physical_path(group_id)
        if not group_dir:
            current_app.logger.error(f"无法为组 {group_id} 找到物理路径，索引任务中止。")
            return

        for file_meta in files_to_index:
            file_id = file_meta['id']
            try:
                # 状态已在创建时设为 processing，这里无需更新
                # pipeline.group_manager.update_file_status(group_id, file_id, "processing")
                
                # 为数据处理器准备带有完整物理路径的元数据
                file_meta_with_path = file_meta.copy()
                file_path = os.path.join(group_dir, file_meta["path"])
                
                # 确认文件存在
                if not os.path.exists(file_path):
                    current_app.logger.error(f"文件 {file_path} 在索引时未找到。")
                    pipeline.group_manager.update_file_status(group_id, file_id, "failed")
                    continue

                file_meta_with_path["physical_path"] = file_path

                nodes = pipeline.data_processor.process_data(
                    group_id=group_id, files_meta=[file_meta_with_path]
                )
                if nodes:
                    pipeline.index.insert_nodes(nodes)
                
                pipeline.group_manager.update_file_status(group_id, file_id, "completed")
                current_app.logger.info(f"成功索引文件 ID {file_id}。")

            except Exception as e:
                current_app.logger.error(f"索引文件 ID {file_id} 时失败: {e}", exc_info=True)
                pipeline.group_manager.update_file_status(group_id, file_id, "failed")


def _index_webpages_task(app, group_id, webpages_to_index):
    """
    在后台线程中执行网页索引的函数。
    """
    with app.app_context():
        pipeline = get_rag_pipeline()
        for page_meta in webpages_to_index:
            page_id = page_meta['id']
            try:
                nodes = pipeline.data_processor.process_data(
                    group_id=group_id, webpages_meta=[page_meta]
                )
                if nodes:
                    pipeline.index.insert_nodes(nodes)
                
                pipeline.group_manager.update_webpage_status(group_id, page_id, "completed")
                current_app.logger.info(f"成功索引网页 ID {page_id}。")

            except Exception as e:
                current_app.logger.error(f"索引网页 ID {page_id} 时失败: {e}", exc_info=True)
                pipeline.group_manager.update_webpage_status(group_id, page_id, "failed")


@api.route("/groups/<group_id>/files", methods=["POST"])
def add_files_to_group(group_id: str):
    """
    上传一个或多个文件到指定组。
    此接口会立即返回，并在后台触发索引过程。
    """
    pipeline = get_rag_pipeline()
    group = pipeline.group_manager.get_group_by_id(group_id)
    if not group:
        return jsonify({"error": f"ID 为 '{group_id}' 的组未找到。"}), 404

    if "files" not in request.files:
        return jsonify({"error": "请求中没有文件部分。"}), 400

    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "没有选择文件。"}), 400

    group_dir = pipeline.group_manager.get_group_physical_path(group_id)
    if not group_dir:
        return jsonify({"error": f"无法获取组 '{group['name']}' 的物理路径。"}), 500

    added_files_meta = []
    for file in files:
        if file and file.filename:
            # 保留原始文件名（包括中文），不使用secure_filename
            original_filename = file.filename
            
            # 检查文件名是否已存在于元数据中
            if pipeline.group_manager.get_file_by_name(group_id, original_filename):
                current_app.logger.warning(
                    f"文件名 '{original_filename}' 已存在于组 '{group['name']}' 中，已跳过上传。"
                )
                continue
            
            # 生成文件ID
            file_id = str(uuid.uuid4())
            
            # 获取文件扩展名
            _, file_extension = os.path.splitext(original_filename)
            if not file_extension:
                # 如果没有扩展名，默认为.txt
                file_extension = '.txt'
            
            # 使用ID作为文件名保存
            storage_filename = f"{file_id}{file_extension}"
            destination_path = os.path.join(group_dir, storage_filename)
            
            try:
                file.save(destination_path)
                file_size = os.path.getsize(destination_path)
                
                # 添加元数据，初始状态为 'processing'
                meta = pipeline.group_manager.add_file_meta(
                    group_id, original_filename, file_size, storage_filename, status="processing"
                )
                if meta:
                    added_files_meta.append(meta)
            except Exception as e:
                current_app.logger.error(f"保存文件 '{original_filename}' 失败: {e}", exc_info=True)
                # 可选：如果保存失败，可以决定是否要中止整个批次
                continue
    
    if not added_files_meta:
        return jsonify({"message": "没有新文件被添加（可能已存在或保存失败）。"}), 200

    # 启动后台线程执行索引
    thread = threading.Thread(
        target=_index_files_task, args=(current_app._get_current_object(), group_id, added_files_meta)
    )
    thread.daemon = True
    thread.start()

    return jsonify(added_files_meta), 202


@api.route("/groups/<group_id>/files/<file_id>", methods=["GET"])
def get_file_details(group_id: str, file_id: str):
    """
    获取单个文件的详细信息，包括其索引状态。
    """
    pipeline = get_rag_pipeline()
    file_meta = pipeline.group_manager.get_file_by_id(group_id, file_id)
    if not file_meta:
        return jsonify({"error": "文件未找到。"}), 404
    return jsonify(file_meta)


@api.route("/groups/<group_id>/webpages", methods=["POST"])
def add_webpages_to_group(group_id: str):
    """
    将一个或多个网页URL添加到指定组，并在后台为它们创建索引。
    """
    pipeline = get_rag_pipeline()
    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"ID 为 '{group_id}' 的组未找到。"}), 404

    try:
        data = WebpagesAddRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    added_webpages_meta = []
    for url in data.urls:
        if pipeline.group_manager.get_webpage_by_url(group_id, url):
            current_app.logger.warning(f"URL '{url}' 已存在于组中，已跳过。")
            continue
        
        meta = pipeline.group_manager.add_webpage_meta(group_id, url, status="processing")
        if meta:
            added_webpages_meta.append(meta)

    if not added_webpages_meta:
        return jsonify({"message": "没有新网页被添加（可能已存在）。"}), 200

    # 启动后台线程执行索引
    thread = threading.Thread(
        target=_index_webpages_task, args=(current_app._get_current_object(), group_id, added_webpages_meta)
    )
    thread.daemon = True
    thread.start()

    return jsonify(added_webpages_meta), 202


@api.route("/groups/<group_id>/sources", methods=["GET"])
def list_sources_in_group(group_id: str):
    """
    列出指定组中的所有数据源（文件和网页）。
    """
    pipeline = get_rag_pipeline()
    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"ID 为 '{group_id}' 的组未找到。"}), 404

    sources = pipeline.list_sources_in_group(group_id)
    return jsonify(sources)


@api.route("/groups/<group_id>/files", methods=["DELETE"])
def delete_files_from_group(group_id: str):
    """
    从指定组中删除一个或多个文件。
    """
    pipeline = get_rag_pipeline()
    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"ID 为 '{group_id}' 的组未找到。"}), 404
    try:
        data = FilesDeleteRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    success = pipeline.delete_files_from_group(group_id, data.file_ids)
    if success:
        return jsonify({"message": "指定的文件已成功删除。"}), 200
    else:
        return jsonify({"error": "删除部分或全部文件时出错。"}), 500


@api.route("/groups/<group_id>/webpages", methods=["DELETE"])
def delete_webpages_from_group(group_id: str):
    """
    从指定组中删除一个或多个网页。
    """
    pipeline = get_rag_pipeline()
    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"ID 为 '{group_id}' 的组未找到。"}), 404

    try:
        data = WebpagesDeleteRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    success = pipeline.delete_webpages_from_group(group_id, data.webpage_ids)
    if success:
        return jsonify({"message": "指定的网页已成功删除。"}), 200
    else:
        return jsonify({"error": "删除部分或全部网页时出错。"}), 500


@api.route("/groups/<group_id>/webpages/<webpage_id>", methods=["GET"])
def get_webpage_details(group_id: str, webpage_id: str):
    """
    获取单个网页的详细信息，包括其索引状态。
    """
    pipeline = get_rag_pipeline()
    # 需要在 GroupManager 中添加一个 get_webpage_by_id 的方法
    group = pipeline.group_manager.get_group_by_id(group_id)
    if not group:
        return jsonify({"error": "组未找到。"}), 404
    
    webpage_meta = next((w for w in group.get('webpages', []) if w['id'] == webpage_id), None)
    
    if not webpage_meta:
        return jsonify({"error": "网页未找到。"}), 404
    return jsonify(webpage_meta)


# --- 查询和聊天路由 ---


@api.route("/query", methods=["POST"])
def query_rag():
    """在指定组内执行查询"""
    pipeline = get_rag_pipeline()
    try:
        data = QueryRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    try:
        response = pipeline.query_in_groups(data.query, data.group_ids)

        # 将 LlamaIndex 的响应对象转换为可序列化的 JSON
        source_nodes = []
        try:
            source_nodes = [
                SourceNodeModel.from_source_node(n) for n in response.source_nodes
            ]
        except Exception as e:
            current_app.logger.error(f"处理源节点时出错: {e}", exc_info=True)
            # 如果处理源节点出错，使用空列表
            
        result = QueryResponse(
            answer=str(response),
            sources=source_nodes,
        )

        return result.model_dump_json(), 200
    except Exception as e:
        current_app.logger.error(f"查询处理期间出错: {e}", exc_info=True)
        return jsonify({"error": "处理查询时发生内部错误。"}), 500


@api.route("/conversations", methods=["POST"])
def create_conversation():
    """创建一个新的对话，可以选择关联一个或多个知识库组。"""
    pipeline = get_rag_pipeline()
    try:
        data = ConversationCreationRequest.model_validate(request.json)
    except ValidationError:
        # 如果请求体为空，也视为有效，创建一个无关联的对话
        data = ConversationCreationRequest(group_ids=None)
    
    # 验证所有提供的 group_id 是否都存在
    if data.group_ids:
        all_group_ids = {g["id"] for g in pipeline.list_all_groups()}
        invalid_ids = [gid for gid in data.group_ids if gid not in all_group_ids]
        if invalid_ids:
            return jsonify({"error": "提供的组 ID 无效", "invalid_ids": invalid_ids}), 400

    conversation_id = str(uuid.uuid4())
    conversation = pipeline.conversation_manager.create_conversation(
        conversation_id, data.group_ids
    )
    
    # 确保对话有默认标题
    if "title" not in conversation:
        conversation["title"] = "新对话"
        pipeline.conversation_manager.rename_conversation(conversation_id, "新对话")
    
    return jsonify(conversation), 201


@api.route("/conversations", methods=["GET"])
def list_conversations():
    """列出所有对话的摘要。"""
    pipeline = get_rag_pipeline()
    conversations = pipeline.conversation_manager.list_conversations()
    return jsonify(conversations)


@api.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id: str):
    """获取一个对话的详细信息，包括完整的消息历史。"""
    pipeline = get_rag_pipeline()
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404
    return jsonify(conversation)


@api.route("/conversations/<conversation_id>/messages", methods=["POST"])
def post_message_to_conversation(conversation_id: str):
    """向指定对话发送消息并获取回复。"""
    pipeline = get_rag_pipeline()

    # 1. 验证对话是否存在
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404

    # 2. 验证请求数据
    try:
        data = MessagePostRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    # 3. 准备聊天历史和上下文
    # LlamaIndex 需要的格式是 {'role': 'user'/'assistant', 'content': '...'}
    chat_history = conversation.get("messages", [])
    
    # 4. 确定使用哪些知识库组
    # 如果请求中指定了知识库组，使用请求中的；否则使用会话中保存的
    group_ids = data.group_ids if data.group_ids is not None else conversation.get("group_ids", [])
    
    # 5. 调用 RAG 引擎
    try:
        response = pipeline.chat(
            query_text=data.message,
            chat_history=chat_history,
            group_ids=group_ids,
        )
    except Exception as e:
        current_app.logger.error(f"聊天处理期间出错: {e}", exc_info=True)
        return jsonify({"error": "处理聊天时发生内部错误。"}), 500

    # 6. 保存新的消息到历史记录
    pipeline.conversation_manager.add_message_to_conversation(
        conversation_id, "user", data.message
    )
    pipeline.conversation_manager.add_message_to_conversation(
        conversation_id, "assistant", str(response)
    )

    # 7. 返回响应
    # 安全地处理 source_nodes，因为普通聊天可能没有这个属性
    source_nodes_data = []
    if hasattr(response, "source_nodes") and response.source_nodes:
        try:
            source_nodes_data = [
                SourceNodeModel.from_source_node(n) for n in response.source_nodes
            ]
        except Exception as e:
            current_app.logger.error(f"处理源节点时出错: {e}", exc_info=True)
            # 如果处理源节点出错，返回空列表而不是失败

    result = QueryResponse(
        answer=str(response),
        sources=source_nodes_data,
    )
    return result.model_dump_json(), 200


@api.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id: str):
    """删除一个对话及其所有历史记录。"""
    pipeline = get_rag_pipeline()
    if pipeline.conversation_manager.delete_conversation(conversation_id):
        return jsonify({"message": "对话已成功删除。"}), 200
    else:
        return jsonify({"error": "对话未找到。"}), 404


@api.route("/conversations/<conversation_id>/rename", methods=["POST"])
def rename_conversation(conversation_id: str):
    """重命名一个对话。"""
    pipeline = get_rag_pipeline()
    
    # 验证对话是否存在
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404
    
    # 验证请求数据
    try:
        data = ConversationRenameRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)
    
    # 重命名对话
    if pipeline.conversation_manager.rename_conversation(conversation_id, data.title):
        return jsonify({"message": "对话已成功重命名。"}), 200
    else:
        return jsonify({"error": "重命名对话失败。"}), 500


@api.route("/conversations/search", methods=["GET"])
def search_conversations():
    """根据查询字符串搜索对话。"""
    query = request.args.get("q", "")

    pipeline = get_rag_pipeline()
    if not query.strip():
        # 如果查询为空，返回所有对话
        results = pipeline.conversation_manager.list_conversations()
    else:   # 否则执行搜索
        results = pipeline.conversation_manager.search_conversations(query)
    
    return jsonify(results), 200


@api.route("/conversations/<conversation_id>/messages/stream", methods=["POST"])
def stream_message_to_conversation(conversation_id: str):
    """向指定对话发送消息并获取流式回复。"""
    pipeline = get_rag_pipeline()

    # 1. 验证对话是否存在
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404

    # 2. 验证请求数据
    try:
        data = MessagePostRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    # 3. 准备聊天历史和上下文
    chat_history = conversation.get("messages", [])
    
    # 4. 确定使用哪些知识库组
    # 如果请求中指定了知识库组，使用请求中的；否则使用会话中保存的
    group_ids = data.group_ids if data.group_ids is not None else conversation.get("group_ids", [])

    # 5. 创建流式响应生成器
    def generate():
        try:
            # 注意：这里假设RAG引擎支持流式响应
            # 如果不支持，需要修改RAG引擎或模拟流式响应
            response = pipeline.chat(
                query_text=data.message,
                chat_history=chat_history,
                group_ids=group_ids,
            )
            
            # 保存用户消息到历史记录
            pipeline.conversation_manager.add_message_to_conversation(
                conversation_id, "user", data.message
            )
            
            # 模拟流式输出（实际实现应该从LLM获取流式输出）
            answer = str(response)
            source_nodes = []
            if hasattr(response, "source_nodes") and response.source_nodes:
                try:
                    source_nodes = [
                        SourceNodeModel.from_source_node(n) for n in response.source_nodes
                    ]
                except Exception as e:
                    current_app.logger.error(f"处理源节点时出错: {e}", exc_info=True)
                    # 如果处理源节点出错，使用空列表
            
            # 保存助手消息到历史记录
            pipeline.conversation_manager.add_message_to_conversation(
                conversation_id, "assistant", answer
            )
            
            # 构建完整响应
            full_response = QueryResponse(
                answer=answer,
                sources=source_nodes,
            )

            # 返回JSON格式的完整响应
            yield full_response.model_dump_json()
            
        except Exception as e:
            current_app.logger.error(f"流式聊天处理期间出错: {e}", exc_info=True)
            yield jsonify({"error": "处理聊天时发生内部错误。"}).get_data(as_text=True)

    # 设置响应头并返回流式响应
    return Response(generate(), mimetype='application/json')


@api.route("/conversations/<conversation_id>/regenerate/stream", methods=["POST"])
def regenerate_message_stream(conversation_id: str):
    """流式重新生成助手消息。"""
    pipeline = get_rag_pipeline()

    # 1. 验证对话是否存在
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404

    # 2. 验证请求数据
    try:
        data = MessageRegenerateRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    # 3. 验证消息索引是否有效
    messages = conversation.get("messages", [])
    if data.from_message_index < 1 or data.from_message_index >= len(messages):
        return jsonify({"error": "无效的消息索引。"}), 400

    # 4. 确保要重新生成的消息是助手消息
    if messages[data.from_message_index]["role"] != "assistant":
        return jsonify({"error": "只能重新生成助手消息。"}), 400

    # 5. 找到前一条用户消息
    user_message_index = data.from_message_index - 1
    if user_message_index < 0 or messages[user_message_index]["role"] != "user":
        return jsonify({"error": "找不到对应的用户消息。"}), 400

    user_message = messages[user_message_index]["content"]

    # 6. 准备聊天历史（只包含到用户消息之前的历史）
    chat_history = messages[:user_message_index]
    
    # 7. 获取知识库组ID
    group_ids = conversation.get("group_ids", [])

    # 8. 创建流式响应生成器
    def generate():
        try:
            # 重新生成回复
            response = pipeline.chat(
                query_text=user_message,
                chat_history=chat_history,
                group_ids=group_ids,
            )
            
            # 更新助手消息
            pipeline.conversation_manager.delete_messages_from_index(
                conversation_id, user_message_index
            )
            pipeline.conversation_manager.add_message_to_conversation(
                conversation_id, "user", user_message
            )
            pipeline.conversation_manager.add_message_to_conversation(
                conversation_id, "assistant", str(response)
            )
            
            # 构建响应
            source_nodes = []
            if hasattr(response, "source_nodes") and response.source_nodes:
                try:
                    source_nodes = [
                        SourceNodeModel.from_source_node(n) for n in response.source_nodes
                    ]
                except Exception as e:
                    current_app.logger.error(f"处理源节点时出错: {e}", exc_info=True)
                    # 如果处理源节点出错，使用空列表
            
            # 构建完整响应
            full_response = QueryResponse(
                answer=str(response),
                sources=source_nodes,
            )
            
            # 返回JSON格式的完整响应
            yield full_response.model_dump_json()
            
        except Exception as e:
            current_app.logger.error(f"重新生成消息期间出错: {e}", exc_info=True)
            yield jsonify({"error": "处理重新生成请求时发生内部错误。"}).get_data(as_text=True)

    # 设置响应头并返回流式响应
    return Response(generate(), mimetype='application/json')


@api.route("/conversations/<conversation_id>/messages", methods=["DELETE"])
def delete_messages_from_conversation(conversation_id: str):
    """删除指定对话中从特定索引开始的所有消息。"""
    pipeline = get_rag_pipeline()

    # 验证对话是否存在
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404
    
    # 验证请求数据
    try:
        data = MessagesDeleteRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)
    
    # 删除消息
    if pipeline.conversation_manager.delete_messages_from_index(conversation_id, data.from_index):
        return jsonify({"message": "消息已成功删除。"}), 200
    else:
        return jsonify({"error": "删除消息失败。"}), 400


@api.route("/conversations/<conversation_id>/groups", methods=["POST"])
def update_conversation_groups(conversation_id: str):
    """更新对话关联的知识库组。"""
    pipeline = get_rag_pipeline()
    
    # 验证对话是否存在
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "对话未找到。"}), 404
    
    # 验证请求数据
    try:
        data = ConversationGroupsUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)
    
    # 验证所有提供的 group_id 是否都存在
    if data.group_ids:
        all_group_ids = {g["id"] for g in pipeline.list_all_groups()}
        invalid_ids = [gid for gid in data.group_ids if gid not in all_group_ids]
        if invalid_ids:
            return jsonify({"error": "提供的组 ID 无效", "invalid_ids": invalid_ids}), 400
    
    # 更新对话关联的知识库组
    conversation["group_ids"] = data.group_ids
    
    # 保存更新后的对话
    with open(pipeline.conversation_manager._get_conv_path(conversation_id), "w", encoding="utf-8") as f:
        import json
        json.dump(conversation, f, indent=4)
    
    return jsonify({"message": "对话关联知识库组已更新。"}), 200

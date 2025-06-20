import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError

from .models import (
    ChatMessageRequest,
    GroupCreateRequest,
    QueryRequest,
    QueryResponse,
    SourceNodeModel,
    SourcesDeleteRequest,
    WebImportRequest,
    AskRequest,
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


@api.route("/groups/<group_id>/files", methods=["POST"])
def add_data_to_group(group_id: str):
    """
    上传文件到指定组并触发索引过程

    Keyword arguments:
    group_id -- 组的 ID
    Return: 上传和索引是否成功
    """
    pipeline = get_rag_pipeline()

    # 1. 验证组是否存在
    group = pipeline.group_manager.get_group_by_id(group_id)
    if not group:
        return jsonify({"error": f"ID 为 '{group_id}' 的组未找到。"}), 404

    content_type = request.content_type

    if content_type and "multipart/form-data" in content_type.lower():
        # 2. 检查是否有文件上传
        if "files" not in request.files:
            return jsonify({"error": "请求中没有文件部分。"}), 400

        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            return jsonify({"error": "没有选择文件。"}), 400

        # 3. 保存文件到临时目录
        temp_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(temp_dir, exist_ok=True)

        saved_file_paths = []
        for file in files:
            if file and file.filename:
                # 使用 UUID 避免文件名冲突
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                temp_path = os.path.join(temp_dir, unique_filename)
                file.save(temp_path)
                saved_file_paths.append(temp_path)

        if not saved_file_paths:
            return jsonify({"error": "没有有效的文件被保存。"}), 400

        try:
            # 4. 调用引擎处理文件并索引
            pipeline.add_and_index_data(group_id, file_paths=saved_file_paths)

            return (
                jsonify(
                    {
                        "message": f"成功上传了 {len(saved_file_paths)} 个文件到组 '{group['name']}' 并触发了索引。"
                    }
                ),
                202,
            )  # 202 Accepted 表示请求已接受，正在处理

        finally:
            # 5. 清理临时文件
            for path in saved_file_paths:
                os.remove(path)

    elif content_type and "application/json" in content_type.lower():
        try:
            data = WebImportRequest.model_validate(request.json)
            pipeline.add_and_index_data(group_id, urls=[data.url])
            return (
                jsonify(
                    {
                        "message": f"成功导入网页 {data.url} 到组 '{group['name']}' 并触发了索引。"
                    }
                ),
                202,
            )
        except ValidationError as e:
            return handle_validation_error(e)
    else:
        return jsonify({"error": "不支持的内容类型"}), 415


@api.route("groups/<group_id>/sources", methods=["DELETE"])
def delete_sources(group_id: str):
    """
    从指定组中删除数据源

    Keyword arguments:
    group_id -- 组的 ID
    Return: 操作是否成功
    """
    """从组中删除指定的数据源"""
    pipeline = get_rag_pipeline()

    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"Group with ID '{group_id}' not found."}), 404

    try:
        data = SourcesDeleteRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    success = pipeline.delete_sources_from_group(group_id, data.sources)

    if success:
        return (
            jsonify({"message": "Specified sources have been successfully deleted."}),
            200,
        )
    else:
        return (
            jsonify({"error": "An error occurred while deleting some of the sources."}),
            500,
        )


# --- 查询路由 ---


@api.route("/query", methods=["POST"])
def query_rag():
    """在指定组内执行查询"""
    try:
        data = QueryRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    pipeline = get_rag_pipeline()

    # 验证所有请求的 group_id 是否都存在
    all_groups = pipeline.list_all_groups()
    all_group_ids = {g["id"] for g in all_groups}
    invalid_ids = [gid for gid in data.group_ids if gid not in all_group_ids]
    if invalid_ids:
        return (
            jsonify({"error": "提供的组 ID 无效", "invalid_ids": invalid_ids}),
            400,
        )

    try:
        response = pipeline.query_in_groups(data.query_text, data.group_ids)

        # 将引擎的响应格式化为我们的 API 模型
        source_nodes = []
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node_with_score in response.source_nodes:
                metadata = node_with_score.node.metadata
                source_nodes.append(
                    SourceNodeModel(
                        score=node_with_score.score,
                        group_id=metadata.get("group_id", "N/A"),
                        file_name=metadata.get("file_name", "N/A"),
                        page_label=metadata.get("page_label", "N/A"),
                        text_snippet=node_with_score.node.text[:250].strip() + "...",
                    )
                )

        api_response = QueryResponse(answer=str(response), source_nodes=source_nodes)
        return jsonify(api_response.model_dump()), 200

    except Exception as e:
        current_app.logger.error(f"查询处理期间出错: {e}", exc_info=True)
        return jsonify({"error": "查询处理失败。"}), 500


@api.route("groups/<group_id>/sources", methods=["GET"])
def list_sources(group_id: str):
    """
    列出指定组内所有的数据源。

    Keyword arguments:
    group_id -- 组的 ID
    Return: 数据源列表
    """
    pipeline = get_rag_pipeline()

    if not pipeline.group_manager.get_group_by_id(group_id):
        return jsonify({"error": f"Group with ID '{group_id}' not found."}), 404

    sources = pipeline.list_sources_in_group(group_id)
    return jsonify(sources), 200


# --- 历史会话相关路由 ---


@api.route("/conversations", methods=["POST"])
def create_conversation():
    """创建一个新的空会话"""
    pipeline = get_rag_pipeline()
    conversation_meta = pipeline.conversation_manager.create_conversation()
    return jsonify(conversation_meta), 201


@api.route("/conversations", methods=["GET"])
def list_conversations():
    """列出所有会话"""
    pipeline = get_rag_pipeline()
    conversations = pipeline.conversation_manager.list_conversations()
    return jsonify(conversations), 200


@api.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id: str):
    """获取指定会话的详情"""
    pipeline = get_rag_pipeline()
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if conversation:
        return jsonify(conversation), 200
    else:
        return jsonify({"error": "会话未找到"}), 404


@api.route("/conversations/<conversation_id>/messages", methods=["POST"])
def post_message_to_conversation(conversation_id: str):
    """在会话中发送新消息并获取回复"""
    pipeline = get_rag_pipeline()

    # 1. 验证请求体
    try:
        data = ChatMessageRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    # 2. 获取当前会话历史
    conversation = pipeline.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "会话未找到"}), 404
    chat_history = conversation["messages"]

    # 3. 调用聊天方法
    response = pipeline.chat(data.query_text, chat_history, data.group_ids)

    # 4. 保存用户消息和AI回复到历史记录
    user_message = {"role": "user", "content": data.query_text}
    ai_response_content = response.response if hasattr(response, "response") else "抱歉，我暂时无法回答这个问题。"
    assistant_message = {"role": "assistant", "content": ai_response_content}

    pipeline.conversation_manager.add_message_to_conversation(
        conversation_id, user_message
    )
    pipeline.conversation_manager.add_message_to_conversation(
        conversation_id, assistant_message
    )

    # 5. 格式化并返回响应
    # (为了简化，我们直接返回 assistant_message)
    # 我们可以返回更完整的响应，包括源节点
    api_response = {
        "answer": assistant_message,
        "source_nodes": (
            [
                SourceNodeModel.model_validate(
                    {
                        "score": node.score,
                        "group_id": node.node.metadata.get("group_id", "N/A"),
                        "file_name": node.node.metadata.get("file_name", "N/A"),
                        "page_label": node.node.metadata.get("page_label", "N/A"),
                        "text_snippet": node.node.text[:250].strip() + "...",
                    }
                ).model_dump()
                for node in response.source_nodes
            ]
            if hasattr(response, "source_nodes")
            else []
        ),
    }
    return jsonify(api_response), 200


@api.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id: str):
    """删除一个会话"""
    pipeline = get_rag_pipeline()
    if pipeline.conversation_manager.delete_conversation(conversation_id):
        return jsonify({"message": "会话已删除"}), 200
    else:
        return jsonify({"error": "会话未找到"}), 404


@api.route("/conversations/search", methods=["GET"])
def search_conversations():
    """搜索会话内容"""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "需要提供查询参数 'q'"}), 400

    pipeline = get_rag_pipeline()
    results = pipeline.conversation_manager.search_conversations(query)
    return jsonify(results), 200


# --- 向后兼容的问答路由 ---
legacy_api = Blueprint("legacy_api", __name__, url_prefix="/api")


def get_default_group(pipeline: RAGPipeline) -> str:
    """
    获取默认组 ID，如果没有组则创建一个。
    """
    default_group_name = "default"
    group = pipeline.group_manager.get_group_by_name(default_group_name)
    if not group:
        group = pipeline.group_manager.create_group(
            default_group_name, "Default group for legacy uploads"
        )
    return group


@legacy_api.route("/ask", methods=["POST"])
def legacy_ask_question():
    """旧的 /ask 路由"""
    pipeline = get_rag_pipeline()
    try:
        data = AskRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    # 如果没有提供 group_ids，则使用默认组
    if not data.group_ids:
        all_groups = pipeline.list_all_groups()
        group_ids = [g["id"] for g in all_groups]
        if not group_ids:
            return jsonify(
                {
                    "answer": "知识库为空，请先添加数据。",
                }
            )
    else:
        group_ids = data.group_ids

    # 调用与新 /query 相同的逻辑
    response = pipeline.query_in_groups(data.question, group_ids)

    # 只返回简单答案以保持兼容性
    return jsonify({"answer": str(response)})


@legacy_api.route("/import/web", methods=["POST"])
def legacy_import_web():
    """兼容旧的 /import/web 路由"""
    pipeline = get_rag_pipeline()
    try:
        data = WebImportRequest.model_validate(request.json)
    except ValidationError as e:
        return handle_validation_error(e)

    group = get_default_group(pipeline)
    pipeline.add_and_index_data(group_id=group["id"], urls=[data.url])

    return jsonify({"message": "导入成功"}), 202


@legacy_api.route("/upload", methods=["POST"])
def legacy_upload_file():
    """兼容旧的 /upload 路由"""
    pipeline = get_rag_pipeline()

    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "没有选择文件"}), 400

    group = get_default_group(pipeline)
    temp_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(temp_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")
    file.save(temp_path)

    try:
        pipeline.add_and_index_data(group_id=group["id"], file_paths=[temp_path])
        return jsonify({"message": "上传成功"}), 202
    finally:
        os.remove(temp_path)


@legacy_api.route("/knowledge", methods=["GET"])
def legacy_get_knowledge():
    """
    兼容旧的 /knowledge 路由。
    这个路由现在变得有些模糊。一个合理的实现是返回所有组及其包含的文件列表。
    这是一个新功能，需要我们在 GroupManager 中添加对文件列表的跟踪。
    **简化实现**：为保持简单，我们返回组列表作为知识的顶级分类。
    """
    pipeline = get_rag_pipeline()
    groups = pipeline.list_all_groups()
    # 格式化为旧的 knowledge_base 格式
    knowledge_base = [
        {
            "id": i + 1,
            "name": g["name"],
            "type": "group",
            "content": g["description"],
            "date": "N/A",  # 日期信息在新架构中不再直接跟踪
        }
        for i, g in enumerate(groups)
    ]
    return jsonify(knowledge_base)


@legacy_api.route("/knowledge/<knowledge_id>", methods=["DELETE"])
def legacy_delete_knowledge(knowledge_id):
    """
    兼容旧的 /knowledge/<id> 路由，现在映射到删除一个组。
    注意：旧的 knowledge_id 是一个自增整数，而新的则是UUID。
    我们需要一个映射机制。最简单的兼容方式是按顺序查找。
    """
    pipeline = get_rag_pipeline()
    # 按名称排序以获得一个确定性的列表
    groups = sorted(pipeline.list_all_groups(), key=lambda x: x["name"])

    if not (1 <= knowledge_id <= len(groups)):
        return jsonify({"error": f"Knowledge ID {knowledge_id} is out of bounds."}), 404

    group_to_delete = groups[knowledge_id - 1]
    group_id_to_delete = group_to_delete["id"]

    current_app.logger.warning(
        f"Legacy API call to delete knowledge ID {knowledge_id}, which maps to group '{group_to_delete['name']}' (ID: {group_id_to_delete})."
    )

    # 调用与新 API 相同的删除逻辑
    success = pipeline.delete_group_completely(group_id_to_delete)
    if success:
        return jsonify({"message": "删除成功"}), 200
    else:
        return jsonify({"error": "删除组时发生内部错误。"}), 500

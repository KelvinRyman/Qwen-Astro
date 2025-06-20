from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import PyPDF2
import markdown
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 配置文件上传目录
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 知识库数据存储
KNOWLEDGE_BASE_FILE = "knowledge_base.json"
if not os.path.exists(KNOWLEDGE_BASE_FILE):
    with open(KNOWLEDGE_BASE_FILE, "w") as f:
        json.dump([], f)


def load_knowledge_base():
    with open(KNOWLEDGE_BASE_FILE, "r") as f:
        return json.load(f)


def save_knowledge_base(data):
    with open(KNOWLEDGE_BASE_FILE, "w") as f:
        json.dump(data, f)


@app.route("/api/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question")

    # TODO: 实现实际的问答逻辑
    # 这里只是一个示例响应
    return jsonify({"answer": f"这是一个示例回答。您的问题是：{question}"})


@app.route("/api/import/web", methods=["POST"])
def import_web():
    data = request.json
    url = data.get("url")

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()

        # 保存到知识库
        knowledge_base = load_knowledge_base()
        knowledge_base.append(
            {
                "id": len(knowledge_base) + 1,
                "name": url,
                "type": "web",
                "content": text,
                "date": str(datetime.now()),
            }
        )
        save_knowledge_base(knowledge_base)

        return jsonify({"message": "导入成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "没有选择文件"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # 根据文件类型提取文本
        text = ""
        if filename.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        elif filename.endswith(".pdf"):
            with open(filepath, "rb") as f:
                pdf = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
        elif filename.endswith(".md"):
            with open(filepath, "r", encoding="utf-8") as f:
                md_text = f.read()
                text = markdown.markdown(md_text)

        # 保存到知识库
        knowledge_base = load_knowledge_base()
        knowledge_base.append(
            {
                "id": len(knowledge_base) + 1,
                "name": filename,
                "type": filename.split(".")[-1],
                "content": text,
                "date": str(datetime.now()),
            }
        )
        save_knowledge_base(knowledge_base)

        return jsonify({"message": "上传成功"})


@app.route("/api/knowledge", methods=["GET"])
def get_knowledge():
    knowledge_base = load_knowledge_base()
    return jsonify(knowledge_base)


@app.route("/api/knowledge/<int:knowledge_id>", methods=["DELETE"])
def delete_knowledge(knowledge_id):
    knowledge_base = load_knowledge_base()
    knowledge_base = [k for k in knowledge_base if k["id"] != knowledge_id]
    save_knowledge_base(knowledge_base)
    return jsonify({"message": "删除成功"})


if __name__ == "__main__":
    app.run(debug=True)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAPI 文档解析脚本
从 TinyAPI 的 OpenAPI JSON 文件自动生成/更新 config/apis.json

功能：
- 读取 OpenAPI JSON（默认路径 C:/Users/admin/Desktop/json-format.json）
- 跳过已存在的 path（不修改已有条目）
- 新 API 追加到 apis.json 末尾
- 每个 API 只生成一个关键词，自动去重
- 自动推断 param_types
"""

import json
import os
import re
import sys
import io

# 修复 Windows 终端 UTF-8 打印问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ───────── 路径配置 ─────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OPENAPI_PATH = "C:/Users/admin/Desktop/json-format.json"
APIS_JSON_PATH = os.path.join(SCRIPT_DIR, "config", "apis.json")


# ───────── 参数类型推断 ─────────
def infer_param_type(param_name: str, param_desc: str) -> str:
    """根据参数名和描述推断参数类型"""
    name_lower = param_name.lower()
    desc_lower = (param_desc or "").lower()

    # 图片
    if any(k in name_lower or k in desc_lower for k in ["image", "img", "pic", "photo", "图片"]):
        return "image_url"
    # 音频
    if any(k in name_lower or k in desc_lower for k in ["audio", "music", "sound", "音频", "音乐"]):
        return "audio_url"
    # 视频
    if any(k in name_lower or k in desc_lower for k in ["video", "movie", "film", "视频"]):
        return "video_url"
    # 通用 URL / 链接
    if any(k in name_lower or k in desc_lower for k in ["url", "link", "src", "链接", "地址"]):
        return "url"
    return "text"


# ───────── 关键词生成 ─────────
def generate_keyword(summary: str, path: str, existing: set) -> str:
    """
    为 API 生成一个唯一的关键词。
    策略：
    1. 从 summary 中提取核心短词（去掉「查询/解析/详情」等后缀）
    2. 若冲突，追加序号
    """
    # 去掉常见的冗余后缀
    kw = summary.strip()
    suffixes = [
        "查询", "解析", "详情", "信息", "搜索", "识别", "生成",
        "【高级模型】", "【】", "高级模型",
    ]
    for suf in suffixes:
        kw = kw.replace(suf, "")
    kw = kw.strip()

    # 如果去掉后缀后为空，回退到 summary 的前 4 个字符
    if not kw:
        kw = summary[:4]

    # 去重：若已存在则加数字后缀
    base = kw
    counter = 1
    while kw in existing:
        counter += 1
        kw = f"{base}{counter}"
        # 防止无限循环（极端情况）
        if counter > 999:
            kw = f"{base}_{counter}"
            break

    return kw


# ───────── 主逻辑 ─────────
def main():
    openapi_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OPENAPI_PATH

    if not os.path.isfile(openapi_path):
        print(f"[✗] OpenAPI 文件不存在：{openapi_path}")
        sys.exit(1)

    # 读取 OpenAPI JSON
    with open(openapi_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # 读取现有 apis.json
    if os.path.isfile(APIS_JSON_PATH):
        with open(APIS_JSON_PATH, "r", encoding="utf-8") as f:
            apis_data = json.load(f)
    else:
        apis_data = {"apis": []}

    # 已存在的 path 集合（用于跳过）
    existing_paths = {api.get("path") for api in apis_data["apis"]}
    # 已存在的关键词集合（用于去重）
    existing_keywords = set()
    for api in apis_data["apis"]:
        for kw in api.get("keywords", []):
            existing_keywords.add(kw)

    paths = spec.get("paths", {})
    added = 0
    skipped = 0

    for path, methods in paths.items():
        # 只处理 get / post（TinyAPI 基本都是 get）
        method_data = methods.get("get") or methods.get("post")
        if not method_data:
            continue

        # 跳过已有 path
        if path in existing_paths:
            skipped += 1
            continue

        summary = method_data.get("summary", path)
        description = method_data.get("description", summary)

        # 收集参数（跳过 apikey）
        params = {}
        required_params = []
        param_types = {}

        for param in method_data.get("parameters", []):
            param_name = param.get("name", "")
            if param_name == "apikey":
                continue
            param_desc = param.get("description", "")
            is_required = param.get("required", False)

            params[param_name] = param_desc
            if is_required:
                required_params.append(param_name)

            # 推断参数类型
            ptype = infer_param_type(param_name, param_desc)
            if ptype != "text":  # 只记录非默认类型
                param_types[param_name] = ptype

        # 生成关键词
        keyword = generate_keyword(summary, path, existing_keywords)
        existing_keywords.add(keyword)

        # 构建 API 条目
        entry = {
            "name": summary,
            "path": path,
            "description": description,
            "keywords": [keyword],
            "params": params,
            "required_params": required_params,
        }
        if param_types:
            entry["param_types"] = param_types

        apis_data["apis"].append(entry)
        added += 1
        print(f"[+] 新增：{summary}  (关键词: {keyword}, path: {path})")

    # 写回 apis.json
    with open(APIS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(apis_data, f, ensure_ascii=False, indent=2)
        f.write("\n")  # 末尾换行

    print(f"\n✅ 完成！新增 {added} 个 API，跳过已有 {skipped} 个。")


if __name__ == "__main__":
    main()

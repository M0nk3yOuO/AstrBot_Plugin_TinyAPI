"""
TinyAPI - 调用290+免费API接口
支持文本/图片/音频/视频返回，图片/音频/视频自动识别并直接发送

行为（指令）说明：
- api查询（及别名）  → 查看所有可用关键词列表（直接对Bot说即可触发）
- 关键词快捷调用      → 直接发送关键词调用对应API（无需/前缀）
- 关键词+参数        → 带参数调用（如：火车 北京）

媒体识别：API返回图片/音频/视频URL时，自动识别并直接发送媒体内容
参数校验：缺少必填参数或格式不正确时给出提示
图片接收：支持一条消息同时发送关键词和图片，用于调用需要图片参数的API
"""
import json
import aiohttp
import os
import re
import base64
from typing import Optional, Dict, Any, List
from astrbot.api.star import Context, Star
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api import logger
import astrbot.api.message_components as Comp


# 简单的URL格式判断正则
URL_PATTERN = re.compile(r'^https?://', re.IGNORECASE)

# 媒体URL扩展名集合（小写，无点）
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".ico", ".svg"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".wma"}
VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".3gp"}


class TinyAPIPlugin(Star):
    """TinyAPI聚合插件主类"""

    def __init__(self, context: Context, config: Dict[str, Any]) -> None:
        super().__init__(context)
        self.base_url = config.get("base_url", "https://api.tinyaii.top")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 30)
        self.enable_keyword_match = config.get("enable_keyword_match", True)
        self.enable_llm_rewrite = config.get("enable_llm_rewrite", False)

        # 配置文件路径
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.sites_file = os.path.join(self.config_dir, "sites.json")
        self.apis_file = os.path.join(self.config_dir, "apis.json")

        # 加载配置
        self.sites_config = self._load_json(self.sites_file, {"sites": []})
        self.apis_config = self._load_json(self.apis_file, {"apis": []})

        # 关键词到API路径的映射
        self.keyword_map = self._build_keyword_map()
        # 关键词到完整API信息的映射（含参数类型、必填等）
        self.keyword_api_info = self._build_keyword_api_info()

        logger.info(f"[TinyAPI] 插件加载完成 | api_key已配置: {bool(self.api_key)} | 关键词数: {len(self.keyword_map)} | 关键词匹配: {self.enable_keyword_match}")

    # ========== 配置加载与构建 ==========

    def _load_json(self, file_path: str, default: Dict) -> Dict:
        """加载JSON配置文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败 {file_path}: {e}")
        return default

    def _save_json(self, file_path: str, data: Dict) -> bool:
        """保存JSON配置文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败 {file_path}: {e}")
            return False

    def _build_keyword_map(self) -> Dict[str, str]:
        """构建关键词到API路径的映射"""
        keyword_map = {}
        for api in self.apis_config.get("apis", []):
            keywords = api.get("keywords", [])
            path = api.get("path", "")
            for keyword in keywords:
                keyword_map[keyword.lower()] = path
        return keyword_map

    def _build_keyword_api_info(self) -> Dict[str, Dict]:
        """构建关键词到完整API信息的映射（含参数校验所需信息）"""
        info_map = {}
        for api in self.apis_config.get("apis", []):
            keywords = api.get("keywords", [])
            api_info = {
                "name": api.get("name", "未命名"),
                "path": api.get("path", ""),
                "description": api.get("description", ""),
                "params": api.get("params", {}),
                "required_params": api.get("required_params", []),
                "param_types": api.get("param_types", {}),
            }
            for keyword in keywords:
                info_map[keyword.lower()] = api_info
        return info_map

    def _image_to_base64(self, image_path: str) -> Optional[str]:
        """将图片转换为 base64 编码
        
        Returns:
            base64 编码的字符串（不含前缀），失败返回 None
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                return encoded_string
        except Exception as e:
            logger.error(f"[TinyAPI] 图片转base64失败: {e}")
            return None

    async def _upload_image_to_host(self, image_path: str) -> Optional[str]:
        """将本地图片上传到 TinyAPI 图床，返回公网 URL
        
        对于需要 image_url 参数的 API，如果平台图片 URL 不可用，
        则通过此方法将本地图片上传到图床，拿到稳定公网 URL 再调用 API。
        
        Returns:
            图片的公网 URL，失败返回 None
        """
        if not image_path or not os.path.exists(image_path):
            return None

        upload_url = f"{self.base_url}/v1/image/upload"
        # 先用 GET 方式测试（传本地 file:// 路径不行，必须用 POST 上传文件）
        # TinyAPI 图床接口：POST 上传二进制文件

        try:
            with open(image_path, "rb") as f:
                file_data = f.read()

            async with aiohttp.ClientSession() as session:
                params = {"apikey": self.api_key}
                form = aiohttp.FormData()
                ext = os.path.splitext(image_path)[1].lower()
                content_type = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }.get(ext, "image/jpeg")
                form.add_field(
                    "file",
                    file_data,
                    filename=os.path.basename(image_path),
                    content_type=content_type,
                )

                async with session.post(upload_url, params=params, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    result = await resp.json(content_type=None)

                    # 尝试多种返回格式
                    # 格式1：{"code": 200, "data": {"url": "..."}}
                    # 格式2：{"code": 200, "data": {"imgurl": "..."}}
                    if isinstance(result, dict) and result.get("code") == 200:
                        data_obj = result.get("data")
                        if isinstance(data_obj, dict):
                            img_url = (
                                data_obj.get("url")
                                or data_obj.get("imgurl")
                                or data_obj.get("picurl")
                                or data_obj.get("image")
                            )
                            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                                logger.info(f"[TinyAPI] 图片上传图床成功: {img_url[:80]}")
                                return img_url

                    logger.warning(f"[TinyAPI] 图片上传图床失败: {result}")
                    return None

        except Exception as e:
            logger.error(f"[TinyAPI] 图片上传图床异常: {e}")
            return None

    async def _extract_image_from_event(self, event: AstrMessageEvent) -> Optional[Dict[str, Any]]:
        """从事件中提取图片

        Returns:
            包含图片信息的字典 {"path": 本地路径, "url": 平台图片URL（如有）},
            如果没有图片或失败返回 None
        """
        try:
            for comp in event.message_obj.message:
                if isinstance(comp, Comp.Image):
                    # 优先尝试获取平台原始图片URL（QQ/Telegram等平台发图时自带URL）
                    image_url = getattr(comp, 'url', None)
                    if not image_url or not str(image_url).startswith("http"):
                        image_url = None

                    # 获取本地图片路径（用于 image_file 类型参数 / 图床上传统功能）
                    image_path = await comp.convert_to_file_path()

                    local_path = image_path if (image_path and os.path.exists(image_path)) else None

                    if local_path or image_url:
                        result = {"path": local_path, "url": image_url}
                        logger.info(f"[TinyAPI] 提取图片成功: path={local_path}, url={image_url[:60] if image_url else None}")
                        return result
        except Exception as e:
            logger.error(f"[TinyAPI] 提取图片失败: {e}")

        return None

    # ========== API调用与结果处理 ==========

    async def _call_api(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """调用TinyAPI接口

        无论HTTP状态码如何，都尝试解析服务端返回的JSON。
        如果服务端返回了标准格式（含code字段），以服务端的code为准。
        """
        if not params:
            params = {}

        # 添加API Key
        if self.api_key:
            params["apikey"] = self.api_key

        url = f"{self.base_url}{path}"
        # 日志脱敏：隐藏 apikey 完整值
        safe_params = {k: ("***" if k == "apikey" else v) for k, v in params.items()}
        logger.info(f"[TinyAPI] Calling {url} with params {safe_params}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    # 无论状态码，都尝试读取响应体
                    try:
                        # content_type=None 允许解析Content-Type非application/json的响应
                        result = await resp.json(content_type=None)
                    except:
                        # 不是JSON，读取纯文本
                        text = await resp.text()
                        result = {"code": resp.status, "message": text[:300], "data": None}

                    # 如果已是标准TinyAPI格式（含code字段），直接返回
                    # 让调用方根据 code 判断是否成功
                    if isinstance(result, dict) and "code" in result:
                        return result

                    # 非标准格式，按HTTP状态码包装
                    if resp.status == 200:
                        return {"code": 200, "message": "success", "data": result}
                    else:
                        return {
                            "code": resp.status,
                            "message": str(result)[:300],
                            "data": None
                        }
        except Exception as e:
            logger.error(f"[TinyAPI] Request failed: {e}")
            return {
                "code": 500,
                "message": f"请求失败: {str(e)}",
                "data": None
            }

    def _detect_media_from_url(self, url: str) -> Optional[str]:
        """从URL扩展名检测媒体类型

        Returns: "image" / "audio" / "video"，无法判断时返回 None
        """
        # 移除查询参数和锚点
        url_path = url.split("?")[0].split("#")[0].lower()
        for ext in IMAGE_EXTS:
            if url_path.endswith(ext):
                return "image"
        for ext in AUDIO_EXTS:
            if url_path.endswith(ext):
                return "audio"
        for ext in VIDEO_EXTS:
            if url_path.endswith(ext):
                return "video"
        return None

    def _format_result(self, result: Dict[str, Any]) -> List[tuple]:
        """格式化API返回结果 - 智能识别媒体类型

        返回 List[tuple]，每项为 (media_type, content)：
        - ("text",  文本内容)
        - ("image", 图片URL)
        - ("audio", 音频URL)
        - ("video", 视频URL)

        优化策略：
        1. 如果data包含content键 → 纯文本
        2. 扫描data中的所有媒体URL和文字字段 → 分别收集，可同时返回多条
        3. 否则，输出格式化的JSON文本
        """
        if result.get("code") != 200:
            return [("text", f"❌ 错误: {result.get('message', '未知错误')}")]

        data = result.get("data", {})
        if not data:
            return [("text", "✅ 请求成功，但返回数据为空")]

        results = []

        # 收集媒体URL和文字字段的辅助函数
        def _collect_all(obj, depth: int = 0, media=None, text_fields=None):
            if media is None:
                media = []
            if text_fields is None:
                text_fields = []
            if depth > 4:
                return media, text_fields
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if isinstance(val, str) and val.startswith("http"):
                        media_type = self._detect_media_from_url(val)
                        if media_type:
                            pair = (media_type, val)
                            if pair not in media:
                                media.append(pair)
                            continue
                    if isinstance(val, (str, int, float, bool)):
                        key_str = str(key)
                        val_str = str(val)
                        # 跳过纯 HTTP 链接字段（已 above 处理）
                        if isinstance(val, str) and val.startswith("http"):
                            continue
                        text_fields.append((key_str, val_str))
                    elif isinstance(val, (dict, list)):
                        _collect_all(val, depth + 1, media, text_fields)
            elif isinstance(obj, list):
                for item in obj:
                    _collect_all(item, depth + 1, media, text_fields)
            return media, text_fields

        # data 是字典
        if isinstance(data, dict):
            # 有 content 键 → 纯文本优先
            if "content" in data:
                content = data["content"]
                results.append(("text", content if isinstance(content, str) else str(content)))
                return results

            media_list, text_fields = _collect_all(data)
            # 添加所有媒体
            for media_type, media_url in media_list:
                results.append((media_type, media_url))
            # 添加文字字段（去重）
            if text_fields:
                seen = set()
                unique_parts = []
                for k, v in text_fields:
                    if k not in seen:
                        seen.add(k)
                        unique_parts.append(f"{k}：{v}")
                if unique_parts:
                    results.append(("text", "\n".join(unique_parts)))
            # 既没有媒体也没有文字 → fallback
            if not results:
                try:
                    results.append(("text", json.dumps(data, ensure_ascii=False, indent=2)))
                except:
                    results.append(("text", str(data)))
            return results

        # data 是纯字符串
        if isinstance(data, str):
            if data.startswith("http"):
                media_type = self._detect_media_from_url(data)
                if media_type:
                    results.append((media_type, data))
                    return results
            results.append(("text", data))
            return results

        # data 是列表
        if isinstance(data, list) and data:
            all_media = []
            all_text = []
            seen_media = set()
            for item in data:
                m, t = _collect_all(item)
                for pair in m:
                    if pair not in seen_media:
                        seen_media.add(pair)
                        all_media.append(pair)
                all_text.extend(t)
            for media_type, media_url in all_media:
                results.append((media_type, media_url))
            if all_text or (data and not all_media):
                # 列表数据：把原始数据作为文字发给 LLM 改写
                try:
                    results.append(("text", json.dumps(data, ensure_ascii=False, indent=2)))
                except:
                    results.append(("text", str(data)))
            return results

        # 默认
        try:
            results.append(("text", json.dumps(data, ensure_ascii=False, indent=2)))
        except:
            results.append(("text", str(data)))
        return results

    async def _send_result(self, event: AstrMessageEvent, result: Dict[str, Any], api_name: str = "") -> None:
        """发送API调用结果

        智能识别返回内容的媒体类型：
        - 图片URL → 直接发送图片（而非链接）
        - 音频URL → 直接发送语音
        - 视频URL → 直接发送视频
        - 文本   → 发送文本消息（若开启LLM改写则先改写）
        - 失败   → 发送错误信息
        - 混合   → 同时发送媒体和文字（如API返回图片+描述）
        """
        # 判断API调用是否成功
        if result.get("code") == 200:
            items = self._format_result(result)
            if not items:
                logger.warning(f"[TinyAPI] API返回数据为空: {api_name}")
                return

            # 分离媒体项和文字项
            media_items = [(t, c) for t, c in items if t in ("image", "video", "audio")]
            text_items = [(t, c) for t, c in items if t == "text"]

            # 准备文字内容（用于LLM改写或原文发送）
            raw_data = result.get("data")
            text_content = None
            if text_items:
                # 优先用原始数据让LLM改写（确保不遗漏字段）
                if self.enable_llm_rewrite and raw_data is not None:
                    try:
                        rewritten = await self._call_llm_rewrite(event, raw_data, api_name)
                        if rewritten:
                            text_content = rewritten
                    except Exception as e:
                        logger.warning(f"[TinyAPI] LLM改写失败，使用原文: {e}")
                if not text_content:
                    text_content = "\n\n".join(c for _, c in text_items)

            # 构建统一的结果对象：文字和媒体都加到同一条消息的 chain 里
            result_obj = MessageEventResult()

            # 先加文字（如果有）
            if text_content:
                result_obj.message(text_content)

            # 再追加媒体（图片/视频/音频）
            # QQ 单条消息有媒体数量限制，图片超过上限会发送失败，需限制数量
            media_image_count = 0
            MAX_IMAGES_PER_MESSAGE = 5  # 单条消息最多发送5张图片

            for media_type, content in media_items:
                if media_type == "image":
                    if media_image_count >= MAX_IMAGES_PER_MESSAGE:
                        logger.warning(f"[TinyAPI] 图片已达上限({MAX_IMAGES_PER_MESSAGE}张)，跳过: {content[:60]}")
                        continue
                    media_image_count += 1
                    logger.info(f"[TinyAPI] 追加图片到消息({media_image_count}/{MAX_IMAGES_PER_MESSAGE}): {content[:80]}")
                    result_obj.chain.append(Comp.Image.fromURL(url=content))
                elif media_type == "video":
                    logger.info(f"[TinyAPI] 追加视频到消息: {content[:80]}")
                    result_obj.chain.append(Comp.Video.fromURL(url=content))
                elif media_type == "audio":
                    logger.info(f"[TinyAPI] 追加音频到消息: {content[:80]}")
                    result_obj.chain.append(Comp.Record(file=content, url=content))

            event.set_result(result_obj)
            logger.info(f"[TinyAPI] 已发送结果: 文字={'有' if text_content else '无'} 媒体数={len(media_items)}")

        else:
            # 失败：发送错误信息
            error_msg = result.get('message', '未知错误')
            error_code = result.get('code', '未知')

            msg = f"❌ API调用失败\n"
            msg += f"错误码: {error_code}\n"
            msg += f"错误信息: {error_msg}\n"

            if api_name:
                msg += f"\nAPI: {api_name}"

            logger.warning(f"[TinyAPI] API调用失败: {api_name} - {error_code} - {error_msg}")
            event.set_result(MessageEventResult().message(msg))

    # ========== LLM 回复改写 ==========

    async def _call_llm_rewrite(self, event: AstrMessageEvent, data: Any, api_name: str = "") -> Optional[str]:
        """调用LLM对API返回的数据进行人性化改写

        使用AstrBot配置的对话大模型，让回复更像真人。
        若调用失败则返回None，上层会使用原文。
        要求LLM保留数据中每一个字段，不得遗漏。
        """
        try:
            # 获取当前会话的模型ID
            umo = event.unified_msg_origin
            provider_id = await self.context.get_current_chat_provider_id(umo=umo)
        except Exception as e:
            logger.warning(f"[TinyAPI] 获取LLM provider_id失败: {e}")
            return None

        # 将数据转为文本传给LLM
        if isinstance(data, (dict, list)):
            data_text = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            data_text = str(data)

        # 构建提示词——明确要求保留所有字段
        api_hint = f"（数据来源：{api_name}）" if api_name else ""
        prompt = (
            f"以下是某个API返回给用户的有用信息（已转为文本），请你用自然、口语化的方式说给用户听。\n\n"
            f"【必须遵守的规则】：\n"
            f"1. 只说有实际内容的信息，空值、空列表、null、空字符串直接跳过，一个字都不要提；\n"
            f"2. 绝对不要提到任何JSON字段名（如 json_data、images、raw_data、passwords 等），直接说内容本身；\n"
            f"3. 不要说「数据里有…」、「json_data 中…」这类话，直接把信息用自然语言说出来；\n"
            f"4. 如果某些字段的值全部是空的（如所有条目的图片都是空），直接不提这些字段，不要专门说「某字段是空的」；\n"
            f"5. 输出要有适当的换行，不同条目、不同主题之间用换行分隔，方便手机阅读，不要挤成一整段；\n"
            f"6. 语气像真人在聊天，简洁自然，不要罗列、不要编号说明结构。\n\n"
            f"【待转化的内容】：\n{data_text}"
        )

        try:
            llm_resp = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=prompt,
            )
            rewritten = llm_resp.completion_text.strip()
            if rewritten:
                logger.info(f"[TinyAPI] LLM改写成功: {api_name}")
                return rewritten
            return None
        except Exception as e:
            logger.warning(f"[TinyAPI] LLM改写调用失败: {e}")
            return None

    # ========== 参数校验与格式提示 ==========

    def _build_usage_hint(self, api_info: Dict, keyword: str) -> str:
        """为缺少参数的API构建使用格式提示

        当用户发送了关键词但没有提供必填参数，或者参数格式不正确时，
        返回清晰的输入格式说明（含 description、必填参数、可选参数）。
        """
        name = api_info.get("name", "")
        desc = api_info.get("description", "")
        params = api_info.get("params", {})
        required_params = api_info.get("required_params", [])
        param_types = api_info.get("param_types", {})

        # 基础提示（含 description）
        msg = f"📌 {name}\n"
        if desc:
            msg += f"   {desc}\n"
        msg += f"\n"

        # 判断是否需要特殊类型输入（图片/音频/视频URL）
        has_image_param = any(
            param_types.get(p) == "image_url" for p in required_params
        )
        has_image_file_param = any(
            param_types.get(p) == "image_file" for p in required_params
        )
        has_audio_param = any(
            param_types.get(p) == "audio_url" for p in required_params
        )
        has_video_param = any(
            param_types.get(p) == "video_url" for p in required_params
        )
        has_url_param = any(
            param_types.get(p) == "url" for p in required_params
        )

        # 必填参数（含详细说明）
        if required_params:
            msg += "📋 必填参数：\n"
            for pname in required_params:
                pdesc = params.get(pname, pname)
                ptype = param_types.get(pname, "text")
                if ptype == "image_url":
                    msg += f"  🖼️ {pname}：图片URL地址\n"
                    msg += f"     └ 说明：需要以 http:// 或 https:// 开头的图片链接\n"
                    msg += f"     └ 快捷方式：直接发送图片，Bot会自动上传图床获取链接\n"
                elif ptype == "image_file":
                    msg += f"  📷 {pname}：图片文件\n"
                    msg += f"     └ 说明：请直接发送图片给Bot\n"
                elif ptype == "audio_url":
                    msg += f"  🔊 {pname}：音频链接\n"
                    msg += f"     └ 说明：需要以 http:// 或 https:// 开头的音频文件链接\n"
                elif ptype == "video_url":
                    msg += f"  🎬 {pname}：视频链接\n"
                    msg += f"     └ 说明：需要以 http:// 或 https:// 开头的视频链接\n"
                elif ptype == "url":
                    msg += f"  🔗 {pname}：{pdesc}\n"
                    msg += f"     └ 说明：需要以 http:// 或 https:// 开头的链接\n"
                else:
                    msg += f"  📝 {pname}：{pdesc}\n"
        else:
            msg += "📋 必填参数：无（可直接调用）\n"

        # 可选参数
        optional_params = [p for p in params if p not in required_params]
        if optional_params:
            msg += "\n可选参数：\n"
            for pname in optional_params:
                pdesc = params.get(pname, pname)
                msg += f"  📎 {pname}：{pdesc}\n"

        # 给出输入格式示例
        msg += "\n💡 正确输入格式：\n"

        # 重新判断参数类型
        has_image_url_param = any(param_types.get(p) == "image_url" for p in required_params)
        has_image_file_param = any(param_types.get(p) == "image_file" for p in required_params)
        has_audio_param = any(param_types.get(p) == "audio_url" for p in required_params)
        has_video_param = any(param_types.get(p) == "video_url" for p in required_params)
        has_url_param = any(param_types.get(p) == "url" for p in required_params)
        text_required = [p for p in required_params if param_types.get(p, "text") == "text"]

        if has_image_file_param:
            msg += f"  {keyword}\n"
            msg += f"  └ 一条消息同时发「{keyword}」+ 图片\n"
        elif has_image_url_param:
            if text_required:
                # 同时需要文本+图片URL
                txt = text_required[0]
                txt_desc = params.get(txt, txt)
                msg += f"  {keyword} {txt_desc} [图片链接]\n"
                msg += f"  示例：{keyword} 识别这张图 https://example.com/face.jpg\n"
            else:
                msg += f"  {keyword} 图片链接\n"
                msg += f"  示例：{keyword} https://example.com/image.jpg\n"
                msg += f"  ✨ 也可以：直接发「{keyword}」+ 图片，Bot自动上传图床\n"
        elif has_audio_param:
            msg += f"  {keyword} 音频链接\n"
            msg += f"  示例：{keyword} https://example.com/audio.mp3\n"
        elif has_video_param:
            msg += f"  {keyword} 视频链接\n"
            msg += f"  示例：{keyword} https://example.com/video.mp4\n"
        elif has_url_param:
            first_required = required_params[0]
            desc_val = params.get(first_required, "")
            msg += f"  {keyword} 链接地址\n"
            msg += f"  示例：{keyword} https://example.com/page\n"
        elif text_required:
            # 普通文本参数，给出具体示例
            parts = [keyword]
            example_parts = [keyword]
            for p in text_required:
                pdesc = params.get(p, p)
                parts.append(f"[{pdesc}]")
                # 根据参数名给一个合理的示例值
                example_val = self._guess_example_value(p, pdesc)
                example_parts.append(example_val)
            msg += f"  {' '.join(parts)}\n"
            msg += f"  示例：{' '.join(example_parts)}\n"
        else:
            msg += f"  {keyword}\n（此API无需参数，直接发送关键词即可调用）\n"

        return msg

    def _guess_example_value(self, param_name: str, param_desc: str) -> str:
        """根据参数名和描述，猜测一个合理的示例值"""
        name_lower = param_name.lower()
        desc_lower = param_desc.lower()
        if any(k in name_lower or k in desc_lower for k in ["city", "城市", "地区"]):
            return "北京"
        if any(k in name_lower or k in desc_lower for k in ["word", "词", "内容", "文本", "msg", "text"]):
            return "你好"
        if any(k in name_lower or k in desc_lower for k in ["num", "数量", "count", "页", "page"]):
            return "10"
        if any(k in name_lower or k in desc_lower for k in ["type", "类型", "类型"]):
            return "1"
        return "示例值"

    def _validate_params(self, api_info: Dict, param_dict: Dict, user_id: Optional[str] = None) -> Optional[str]:
        """校验参数格式，返回错误提示或None（校验通过）

        主要校验：
        1. 必填参数是否缺失
        2. 需要URL的参数是否以 http:// 或 https:// 开头
        3. 图片文件参数是否有缓存的图片
        """
        required_params = api_info.get("required_params", [])
        param_types = api_info.get("param_types", {})
        params_desc = api_info.get("params", {})

        # 1. 检查必填参数缺失
        missing = []
        for p in required_params:
            if p not in param_dict or not param_dict[p]:

                missing.append(p)
        
        if missing:
            # 构造缺失参数的提示
            missing_desc = []
            for p in missing:
                ptype = param_types.get(p, "text")
                pdesc = params_desc.get(p, p)
                if ptype == "image_url":
                    missing_desc.append(f"🖼️ {p}（图片URL地址）")
                elif ptype == "image_file":
                    missing_desc.append(f"📷 {p}（图片文件，请直接发送图片给Bot）")
                elif ptype == "audio_url":
                    missing_desc.append(f"🔊 {p}（音频链接）")
                elif ptype == "video_url":
                    missing_desc.append(f"🎬 {p}（视频链接）")
                elif ptype == "url":
                    missing_desc.append(f"🔗 {p}（{pdesc}）")
                else:
                    missing_desc.append(f"📝 {p}（{pdesc}）")

            return f"⚠️ 缺少必填参数：{', '.join(missing_desc)}"

        # 2. 检查URL类参数格式
        for pname, pvalue in param_dict.items():
            ptype = param_types.get(pname, "text")
            if ptype in ("image_url", "audio_url", "video_url", "url"):
                if not URL_PATTERN.match(str(pvalue)):
                    type_label = {
                        "image_url": "图片URL",
                        "audio_url": "音频链接",
                        "video_url": "视频链接",
                        "url": "链接",
                    }.get(ptype, "URL")
                    return (
                        f"⚠️ 参数 {pname} 需要提供{type_label}，"
                        f"请以 http:// 或 https:// 开头\n"
                        f"你输入的内容：{pvalue}\n"
                        f"正确格式：{pname}=https://example.com/..."
                    )
            # image_file 类型不需要校验URL格式

        return None  # 校验通过
    # ========== 关键词快捷功能 ==========

    # ========== 关键词匹配处理器 ==========

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def keyword_match_handler(self, event: AstrMessageEvent) -> None:
        """关键词快捷调用处理器

        直接发送关键词即可调用对应API（无需/前缀）。
        两层匹配策略：
        1. 精确首词匹配 → 调用API（带参数校验）
        2. 短消息子串兜底 → 调用无参数API
        """
        if not self.enable_keyword_match:
            return

        user_id = event.get_sender_id()
        raw_message = event.message_str.strip()
        # 去掉所有 ？/?（支持消息中间也带？的情况）
        message_clean = raw_message.replace("？", "").replace("?", "")
        is_help_query = raw_message.endswith("？") or raw_message.endswith("?")
        message_lower = message_clean.lower()

        # 0. 先尝试提取图片（如果有），返回图片信息字典
        image_info = None
        image_info = await self._extract_image_from_event(event)
        if image_info:
            logger.info(f"[TinyAPI] 用户 {user_id} 发送了图片: {image_info.get('path', '')[:60]}")

        # 1. 精确首词匹配（优先级最高）
        # 支持「关键词？」或「关键词?» 结尾时展示参数说明
        tokens = message_clean.split()
        if tokens:
            first_word_lower = tokens[0].lower()
            if first_word_lower in self.keyword_map:
                # 匹配到关键词，必须停止事件传播
                event.stop_event()

                # 以 ？/? 结尾 → 展示参数说明，不调用API
                if is_help_query:
                    api_info = self.keyword_api_info.get(first_word_lower, {})
                    hint = self._build_usage_hint(api_info, first_word_lower)
                    event.set_result(MessageEventResult().message(hint))
                    return

                path = self.keyword_map[first_word_lower]
                api_info = self.keyword_api_info.get(first_word_lower, {})
                api_name = api_info.get("name", "")
                api_params = api_info.get("params", {})
                required_params = api_info.get("required_params", [])
                param_types = api_info.get("param_types", {})

                remaining_text = " ".join(tokens[1:])

                # 构建参数字典
                param_dict = {}
                if remaining_text:
                    if required_params:
                        first_required = required_params[0]
                        param_dict[first_required] = remaining_text
                    elif api_params:
                        first_param = list(api_params.keys())[0]
                        param_dict[first_param] = remaining_text
                    else:
                        param_dict["msg"] = remaining_text

                # --- 图片参数处理 ---
                # 获取可用的图片信息（仅当前消息，不支持分开发送）
                curr_image_info = image_info
                curr_image_path = curr_image_info.get("path") if curr_image_info else None
                curr_image_url = curr_image_info.get("url") if curr_image_info else None

                # 检查API是否需要图片参数
                has_image_file_param = any(
                    param_types.get(p) == "image_file" for p in required_params + list(api_params.keys())
                )
                has_image_url_param = any(
                    param_types.get(p) == "image_url" for p in required_params + list(api_params.keys())
                )
                has_any_image = (has_image_file_param and curr_image_path) or (has_image_url_param and curr_image_url)

                # 处理 image_file 类型参数（本地图片文件）
                if has_image_file_param and curr_image_path:
                    image_param_name = None
                    for pname, ptype in param_types.items():
                        if ptype == "image_file":
                            image_param_name = pname
                            break
                    if image_param_name:
                        image_data = self._image_to_base64(curr_image_path)
                        if image_data:
                            param_dict[image_param_name] = image_data
                        else:
                            param_dict[image_param_name] = curr_image_path

                # 处理 image_url 类型参数（图片URL）
                if has_image_url_param and curr_image_url:
                    url_param_name = None
                    for pname, ptype in param_types.items():
                        if ptype == "image_url":
                            url_param_name = pname
                            break
                    if url_param_name:
                        param_dict[url_param_name] = curr_image_url

                # 如果API需要 image_url 但只有本地图片路径，自动上传图床
                if has_image_url_param and not curr_image_url and curr_image_path:
                    url_param_name = None
                    for pname, ptype in param_types.items():
                        if ptype == "image_url":
                            url_param_name = pname
                            break
                    if url_param_name:
                        logger.info(f"[TinyAPI] 正在上传图片到图床获取URL: {curr_image_path}")
                        uploaded_url = await self._upload_image_to_host(curr_image_path)
                        if uploaded_url:
                            param_dict[url_param_name] = uploaded_url
                            logger.info(f"[TinyAPI] 图片上传成功，URL: {uploaded_url[:60]}")
                        else:
                            event.set_result(MessageEventResult().message(
                                "⚠️ 图片上传图床失败，无法调用此API。请尝试直接发送图片链接。"
                            ))
                            return

                # --- 参数校验 ---
                validation_error = self._validate_params(api_info, param_dict, user_id)
                if validation_error:
                    # 校验失败：显示完整使用说明（含描述、参数列表、正确格式）
                    hint = self._build_usage_hint(api_info, first_word_lower)
                    event.set_result(MessageEventResult().message(hint))
                    return

                # 如果没有剩余文本且API需要必填参数，且没有提供图片 → 显示使用提示
                # 注意：有图片参数的API，图片输入等同于参数输入
                needs_text_input = required_params and not any(
                    param_types.get(p) in ("image_file", "image_url") for p in required_params
                )
                has_any_image_input = (has_image_file_param and curr_image_path) or (has_image_url_param and curr_image_url)
                if not remaining_text and needs_text_input and not has_any_image_input:
                    hint = self._build_usage_hint(api_info, first_word_lower)
                    event.set_result(MessageEventResult().message(hint))
                    return

                # 调用API
                result = await self._call_api(path, param_dict)
                await self._send_result(event, result, api_name)
                return

        # 2. 子串匹配（兜底，仅用于短消息）
        if len(message_clean) <= 4:
            for keyword, path in self.keyword_map.items():
                if keyword in message_lower:
                    # 若以 ？/? 结尾 → 展示参数说明
                    if is_help_query:
                        api_info = self.keyword_api_info.get(keyword, {})
                        hint = self._build_usage_hint(api_info, keyword)
                        event.set_result(MessageEventResult().message(hint))
                        return
                    api_info = self.keyword_api_info.get(keyword, {})
                    if api_info.get("required_params"):
                        continue
                    event.stop_event()
                    api_name = api_info.get("name", "")
                    logger.info(f"[TinyAPI] 子串匹配调用: keyword={keyword}, path={path}")
                    result = await self._call_api(path)
                    await self._send_result(event, result, api_name)
                    return



    @filter.command(
        "api查询",
        alias={
            "查看api", "查看接口", "api列表", "关键词列表", "可用api", "可用接口",
            "查看关键词", "查看关键字", "接口列表", "查询api", "查询接口",
            "api关键字", "关键字列表",
        },
    )
    async def view_api_list(self, event: AstrMessageEvent) -> None:
        """查看所有可用的API关键词列表（直接对Bot说即可触发）"""
        pages = self._build_keyword_messages()
        total_pages = len(pages)
        for i, msg in enumerate(pages, 1):
            if total_pages > 1:
                msg = f"（第 {i}/{total_pages} 页）\n" + msg
            yield event.plain_result(msg)

    # ========== 关键词快捷功能 ==========

    def _build_keyword_messages(self) -> list:
        """构建关键词→API名称映射消息列表，返回字符串列表（每条为一条消息）

        每条消息最多 80 行，超出自动分批，避免单条消息过长。
        格式：纯垂直列表，每行一个「关键词 → API名称」。
        """
        apis = self.apis_config.get("apis", [])
        if not apis:
            return ["📭 API池为空，请先在 config/apis.json 中添加API"]

        # 收集所有关键词→名称映射（去重，保持原顺序）
        keyword_mappings = []
        seen_keywords = set()
        for api in apis:
            name = api.get("name", "未命名")
            for kw in api.get("keywords", []):
                kl = kw.lower()
                if kl not in seen_keywords:
                    seen_keywords.add(kl)
                    keyword_mappings.append((kw, name))

        total = len(keyword_mappings)

        # 每页底部提示备注
        footer = "\n💡 左侧为关键词，关键词需严格对应，输入「关键词？」可询问Bot该功能如何使用\n"

        # 简洁头部
        header = "📋 TinyAPI 关键词列表（共 " + str(total) + " 个）\n\n"

        pages = []
        current = header
        line_count = 0
        for kw, name in keyword_mappings:
            line = "  " + kw + " → " + name + "\n"
            if line_count >= 80 or len(current) + len(line) > 3500:
                current += footer
                pages.append(current)
                current = header
                line_count = 0
            current += line
            line_count += 1
        current += footer
        pages.append(current)

        return pages


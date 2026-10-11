from urllib.parse import urlsplit


class ModelConfigurationError(RuntimeError):
    """可安全展示的模型配置或发现错误，不包含服务商原始响应。"""


def model_settings(configured_model, base_url, client, api_key):
    """通过官方模型列表解析显示名，只接受同一条记录，不替换模型。"""
    if urlsplit(base_url or "").hostname != "api.deepseek.com":
        return configured_model, {}

    response = client.get(base_url.rstrip("/") + "/models",
                          headers={"Authorization": f"Bearer {api_key}"}, timeout=20)
    if not response.is_success:
        raise ModelConfigurationError(f"读取服务商可用模型失败（HTTP {response.status_code}）；请检查密钥和接口配置")
    records = response.json().get("data", [])
    matches = [record for record in records
               if configured_model in (record.get("id"), record.get("name"))]
    identifiers = {record.get("id") for record in matches if record.get("id")}
    if len(identifiers) != 1:
        raise ValueError("配置名称无法唯一匹配服务商可用模型；请核对名称，程序没有自动替换模型")

    # 抽取器强制调用 Extraction，DeepSeek 思考模式不支持指定工具。
    return identifiers.pop(), {"extra_body": {"thinking": {"type": "disabled"}}}

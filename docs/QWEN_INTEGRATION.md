# 千问接入与密钥安全

## 这一版如何使用千问

`v0.4.0` 采用 Hybrid Agent：

```text
用户问题
  → 本地识别分析重点
  → SQLite 查询球员数据
  → Python 计算每90分钟、百分位和加权得分
  → 生成结构化证据与结论边界
  → 千问只基于这些内容组织中文回答
```

千问不能修改胜者、综合得分、置信度或指标数据。没有 API Key、请求超时、
额度异常或返回格式错误时，后端会自动使用本地规则结论，不会让整个页面失败。

## Windows 配置

打开项目中的 `backend/.env`，在文件末尾加入：

```env
DASHSCOPE_API_KEY=把你自己的百炼API-Key填在这里
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_TIMEOUT_SECONDS=20
```

保存后重启后端。浏览器打开：

<http://127.0.0.1:8000/api/agent/capabilities>

当 `qwen_configured` 为 `true` 时，表示后端已读取到配置。此接口永远不会返回
真实 API Key。

阿里云目前建议北京、新加坡和东京地域使用带业务空间 ID 的专属 Base URL。
如果控制台向你提供了专属地址，就把 `QWEN_BASE_URL` 替换为控制台中的地址。
原有 `dashscope.aliyuncs.com` 地址仍可用于兼容接入。

官方参考：

- [OpenAI Chat 接口兼容](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [千问结构化输出](https://help.aliyun.com/en/model-studio/qwen-structured-output)
- [新人免费额度](https://help.aliyun.com/zh/model-studio/new-free-quota)

## 必须遵守的安全规则

- API Key 只能写在 `backend/.env`。
- 不要把 Key 写进 `frontend/.env.local` 或任何 `NEXT_PUBLIC_*` 变量。
- 不要把 Key 粘贴进源码、截图、README、Issue 或聊天记录。
- 提交前在项目根目录运行 `git status`，确认没有 `.env`。
- 如果 Key 曾经被上传到 GitHub，应立即在百炼控制台删除并重新创建。

## 四种正常页面状态

| 页面状态 | 含义 |
| --- | --- |
| `LOCAL SAFE MODE` | 未配置千问，或本次调用已安全回退；本地分析仍完整可用 |
| `QWEN ENHANCED` | 千问已基于本地计算结果组织回答 |
| `LOCAL TOOL ROUTER` | League Copilot 由本地路由选择受控工具并执行 |
| `QWEN TOOL CALLING` | 千问返回 `tool_calls`，后端校验、执行并回传结构化证据 |

即使页面显示 `QWEN ENHANCED`，数值和证据仍来自本地数据库与 Python 计算。
即使页面显示 `QWEN TOOL CALLING`，千问也不能直接访问数据库或修改工具结果。完整流程见 [`LEAGUE_COPILOT.md`](LEAGUE_COPILOT.md)。

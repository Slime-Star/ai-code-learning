AI 服务使用后端目录的 `.env`，不要将 API 密钥放入前端、报告或版本库。

豆包编程助手通过本机 3000 端口的 Node 服务调用。当前模型配置为 `doubao-seed-2-1-turbo-260628`，接口为 `https://ark.cn-beijing.volces.com/api/v3/chat/completions`。`DOUBAO_API_KEY`、`DOUBAO_MODEL_ID`、`DOUBAO_API_URL` 分别设置密钥、模型和接口；专用配置优先于兼容的 `AI_API_KEY`、`AI_MODEL_ID`。`bot-…` 模型在未指定接口时走应用接口，模型或 `ep-…` 接入点走标准接口。显式配置 `AI_CHAT_COMPLETIONS_URL` 时只调用该自定义服务。

DeepSeek 学习分析由 3002 端口的 Python 服务提供。`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`DEEPSEEK_API_BASE` 分别设置密钥、模型、服务地址。默认使用 `deepseek-flash`；官方服务中的已退役旧名称会迁移为此名称，自定义地址与自定义模型保留原配置。

学生只能分析本人，教师只能分析自己班级内学生。报告查询同一时间范围的数据库记录，先显示本地概览，再补充模型建议；模型失败保留本地结果。分析依据、次数和样本范围由后端固定，模型仅补充说明与建议。相同数据的成功模型报告缓存 5 分钟，相同正在处理的报告合并请求。

聊天界面显示实际回复来源。取消请求会停止上游等待，不启动备用模型；豆包无法提供服务时，可使用已配置的 DeepSeek，并明确标记备用来源。配置修改后需重启 Node 与 Python 服务。

接口依据：[火山方舟会话 API](https://api.volcengine.com/api-docs/view?action=ChatCompletions&serviceCode=ark&version=2024-01-01)、[DeepSeek JSON 输出](https://api-docs.deepseek.com/guides/json_mode/)、[DeepSeek 模型更新说明](https://api-docs.deepseek.com/updates/)。

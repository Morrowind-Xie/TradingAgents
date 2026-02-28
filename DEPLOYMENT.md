# 部署指南（TradingAgents）

这个项目默认以脚本/CLI 方式运行，不需要对外暴露入站端口。你只需要准备好运行环境与 API Key。

## 方式一：在服务器上直接运行（推荐）

1. 准备 Python（>=3.10）

在 Ubuntu/Debian 上，通常需要先安装 venv 与 pip：

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

2. 安装依赖

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
pip install -r requirements.txt
```

3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入：

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`（当 LLM 直连 deepseek 时可用它替代 OPENAI_API_KEY）
- `OPENROUTER_API_KEY`（当 LLM 使用 openrouter 时可用它替代 OPENAI_API_KEY）
- `ALPHA_VANTAGE_API_KEY`（使用默认数据源时需要）
- `TUSHARE_TOKEN`（当数据源使用 tushare 时需要）

4. 运行

非交互示例（直接跑 `main.py`）：

```bash
python3 main.py
```

交互式 CLI：

```bash
python3 -m cli.main
```

## 方式二：Docker Compose 部署

1. 准备 `.env`

```bash
cp .env.example .env
```

2. 启动

```bash
docker compose up -d --build
docker compose logs -f
```

默认会把 `./results` 与 `./data` 挂载到容器内的 `/app/results`、`/app/data`，便于持久化产物与本地数据。

## 可选：使用本机 Ollama（11434）

如果你希望把 LLM 后端换成本机 Ollama（默认监听 `localhost:11434`），需要保证容器能访问宿主机。

`docker-compose.yml` 已包含：

- `extra_hosts: host.docker.internal:host-gateway`

这样容器内可以用 `http://host.docker.internal:11434/v1` 访问宿主机。

然后在你的运行配置里把：

- `llm_provider` 设为 `ollama`
- `backend_url` 设为 `http://host.docker.internal:11434/v1`

---

## 项目运行形态与端口说明

这个项目默认不是一个“前端/后端 Web 服务”，而是脚本/CLI 驱动的工作流：

- **没有需要对外开放的入站端口**
- 主要是**出站访问**：LLM 推理服务（DeepSeek / OpenAI / OpenRouter / Ollama 等）与数据源（AkShare、Google News 抓取等）

可能涉及的端口：

- **443（出站）**：访问 `https://api.deepseek.com/v1`、Google 搜索等
- **11434（出站到本机）**：仅当你使用本机 Ollama（`http://localhost:11434/v1`）时

---

## 入口与启动方式

**1）非交互脚本入口**

- 文件：`main.py`
- 用途：固定参数跑一遍分析（适合测试你的 Key/依赖是否正常）

```bash
cd /home/morrowind/My_Projects/TradingAgents
. .venv/bin/activate
python3 main.py
```

**2）交互式 CLI 入口**

- 入口：`python3 -m cli.main`
- 用途：按步骤选择 ticker、日期、分析团队、LLM Provider、模型等（适合日常使用）

```bash
cd /home/morrowind/My_Projects/TradingAgents
. .venv/bin/activate
python3 -m cli.main
```

---

## 环境变量与配置（建议做法）

### `.env` 与 `.env.example` 的区别

- `.env.example`：示例模板（可以提交到仓库，用于提示需要哪些配置）
- `.env`：你本机真实配置（通常包含密钥，**不要提交到仓库**）

### DeepSeek 直连（当前默认方案）

当前默认配置为 DeepSeek OpenAI-兼容直连：

- `TRADINGAGENTS_BACKEND_URL=https://api.deepseek.com/v1`
- `TRADINGAGENTS_DEEP_THINK_LLM=deepseek-chat`
- `TRADINGAGENTS_QUICK_THINK_LLM=deepseek-chat`
- `llm_provider` 内部使用 `openai`（因为项目使用 OpenAI 兼容 SDK/ChatOpenAI，但 base_url 指向 DeepSeek）

推荐 `.env` 至少包含：

```env
DEEPSEEK_API_KEY=你的_key
TRADINGAGENTS_BACKEND_URL=https://api.deepseek.com/v1
TRADINGAGENTS_DEEP_THINK_LLM=deepseek-chat
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-chat
```

项目会把 `DEEPSEEK_API_KEY` 映射为 `OPENAI_API_KEY` 使用（当 `OPENAI_API_KEY` 为空或仍是 placeholder 时）。

### 数据源（A 股推荐：AkShare）

当前默认更偏向 A 股数据：

- 行情：`akshare,yfinance`
- 技术指标：`yfinance`（stockstats/yfinance 体系）
- 基本面：`akshare`
- 新闻：`akshare`
- 全局新闻：单独强制走 `google`（避免依赖 OpenAI 的 web_search tools）

推荐 `.env` 配置：

```env
TRADINGAGENTS_CORE_STOCK_APIS_VENDOR=akshare,yfinance
TRADINGAGENTS_FUNDAMENTAL_DATA_VENDOR=akshare
TRADINGAGENTS_NEWS_DATA_VENDOR=akshare
TRADINGAGENTS_GET_GLOBAL_NEWS_VENDOR=google
```

---

## Docker 部署说明（已添加文件）

仓库已包含：

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

使用方式：

```bash
cd /home/morrowind/My_Projects/TradingAgents
cp .env.example .env
docker compose up -d --build
docker compose logs -f
```

默认挂载：

- `./results` → `/app/results`
- `./data` → `/app/data`

---

## CLI 交互步骤说明（常见问题）

### Step 1: Ticker Symbol

这里要输入你要分析的标的：

- A 股推荐输入：`600519.SH`、`000001.SZ`
- 也支持仅输入 6 位数字：`600519`

如果直接回车会使用默认值（如 `SPY`）。

### Step 5: OpenAI backend（其实是“选择 LLM 服务”）

CLI 的菜单里选择你要连接的“OpenAI 兼容服务 base_url”。

为避免困惑，CLI 已新增 **DeepSeek** 选项：

- 选 **DeepSeek**：对应 `https://api.deepseek.com/v1`
- 选 **OpenAI**：对应 `https://api.openai.com/v1`
- 选 **Openrouter**：对应 `https://openrouter.ai/api/v1`
- 选 **Ollama**：对应 `http://localhost:11434/v1`

注意：内部会把 `DeepSeek` 映射为 OpenAI 兼容模式运行（`llm_provider` 会转换为 `openai`）。

---

## 调试记录（按问题归档）

### 1）系统 Python 没有 pip / `ensurepip` 被禁用

现象：

- `python3 -m pip ...` 报 `No module named pip`
- `python3 -m ensurepip` 报 “ensurepip is disabled in Debian/Ubuntu for the system python”

处理：

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

然后使用 venv 安装依赖（推荐做法）：

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
pip install -r requirements.txt
```

### 2）在错误目录激活 venv（`.venv/bin/activate` 找不到）

现象：

- 在 `~` 目录执行 `. .venv/bin/activate` 报错 `No such file or directory`

处理：

必须先进入项目目录：

```bash
cd /home/morrowind/My_Projects/TradingAgents
. .venv/bin/activate
```

### 3）`.env` 里 `OPENAI_API_KEY` 是 placeholder，导致 DeepSeek 直连没有生效

现象：

- `.env` 中虽然写了 `DEEPSEEK_API_KEY`，但 `OPENAI_API_KEY` 仍是 `openai_api_key_placeholder`
- 由于环境变量已存在，程序不会自动用 DeepSeek key 覆盖，导致鉴权失败

处理：

- 已在 `main.py` / `cli/main.py` 增强逻辑：当 `OPENAI_API_KEY` 为空或包含 `placeholder` 时，会使用 `DEEPSEEK_API_KEY` 覆盖到 `OPENAI_API_KEY`。

建议：

- 生产环境最好只保留一个有效 key（不要保留 placeholder）。

### 4）全局新闻 `get_global_news` 在 AkShare 场景下阻断运行

现象：

- `get_global_news` 之前没有 `akshare` vendor
- fallback 到 `openai` 会因 `responses`/工具不兼容或 404 失败
- fallback 到 `local` 会因 `./data/reddit_data/...` 不存在而失败

处理：

- 新增 `get_global_news_google`，让全局新闻走 Google 抓取
- 在默认配置中把 `get_global_news` 强制为 `google` vendor（`tool_vendors`）

### 5）`get_news` 中 AkShare 报 `Unsupported ticker format: 储能/中国能源`

现象：

- LLM 有时把“概念词/关键词”（如“储能”）当作 ticker 传入 `get_news`
- AkShare 的股票新闻接口通常需要 6 位代码或可识别的股票名，概念词无法解析

处理：

- AkShare 增加“中文公司名 → 6 位代码”的解析与缓存（缓存文件：`dataflows/data_cache/akshare_a_code_name.csv`）
- 新增 `get_news_google(query, start_date, end_date)` 作为兜底（同签名），并把 `google` 放在 `get_news` 的优先 fallback 位置
- 路由层不再把空字符串当作成功结果，避免“成功但没有新闻”的假成功

建议：

- 输入 ticker 时优先使用 `600xxx.SH / 000xxx.SZ`，减少 LLM 误传“概念词”的概率。

### 6）AkShare 上游请求不稳定（超时 / incomplete read）

现象：

- AkShare 调用某些接口时出现 `Read timed out`、`IncompleteRead` 等网络错误

处理策略：

- 对“公司名→代码”的解析加缓存，减少频繁访问上游列表接口
- 对财报接口增加多函数回退（同一类财报换不同 AkShare 函数尝试）

### 7）CLI 中“用 DeepSeek 但没有选项”的困惑

现象：

- Step 5 提示 “OpenAI backend”，菜单只有 OpenAI/Anthropic/Google/Openrouter/Ollama

处理：

- CLI 已新增 **DeepSeek** 选项（base_url=`https://api.deepseek.com/v1`），并在内部映射为 OpenAI 兼容运行。

### 8）A 股技术指标全部返回 "N/A: Not a trading day"

现象：

- `get_indicators` 对 A 股代码（如 `600519.SH`）调用时，所有日期的指标值都返回 "N/A: Not a trading day (weekend or holiday)"
- 实际上这些日期是交易日，有正常的行情数据

根本原因：

- 技术指标默认使用 `yfinance` vendor
- `yfinance` 的 `yf.download()` 对 A 股代码支持不好，返回空数据
- 当数据为空时，stockstats 无法计算指标，所有日期都找不到对应值

处理：

- 在 `akshare_cn.py` 中新增 `get_indicators_akshare()` 函数，基于 AkShare 行情数据 + stockstats 计算技术指标
- 在 `interface.py` 的 `VENDOR_METHODS` 中添加 `akshare` 作为 `get_indicators` 的 vendor
- 更新 `default_config.py`，将 `technical_indicators` 默认值改为 `akshare,yfinance`（优先用 akshare，yfinance 作为回退）

支持的指标：

- 移动平均：`close_50_sma`、`close_200_sma`、`close_10_ema`
- MACD 系列：`macd`、`macds`、`macdh`
- 动量指标：`rsi`、`mfi`
- 布林带：`boll`、`boll_ub`、`boll_lb`
- 波动率：`atr`
- 成交量加权：`vwma`

---

## 安全注意事项（重要）

- 不要把真实 API Key 提交到仓库或粘贴到公开渠道。
- 如果你曾经在终端/聊天里暴露过 Key，建议立刻在对应平台控制台**作废并重新生成**。

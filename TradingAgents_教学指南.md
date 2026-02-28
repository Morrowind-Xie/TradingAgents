# TradingAgents 教学指南

> 一份通俗易懂的多智能体金融交易框架解读

---

## 一、项目是什么？

### 1.1 一句话概括

**TradingAgents 是一个用 LLM（大语言模型）模拟真实投资公司运作的交易决策框架。**

### 1.2 生活化比喻

想象你开了一家投资公司，里面有：
- **4个分析师** - 分别从不同角度研究市场
- **2个研究员** - 一个看多一个看空，互相辩论
- **1个研究经理** - 听完辩论做出投资建议
- **1个交易员** - 根据建议制定交易计划
- **3个风险专家** - 评估交易风险
- **1个风控经理** - 做最终决策

TradingAgents 就是用 AI 来扮演这些角色，让他们协作完成交易决策。

---

## 二、核心设计理念

### 2.1 为什么用多个 Agent？

| 单一模型的问题 | 多智能体的优势 |
|:---|:---|
| 容易产生偏见 | 多角度互相校验 |
| 信息处理有限 | 分工协作效率高 |
| 决策黑盒 | 流程透明可追溯 |
| 无法自我质疑 | 辩论机制纠偏 |

### 2.2 两个核心机制

1. **辩论机制（Debate）**
   - 看多 vs 看空研究员辩论
   - 激进/稳健/中立风控辩论
   - 通过对抗得出更平衡的结论

2. **记忆机制（Memory）**
   - 记录历史决策和结果
   - 相似场景时调取经验
   - 从错误中学习改进

---

## 三、系统架构

### 3.1 四层架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        输入层 Input                              │
│                   股票代码 + 交易日期                             │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   分析层 Analyst Team                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐       │
│  │ 市场分析 │ │ 情绪分析 │ │ 新闻分析 │ │  基本面分析   │       │
│  │ Analyst  │ │ Analyst  │ │ Analyst  │ │   Analyst    │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘       │
│       │           │            │              │                │
│       └───────────┴────────────┴──────────────┘                │
│                        ▼ 汇总4份报告                            │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   研究层 Researcher Team                        │
│       ┌────────────────────────────────────────┐               │
│       │    🐂 Bull           🐻 Bear           │               │
│       │   看多研究员  ⟷辩论⟷  看空研究员       │               │
│       └───────────────────┬────────────────────┘               │
│                           ▼                                     │
│                   📋 Research Manager                           │
│                   (综合辩论结果，生成投资建议)                    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    交易层 Trader                                │
│              📈 根据投资建议，制定具体交易计划                    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  风控层 Risk Management                         │
│       ┌────────────────────────────────────────┐               │
│       │  🔥激进      ⚖️中立       🛡️保守       │               │
│       │ Risky ⟷辩论⟷ Neutral ⟷辩论⟷ Safe      │               │
│       └───────────────────┬────────────────────┘               │
│                           ▼                                     │
│                   ⚖️ Risk Manager                               │
│               (最终决策: BUY / HOLD / SELL)                     │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构

```
TradingAgents/
├── tradingagents/           # 核心代码
│   ├── agents/              # 所有 Agent 定义
│   │   ├── analysts/        # 4类分析师
│   │   ├── researchers/     # 多空研究员
│   │   ├── trader/          # 交易员
│   │   ├── managers/        # 研究经理 & 风控经理
│   │   ├── risk_mgmt/       # 风险辩论者
│   │   └── utils/           # 状态定义 & 记忆系统
│   ├── graph/               # LangGraph 工作流
│   │   ├── trading_graph.py # 主入口
│   │   ├── setup.py         # 图构建
│   │   ├── conditional_logic.py # 流程控制
│   │   └── reflection.py    # 反思机制
│   └── dataflows/           # 数据源接口
│       ├── y_finance.py     # Yahoo Finance
│       ├── akshare_cn.py    # A股数据
│       └── ...              # 其他数据源
├── main.py                  # 使用示例
└── cli/                     # 命令行工具
```

---

## 四、Agent 角色详解

### 4.1 分析师团队（并行执行）

| Agent | 职责 | 使用的工具 | 输出 |
|:---|:---|:---|:---|
| **Market Analyst** | 技术面分析 | 股价数据、MACD/RSI/布林带等指标 | 技术分析报告 |
| **Social Analyst** | 舆情分析 | 社交媒体新闻 | 市场情绪报告 |
| **News Analyst** | 新闻分析 | 全球新闻、内部交易信息 | 新闻影响报告 |
| **Fundamentals Analyst** | 基本面分析 | 财报、资产负债表、现金流 | 财务分析报告 |

**工作方式**：每个分析师调用对应的数据工具，生成 Markdown 格式报告。

### 4.2 研究员团队（辩论模式）

```
┌─────────────────────────────────────────────────────────┐
│  Bull Researcher（看多派）                               │
│  "这只股票有增长潜力、竞争优势、正面市场指标..."          │
└─────────────────────────┬───────────────────────────────┘
                          │ 辩论回合 (默认1轮)
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Bear Researcher（看空派）                               │
│  "风险因素包括...市场不确定性...估值过高..."              │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Research Manager（裁判）                               │
│  综合双方观点，输出投资建议                              │
└─────────────────────────────────────────────────────────┘
```

### 4.3 交易员

- **输入**：研究经理的投资建议
- **处理**：结合历史记忆，制定具体交易计划
- **输出**：交易提案（买入/卖出/持有 + 理由）

### 4.4 风控团队（三方辩论）

| Agent | 立场 | 关注点 |
|:---|:---|:---|
| **Risky Analyst** | 激进 | 追求高收益，愿意承担风险 |
| **Neutral Analyst** | 中立 | 平衡收益与风险 |
| **Safe Analyst** | 保守 | 优先考虑风险控制 |

**Risk Manager** 最终综合三方意见，输出最终决策：
- `BUY` - 买入
- `HOLD` - 持有
- `SELL` - 卖出

---

## 五、工作流程详解

### 5.1 数据流转过程

```python
# 1. 初始化输入
input = {
    "company_of_interest": "600519.SH",  # 贵州茅台
    "trade_date": "2024-05-10"
}

# 2. 分析层
→ Market Analyst  → market_report
→ Social Analyst  → sentiment_report  
→ News Analyst    → news_report
→ Fundamentals    → fundamentals_report

# 3. 研究层
→ Bull ⟷ Bear 辩论
→ Research Manager → investment_plan

# 4. 交易层
→ Trader → trader_investment_plan

# 5. 风控层
→ Risky ⟷ Neutral ⟷ Safe 辩论
→ Risk Manager → final_trade_decision ("BUY/HOLD/SELL")
```

### 5.2 状态管理

系统使用 `AgentState` 统一管理所有信息流转：

```python
class AgentState:
    company_of_interest: str   # 股票代码
    trade_date: str            # 交易日期
    
    # 4份分析报告
    market_report: str
    sentiment_report: str
    news_report: str
    fundamentals_report: str
    
    # 投资辩论状态
    investment_debate_state: InvestDebateState
    investment_plan: str       # 研究经理的建议
    
    # 交易计划
    trader_investment_plan: str
    
    # 风控辩论状态
    risk_debate_state: RiskDebateState
    final_trade_decision: str  # 最终决策
```

---

## 六、关键技术点

### 6.1 LangGraph 状态图

项目使用 **LangGraph** 构建 Agent 工作流：

```python
# 简化的图构建逻辑
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("Market Analyst", market_analyst_node)
workflow.add_node("Bull Researcher", bull_node)
workflow.add_node("Bear Researcher", bear_node)
# ...

# 定义边（流转规则）
workflow.add_edge(START, "Market Analyst")
workflow.add_edge("Market Analyst", "Social Analyst")
# ...

# 条件边（根据状态决定下一步）
workflow.add_conditional_edges(
    "Bull Researcher",
    should_continue_debate,  # 判断是否继续辩论
    {"Bear Researcher", "Research Manager"}
)
```

### 6.2 记忆系统 (Memory)

基于 **ChromaDB** 的向量记忆：

```python
class FinancialSituationMemory:
    def add_situations(self, situations_and_advice):
        """存储历史场景和建议"""
        # 将场景编码为向量存入 ChromaDB
        
    def get_memories(self, current_situation, n_matches=2):
        """检索相似历史场景"""
        # 返回最相似的历史经验
```

**作用**：Agent 在决策时会检索相似历史场景，参考过去的经验教训。

### 6.3 反思机制 (Reflection)

交易结束后，根据实际收益/亏损进行反思：

```python
def reflect_and_remember(self, returns_losses):
    """根据收益结果反思各个 Agent 的决策"""
    # 分析哪些判断正确/错误
    # 将反思结果存入记忆
```

---

## 七、快速上手

### 7.1 最简代码

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 初始化
ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())

# 运行决策
_, decision = ta.propagate("600519.SH", "2024-05-10")
print(decision)  # 输出: BUY / HOLD / SELL
```

### 7.2 配置说明

```python
config = {
    # LLM 配置
    "llm_provider": "openai",
    "deep_think_llm": "deepseek-chat",   # 深度思考模型
    "quick_think_llm": "deepseek-chat",  # 快速响应模型
    "backend_url": "https://api.deepseek.com/v1",
    
    # 辩论轮数
    "max_debate_rounds": 1,      # 多空辩论轮数
    "max_risk_discuss_rounds": 1, # 风控辩论轮数
    
    # 数据源
    "data_vendors": {
        "core_stock_apis": "akshare,yfinance",
        "technical_indicators": "akshare,yfinance",
        "fundamental_data": "akshare",
        "news_data": "akshare",
    },
}
```

### 7.3 CLI 使用

```bash
# 启动交互式命令行
python -m cli.main
```

---

## 八、总结

### TradingAgents 的核心价值

1. **模拟真实投资流程** - 分工明确，流程清晰
2. **多角度分析** - 技术面、基本面、情绪面全覆盖
3. **辩论式决策** - 通过对抗减少单一偏见
4. **持续学习** - 记忆+反思机制不断优化

### 适用场景

- 量化策略研究
- 投资决策辅助
- 金融 AI 教学
- Agent 系统学习

### 注意事项

⚠️ **免责声明**：本框架仅供研究学习，不构成投资建议。实际交易受多种因素影响，请谨慎决策。

---

## 附录：核心文件速查

| 文件 | 作用 |
|:---|:---|
| `tradingagents/graph/trading_graph.py` | 主入口类 |
| `tradingagents/graph/setup.py` | 图构建逻辑 |
| `tradingagents/agents/analysts/*.py` | 4类分析师实现 |
| `tradingagents/agents/researchers/*.py` | 多空研究员实现 |
| `tradingagents/agents/trader/trader.py` | 交易员实现 |
| `tradingagents/agents/managers/*.py` | 经理层实现 |
| `tradingagents/agents/risk_mgmt/*.py` | 风控辩论者实现 |
| `tradingagents/agents/utils/memory.py` | 记忆系统 |
| `tradingagents/graph/reflection.py` | 反思机制 |
| `tradingagents/default_config.py` | 默认配置 |

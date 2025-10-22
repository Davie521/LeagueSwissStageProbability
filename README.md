# League of Legends Worlds Swiss Stage Probability Calculator
# 英雄联盟世界赛瑞士轮抽签概率统计工具

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

A Python tool for calculating precise matchup probabilities in the 2025 League of Legends World Championship Swiss Stage format.

### Overview

This tool calculates the probability of two teams facing each other in the next round of the Swiss Stage, considering all tournament rules and constraints.

## ✨ Features

### Core Capabilities
- 📊 **Live Standings**: View current records and status of all teams
- 🎯 **Group Display**: See next round's potential matchup groups
- 🎲 **Matchup Probability**: Calculate precise probability of any two teams meeting
- 📈 **All Opponents Analysis**: View a team's probability against all possible opponents
- 🔮 **Advancement Simulation**: Monte Carlo simulation of qualification/elimination odds
- 🔍 **Team Details**: View match history and past opponents

### 🚀 v2.1: Detailed Pairing Schemes Display

When calculating cross-group probabilities, the tool now shows **all possible pairing schemes** for each scenario and highlights which schemes contain the target matchup.

**Features:**
- ✅ Display all valid pairing schemes
- ✅ Green highlight for schemes containing the target matchup
- ✅ Gray display for schemes without the target matchup
- ✅ Only show scenarios with probability > 0%
- ✅ Help users understand the probability calculation basis

**User Value:**
1. **Transparency** - See how probabilities are calculated
2. **Verifiability** - Manually verify pairing scheme validity
3. **Educational** - Understand Swiss format rules and rematch restrictions
4. **Strategic Reference** - Know all possible matchup combinations

### 🎯 v2.0: Interactive Cross-Group Probability Calculation

Intelligent interactive probability system that precisely calculates the probability of two teams from different groups meeting.

**Core Features:**
- ✅ Intelligent identification of pending matches
- ✅ Automatic impact factor analysis
- ✅ Only prompts for user input when necessary
- ✅ Enumerates all possible match result combinations
- ✅ Precise pairing probability considering rematch restrictions
- ✅ Weighted average probability calculation
- ✅ Detailed explanations

## 🚀 Quick Start

```bash
# Using uv (recommended)
uv sync
uv run python -m src.cli

# Or using pip
pip install -r requirements.txt
python -m src.cli
```

## 📖 Usage Examples

```bash
# Run main program
uv run python -m src.cli

# Run tests
uv run python test_swiss.py
```

## 🧮 How Probability Calculation Works

### Key Concept: Conditional Probability

**Important**: The probabilities calculated by this tool are **conditional probabilities** - they represent the chance of two teams meeting **given that both teams reach the target record group**.

#### Example Scenario:

Suppose **BLG is 1-2** and **TES is 2-1**. You want to know: "What's the probability BLG faces TES?"

**What the tool calculates:**
- **P(BLG vs TES | both teams reach 2-2) = 33.3%**
- This means: "**IF** BLG wins their next match (→ 2-2) **AND** TES loses their next match (→ 2-2), there's a 33.3% chance they face each other in the 2-2 bracket"

**What the tool does NOT calculate:**
- NOT: P(BLG reaches 2-2) × P(TES reaches 2-2) × P(they meet | both 2-2)
- NOT: The overall probability considering whether they actually reach 2-2

**Why this matters:**
- BLG might only have a 40% chance to win (reach 2-2)
- TES might only have a 30% chance to lose (reach 2-2)
- The overall probability would be: 40% × 30% × 33.3% = 4%
- But the tool shows **33.3%** - the probability **after** they both enter the 2-2 group

### Two Scenarios

#### 1. Same Group (Direct Calculation)

When both teams are already in the same record group (e.g., both are 2-1):

```
Probability = (Pairings containing Team A vs Team B) / (Total valid pairings)
```

**Example**: If there are 6 teams in the 2-1 group:
- Total valid pairings: 15 possible complete pairing schemes
- Pairings with BLG vs TES: 5 schemes
- Probability: 5/15 = 33.3%

#### 2. Cross-Group (Multi-Scenario Weighted Average)

When teams are in different groups (e.g., BLG is 1-2, TES is 2-1), the calculation involves:

**Step 1: Prerequisites**
- What must happen for them to meet? (e.g., BLG must win → 2-2, TES must lose → 2-2)

**Step 2: Impact Matches**
- Identify other pending matches that affect the 2-2 group composition
- Example: If G2 (1-2) and T1 (2-1) also have pending matches, their results change who's in the 2-2 group

**Step 3: Scenario Enumeration**
For each combination of impact match results:
- User provides win probability estimates (e.g., "G2 has 60% to beat opponent")
- Calculate scenario occurrence probability
- Simulate final group composition
- Calculate pairing probability within that group

**Step 4: Weighted Average**
```
Final Probability = Σ [P(scenario occurs) × P(Team A vs Team B | scenario)]
```

**Example**:
```
Scenario 1 (G2 wins, T1 loses): 60% × 40% = 24% chance
  → 2-2 group: BLG, TES, G2, T1 (4 teams)
  → P(BLG vs TES | this group) = 1/3
  → Contributes: 24% × 33.3% = 8%

Scenario 2 (G2 wins, T1 wins): 60% × 60% = 36% chance
  → 2-2 group: BLG, TES, G2 (3 teams)
  → P(BLG vs TES | this group) = 100%
  → Contributes: 36% × 100% = 36%

... (other scenarios)

Final Probability = 8% + 36% + ... = 45.2%
```

### Swiss Stage Rules

The calculation respects all tournament rules:

1. **Same Record Matching**: Teams with X-Y record only face other X-Y teams
2. **No Rematches**: Teams that already played cannot meet again (enforced via `opponents_played` set)
3. **Win Threshold**: 3 wins = qualified, 3 losses = eliminated

### Algorithm Details

- **Backtracking**: Generates all valid complete pairings for a group
- **Time Complexity**: O(2^n × m!!), where n = impact matches, m = teams in group
- **Typical Performance**: < 1 second for 2-4 impact matches with 4-6 teams

### Important Assumptions

1. **Independence**: Match outcomes are assumed independent (no team strength modeling)
2. **User Input**: Win probability estimates for pending matches come from user judgment
3. **Single-Step**: Only considers teams reaching target group in one match (no multi-step paths)

## 💡 Core Algorithms

- **Same Record Principle**: Only teams with identical records can face each other
- **No Rematch Principle**: Teams that already played cannot meet again
- **Backtracking Algorithm**: Enumerates all valid pairing schemes
- **Probability Calculation**: Target pairings / Total valid pairings

## 📦 Project Structure

```
src/
├── models.py            # Data models (Team, Match, SwissStage)
├── swiss_engine.py      # Probability calculation engine
├── worlds_2025_data.py  # Current tournament data
└── cli.py               # Interactive CLI interface
```

## 🎮 Current Tournament State

Based on the state after Round 4 of the 2025 Worlds Swiss Stage.

For more details, see the source code and documentation.

---

<a name="中文"></a>
## 中文

一个用于计算2025英雄联盟世界赛瑞士轮抽签概率的Python工具，可以分析队伍在下一轮相遇的精确概率。

## ✨ 功能特点

### 核心功能
- 📊 **实时积分榜**: 查看当前所有队伍的战绩和状态
- 🎯 **分组显示**: 查看下一轮可能的对阵分组
- 🎲 **对阵概率**: 计算任意两支队伍相遇的精确概率
- 📈 **全对手分析**: 某队与所有可能对手的匹配概率
- 🔮 **晋级模拟**: 蒙特卡洛模拟晋级/淘汰概率
- 🔍 **队伍详情**: 查看比赛历史和已交手队伍

### 🚀 v2.1 新功能：详细配对方案展示

在计算跨组相遇概率时，现在会展示**每种情况下的所有配对方案**，并清楚标注哪些方案包含目标对阵。

**功能特点：**
- ✅ 展示所有有效配对方案
- ✅ 绿色高亮包含目标对阵的方案
- ✅ 灰色显示不包含目标对阵的方案
- ✅ 只显示发生概率 > 0% 的情况
- ✅ 帮助用户理解概率计算依据

**用户价值：**
1. **透明度提升** - 看到概率是如何计算出来的
2. **可验证性** - 可以人工检查配对方案的合理性
3. **学习价值** - 理解瑞士轮配对规则和已交手限制
4. **战略参考** - 了解所有可能的对阵组合

### 🎯 v2.0 功能：交互式跨组概率计算

实现了智能的交互式概率计算系统，可以精确计算两支不在同一分组的队伍相遇的概率。

**核心特性：**
- ✅ 智能识别待定比赛
- ✅ 自动分析影响因素
- ✅ 只在必要时询问用户输入
- ✅ 枚举所有可能的比赛结果组合
- ✅ 考虑已交手限制的精确配对概率
- ✅ 加权平均概率计算
- ✅ 详细的解释说明

## 🚀 快速开始

```bash
# 使用 uv (推荐)
uv sync
uv run python -m src.cli

# 或使用 pip
pip install -r requirements.txt
python -m src.cli
```

## 📖 使用示例

```bash
# 运行主程序
uv run python -m src.cli

# 运行测试
uv run python test_swiss.py
```

## 🧮 概率计算原理详解

### 核心概念：条件概率

**重要说明**：本工具计算的概率是**条件概率** - 表示在两支队伍都进入目标战绩分组的前提下，他们相遇的概率。

#### 具体例子：

假设 **BLG当前战绩1-2**，**TES当前战绩2-1**。你想知道："BLG和TES相遇的概率是多少？"

**工具计算的是：**
- **P(BLG vs TES | 两队都进入2-2组) = 33.3%**
- 意思是："**如果** BLG赢下一场（→ 2-2）**并且** TES输掉下一场（→ 2-2），那么他们在2-2组相遇的概率是33.3%"

**工具不计算的是：**
- 不是：P(BLG到达2-2) × P(TES到达2-2) × P(相遇 | 都在2-2)
- 不是：考虑他们是否真的能到达2-2组的总体概率

**为什么这很重要：**
- BLG可能只有40%的概率赢下一场（到达2-2）
- TES可能只有30%的概率输掉下一场（到达2-2）
- 总体概率应该是：40% × 30% × 33.3% = 4%
- 但工具显示的是 **33.3%** - 这是他们**进入2-2组之后**相遇的概率

### 两种计算场景

#### 1. 同组计算（直接计算）

当两支队伍已经在同一战绩分组时（例如都是2-1）：

```
概率 = 包含队伍A vs 队伍B的配对方案数 / 总有效配对方案数
```

**示例**：如果2-1组有6支队伍：
- 总有效配对方案数：15种完整配对方案
- 包含BLG vs TES的方案：5种
- 概率：5/15 = 33.3%

#### 2. 跨组计算（多情景加权平均）

当队伍在不同分组时（例如BLG是1-2，TES是2-1），计算过程包括：

**步骤1：前置条件**
- 他们要相遇需要什么？（例如：BLG必须赢 → 2-2，TES必须输 → 2-2）

**步骤2：影响比赛**
- 识别其他会影响2-2组成员的待定比赛
- 例如：如果G2 (1-2) 和T1 (2-1) 也有待定比赛，他们的结果会改变谁在2-2组

**步骤3：情景枚举**
对于每种影响比赛结果的组合：
- 用户提供胜率估计（例如："G2有60%概率赢对手"）
- 计算该情景发生的概率
- 模拟最终的分组构成
- 计算该分组内的配对概率

**步骤4：加权平均**
```
最终概率 = Σ [P(情景发生) × P(队伍A vs 队伍B | 该情景)]
```

**示例**：
```
情景1（G2赢，T1输）：60% × 40% = 24% 概率
  → 2-2组：BLG, TES, G2, T1（4支队伍）
  → P(BLG vs TES | 该分组) = 1/3
  → 贡献：24% × 33.3% = 8%

情景2（G2赢，T1赢）：60% × 60% = 36% 概率
  → 2-2组：BLG, TES, G2（3支队伍）
  → P(BLG vs TES | 该分组) = 100%
  → 贡献：36% × 100% = 36%

...（其他情景）

最终概率 = 8% + 36% + ... = 45.2%
```

### 瑞士轮规则

计算遵循所有比赛规则：

1. **同战绩对阵**：只有X-Y战绩相同的队伍才会对阵
2. **不重复对阵**：已经交过手的队伍不会再次相遇（通过`opponents_played`集合强制执行）
3. **晋级门槛**：3胜=晋级，3负=淘汰

### 算法细节

- **回溯算法**：生成一个分组的所有有效完整配对方案
- **时间复杂度**：O(2^n × m!!)，其中n = 影响比赛数，m = 分组队伍数
- **典型性能**：对于2-4场影响比赛、4-6支队伍的情况 < 1秒

### 重要假设

1. **独立性**：假设比赛结果相互独立（不考虑队伍实力建模）
2. **用户输入**：待定比赛的胜率估计来自用户判断
3. **单步限制**：仅考虑队伍通过一场比赛到达目标分组（不考虑多步路径）

## 💡 核心算法

- **同战绩原则**: 只有相同战绩的队伍才会对战
- **不重复原则**: 已经交手的队伍不会再次相遇
- **回溯算法**: 枚举所有有效配对方案
- **概率计算**: 目标配对数 / 总配对方案数

## 📦 项目结构

```
src/
├── models.py            # 数据模型（Team, Match, SwissStage）
├── swiss_engine.py      # 概率计算引擎
├── worlds_2025_data.py  # 当前赛况数据
└── cli.py               # 交互式命令行界面
```

## 🎮 当前赛况

基于2025世界赛瑞士轮第4轮结束后的状态。

更多详情请查看源代码和文档。

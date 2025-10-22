# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

League Swiss Stage Probability Calculator - 英雄联盟世界赛瑞士轮抽签概率统计工具

A Python application that calculates precise probabilities for team matchups in the 2025 League of Legends World Championship Swiss Stage format. The system features an **interactive probability calculation engine** that intelligently handles cross-group matchup scenarios.

## Development Commands

### Running the Application

```bash
# Run main CLI (recommended)
uv run python run.py

# Alternative
uv run python -m src.cli
```

### Testing

```bash
# Run all tests
uv run python test_interactive_probability.py
uv run python test_final.py

# Run basic tests
uv run python test_swiss.py
uv run python test_probability.py
```

### Package Management

```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package>
```

## Architecture Overview

### Core Components

**Three-layer architecture:**

1. **Data Layer** (`src/models.py`): Core domain models
   - `Team`: Tracks wins, losses, opponents_played, match_history
   - `Match`: Represents individual games
   - `SwissStage`: Manages tournament state

2. **Engine Layer** (`src/swiss_engine.py`): Probability calculation algorithms
   - `SwissDrawEngine`: Pairing generation with backtracking
   - `ProbabilityCalculator`: Main probability computation engine

3. **Interface Layer** (`src/cli.py`): User interaction via Rich library

### Key Data Structures

**Team State:**
- `opponents_played: Set[str]` - Enforces "no-rematch" rule
- `match_history: List[Tuple[str, Optional[bool]]]` - `None` indicates pending matches
- Active teams: `not is_qualified and not is_eliminated`

**Swiss Stage Rules:**
- Same record only: Teams with X-Y record only face other X-Y teams
- No rematches: `can_play_against()` checks `opponents_played`
- Win threshold: 3 wins = qualified, 3 losses = eliminated

## Interactive Probability System

### When User Input is Required

The system intelligently determines when to ask for user input:

1. **Same Group** → Calculate directly, no input needed
2. **Cross-Group with Pending Matches** → Ask for win probability estimates
3. **Cannot Meet** → Explain why, no input needed

### Calculation Flow

**For cross-group matchups (e.g., BLG 1-2 vs TES 2-1):**

1. **Prerequisites Identification**: What results are necessary?
   - BLG must win → reach 2-2
   - TES must lose → reach 2-2

2. **Impact Matches Identification**: What other pending matches affect the target group?
   - Filters out prerequisite matches
   - Only includes matches that change group composition

3. **Scenario Enumeration**: 2^n combinations of impact match results
   - Each scenario has occurrence probability (user input)
   - Simulates group composition via `_simulate_group_with_results()`

4. **Pairing Probability**: For each scenario's group composition
   - Backtracking algorithm generates all valid pairings
   - Respects `opponents_played` constraints
   - Counts pairings containing target matchup

5. **Weighted Average**:
   ```
   final_probability = Σ(scenario_probability × pairing_probability)
   ```

### Key Methods

**`calculate_cross_group_probability_interactive()`** - Core interactive calculator
- Input: `team1_name`, `team2_name`, `win_probabilities: Optional[Dict]`
- Returns: Detailed dict with scenarios, probabilities, explanations
- If `win_probabilities is None`: Returns `need_input: True` to trigger UI prompts

**`_identify_pending_matches()`** - Finds all matches with `won = None`

**`_find_path_to_target_group()`** - Determines if team can reach a record (limited to single-step moves)

**`_identify_impact_matches()`** - Filters pending matches that affect target group, excluding prerequisites

**`_simulate_group_with_results()`** - Deep copies stage and applies match results to simulate final group composition

**`_calculate_pairing_probability()`** - Uses `SwissDrawEngine.generate_valid_pairings()` to enumerate all valid pairings respecting rematch constraints

## Data Management

### Current Tournament State

`src/worlds_2025_data.py` contains:
- `create_worlds_2025_teams()`: List of all 16 teams
- `get_current_results()`: Dict of team records with match history
  - Format: `{team_name: (wins, losses, [(opponent, result)])}`
  - `result` can be `True` (win), `False` (loss), or `None` (pending)
- `load_current_swiss_stage()`: Loads current state into `SwissStage` object

**To update tournament data**: Edit `get_current_results()` in `worlds_2025_data.py`

## Algorithm Details

### Pairing Generation (Backtracking)

`SwissDrawEngine.generate_valid_pairings()`:
- Recursive backtracking to find all valid complete pairings
- Constraint: `team1.can_play_against(team2)` (checks opponents_played)
- Optimized with `is_valid_pairing()` pruning
- Time: O(n!!), where n is team count in group

### Probability Calculation

**Same Group:**
```
P(A vs B) = (pairings containing A-B) / (total valid pairings)
```

**Cross Group:**
```
P(A vs B) = Σ P(scenario_i occurs) × P(A vs B | scenario_i)
```

Where `scenario_i` represents a specific outcome for all impact matches.

## Testing Strategy

**Test Coverage:**
1. `test_same_group_matchup()` - Direct pairing (100% probability)
2. `test_cross_group_interactive()` - Multi-scenario with weighted average
3. `test_cannot_meet()` - Elimination/qualification edge cases
4. `test_pending_matches_identification()` - Correct extraction of pending matches
5. `test_group_simulation()` - Accurate state simulation
6. `test_pairing_probability_with_restrictions()` - Rematch constraints
7. `test_detailed_pairings.py` - Detailed pairing display validation

## Detailed Pairing Display Feature (v2.1)

**New in CLI**: When calculating cross-group probabilities, the system now displays **all pairing schemes** for each scenario.

**Implementation** (`src/cli.py` lines 217-273):
- For scenarios with probability > 0%, regenerates all valid pairings
- Classifies pairings into "favorable" (contains target matchup) vs "other"
- Uses Rich markup to highlight:
  - ✅ Green for pairings containing the target matchup
  - ❌ Gray for pairings without the target matchup
- Only displays scenarios with occurrence probability > 0%
- Shows all pairings so users understand probability calculation basis

**Feature Highlights:**
- ✅ Display all valid pairing schemes
- ✅ Green highlight for schemes containing target matchup
- ✅ Gray display for schemes without target matchup
- ✅ Only show scenarios with probability > 0%
- ✅ Help users understand probability calculation basis

**Example Output:**
```
情况 1 (发生概率 100.0%):
2-2组队伍: BLG, TES, T1, MKOI, FLY, CFO

✓ 包含 BLG vs TES 的方案 (1 种):
  方案 1: BLG-TES, T1-FLY, MKOI-CFO

✗ 不包含该对阵的方案 (8 种):
  方案 1: BLG-T1, TES-FLY, MKOI-CFO
  方案 2: BLG-T1, TES-MKOI, FLY-CFO
  ...（共8种）
```

**User Value:**
1. **Transparency** - See how probabilities are calculated
2. **Verifiability** - Manually verify pairing scheme validity
3. **Educational Value** - Understand Swiss format rules and rematch restrictions
4. **Strategic Reference** - Know all possible matchup combinations

**Performance Impact:**
- Computation time: Negligible (pairing schemes already generated during probability calculation)
- Display time: < 0.1s (even for complex scenarios)
- Memory usage: Slight increase (temporary storage for classified pairings)

## Common Patterns

### Adding New Functionality

1. **New Calculation Method**: Add to `ProbabilityCalculator` class in `swiss_engine.py`
2. **New UI Feature**: Modify `src/cli.py` functions (use Rich library for formatting)
3. **Data Update**: Edit `get_current_results()` in `worlds_2025_data.py`

### Rich Markup Issues

When printing exceptions or strings with brackets:
```python
# WRONG - brackets conflict with Rich markup
console.print(f"[dim]{traceback.format_exc()}[/dim]")

# CORRECT - use style parameter
console.print(traceback.format_exc(), style="dim")
```

### Deep Copy for Simulation

Always use `copy.deepcopy()` when simulating match results to avoid mutating original state:
```python
simulated_stage = copy.deepcopy(self.stage)
```

## Performance Considerations

- **Time Complexity**: O(2^n × m!), where n = impact matches, m = teams in group
- **Typical Performance**: < 1 second for 2-4 impact matches with 4-6 teams
- **Optimization**: Early pruning in backtracking, graph-based validity checks

## Important Notes

- Team names are **case-sensitive** but CLI converts to uppercase
- Match history order matters - last match with `None` is considered "next match"
- Single-step limitation: `_find_path_to_target_group()` only handles one match to reach target
- Probability assumes independent match outcomes (no strength modeling)

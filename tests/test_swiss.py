"""
测试瑞士轮概率计算
"""
from src.worlds_2025_data import load_current_swiss_stage, get_next_round_matchups
from src.swiss_engine import ProbabilityCalculator
from rich import print


def test_basic_functionality():
    """测试基本功能"""
    print("[bold cyan]测试瑞士轮概率计算器[/bold cyan]\n")

    # 加载当前数据
    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    print(f"[yellow]总队伍数:[/yellow] {len(stage.teams)}")
    print(f"[green]已晋级队伍:[/green] {[t.name for t in stage.get_qualified_teams()]}")
    print(f"[red]已淘汰队伍:[/red] {[t.name for t in stage.get_eliminated_teams()]}")
    print(f"[cyan]活跃队伍数:[/cyan] {len(stage.get_active_teams())}\n")

    # 测试下一轮分组
    print("[bold]下一轮分组:[/bold]")
    for record, teams, pending in get_next_round_matchups():
        print(f"  {record}: {teams}")
        if pending:
            print(f"    待定对阵: {pending}")

    print("\n[bold]测试概率计算:[/bold]")

    # 测试 2-1 组队伍相遇概率
    teams_2_1 = stage.get_teams_by_record(2, 1)
    if len(teams_2_1) >= 2:
        team1 = teams_2_1[0]
        team2 = teams_2_1[1]

        result = calculator.calculate_matchup_probability(team1.name, team2.name)
        print(f"  {team1.name} vs {team2.name}: {result['probability']:.1%}")

    # 测试某队所有对手概率
    if teams_2_1:
        test_team = teams_2_1[0]
        print(f"\n[bold]{test_team.name} 所有可能对手:[/bold]")

        all_probs = calculator.calculate_all_matchup_probabilities(test_team.name)
        for opponent, prob in sorted(all_probs.items(), key=lambda x: x[1], reverse=True):
            print(f"  vs {opponent}: {prob:.1%}")

    # 测试无法相遇的情况
    print("\n[bold]测试规则限制:[/bold]")

    # 已经打过的队伍
    team = stage.get_team_by_name("T1")
    if team and team.opponents_played:
        opponent = list(team.opponents_played)[0]
        result = calculator.calculate_matchup_probability("T1", opponent)
        print(f"  T1 vs {opponent} (已交手): {result['probability']:.1%}")

    # 不同战绩的队伍
    teams_2_1 = stage.get_teams_by_record(2, 1)
    teams_1_2 = stage.get_teams_by_record(1, 2)
    if teams_2_1 and teams_1_2:
        result = calculator.calculate_matchup_probability(teams_2_1[0].name, teams_1_2[0].name)
        print(f"  {teams_2_1[0].name} (2-1) vs {teams_1_2[0].name} (1-2): {result['probability']:.1%}")


def test_simulation():
    """测试晋级概率模拟"""
    print("\n[bold cyan]测试晋级概率模拟[/bold cyan]\n")

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 测试不同战绩队伍的晋级概率
    test_cases = [
        (2, 1),  # 晋级边缘
        (1, 2),  # 淘汰边缘
        (2, 2),  # 生死战
    ]

    for wins, losses in test_cases:
        teams = stage.get_teams_by_record(wins, losses)
        if teams:
            team = teams[0]
            print(f"[yellow]测试 {team.name} ({team.record}):[/yellow]")

            result = calculator.simulate_advancement_probability(team.name, 1000)
            print(f"  晋级概率: {result['qualify']:.1%}")
            print(f"  淘汰概率: {result['eliminate']:.1%}\n")


def test_rules():
    """测试瑞士轮规则"""
    print("[bold cyan]测试瑞士轮规则[/bold cyan]\n")

    stage = load_current_swiss_stage()

    # 测试每个队伍的可对战队伍
    for team in stage.get_active_teams():
        valid_opponents = []
        same_record_teams = stage.get_teams_by_record(team.wins, team.losses)

        for opponent in same_record_teams:
            if team.can_play_against(opponent):
                valid_opponents.append(opponent.name)

        print(f"{team.name} ({team.record}) 可对战: {valid_opponents}")


if __name__ == "__main__":
    print("=" * 50)
    test_basic_functionality()
    print("=" * 50)
    test_simulation()
    print("=" * 50)
    test_rules()
    print("=" * 50)
    print("\n[green]✅ 所有测试完成！[/green]")
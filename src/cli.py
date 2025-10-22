"""
命令行界面
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from rich.markup import escape
import time

from .worlds_2025_data import (
    load_current_swiss_stage,
    get_next_round_matchups
)
from .swiss_engine import ProbabilityCalculator


console = Console()


def display_current_standings():
    """显示当前积分榜"""
    stage = load_current_swiss_stage()

    # 创建表格
    table = Table(title="2025英雄联盟世界赛瑞士轮积分榜", show_header=True, header_style="bold magenta")
    table.add_column("队伍", style="cyan", width=8)
    table.add_column("战绩", justify="center", style="white")
    table.add_column("状态", justify="center")
    table.add_column("对战历史", style="dim")

    # 按战绩排序
    teams_sorted = sorted(stage.teams, key=lambda t: (t.wins, -t.losses), reverse=True)

    for team in teams_sorted:
        status = ""
        status_style = "white"

        if team.is_qualified:
            status = "✅ 已晋级"
            status_style = "green"
        elif team.is_eliminated:
            status = "❌ 已淘汰"
            status_style = "red"
        else:
            status = "⚔️ 比赛中"
            status_style = "yellow"

        # 格式化对战历史，每场比赛固定宽度为6个字符
        history = []
        for opponent, won in team.match_history:
            # 计算对手名称需要的填充
            # 格式: "✓ XXXX" 总共6个字符，符号1个+空格1个+队名4个
            padded_opponent = opponent.ljust(4)
            if won is None:
                # 待定比赛，显示为亮灰色
                history.append(f"[bright_black]- {padded_opponent}[/bright_black]")
            elif won:
                history.append(f"[green]✓ {padded_opponent}[/green]")
            else:
                history.append(f"[red]✗ {padded_opponent}[/red]")

        table.add_row(
            team.name,
            f"{team.wins}-{team.losses}",
            f"[{status_style}]{status}[/{status_style}]",
            " | ".join(history)
        )

    console.print(table)


def display_next_round_groups():
    """显示下一轮分组"""
    matchups = get_next_round_matchups()

    console.print("\n[bold cyan]下一轮可能的对阵组:[/bold cyan]\n")

    for record, confirmed_teams, pending_matchups in matchups:
        # 构建显示内容
        display_items = []

        # 添加已确定的队伍
        display_items.extend(confirmed_teams)

        # 添加待定对阵（显示为 "(队伍A vs 队伍B) 胜者"）
        for team1, team2 in pending_matchups:
            display_items.append(f"({team1} vs {team2}) 胜者")

        panel_content = ", ".join(display_items)
        panel = Panel(panel_content, title=record, title_align="left", border_style="cyan")
        console.print(panel)


def get_team_input(prompt_text: str, active_teams: list) -> str:
    """
    获取队伍输入，支持：
    1. 直接输入队伍名称（如 "BLG"）
    2. 输入序号（如 "1"）

    Args:
        prompt_text: 提示文本
        active_teams: 活跃队伍列表

    Returns:
        队伍名称（大写）
    """
    while True:
        user_input = Prompt.ask(prompt_text).strip()

        # 尝试作为序号解析
        try:
            index = int(user_input)
            if 1 <= index <= len(active_teams):
                return active_teams[index - 1]
            else:
                console.print(f"[red]序号无效，请输入 1-{len(active_teams)} 之间的数字[/red]")
                continue
        except ValueError:
            # 不是数字，作为队伍名称处理
            team_name = user_input.upper()
            if team_name in active_teams:
                return team_name
            else:
                console.print(f"[red]队伍 '{user_input}' 不在活跃队伍列表中，请重新输入[/red]")
                continue


def calculate_single_matchup():
    """计算两队相遇概率（支持交互式输入）"""
    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 获取活跃队伍
    active_teams = [t.name for t in stage.get_active_teams()]

    if not active_teams:
        console.print("[red]当前没有活跃的队伍！[/red]")
        return

    console.print("\n[bold]当前仍在比赛的队伍:[/bold]")
    for i, team in enumerate(active_teams, 1):
        team_obj = stage.get_team_by_name(team)
        console.print(f"  {i}. {team} ({team_obj.record})")

    team1 = get_team_input("\n请输入第一支队伍名称或序号", active_teams)
    team2 = get_team_input("请输入第二支队伍名称或序号", active_teams)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]分析中...", total=None)

            # 第一步：初步计算
            result = calculator.calculate_matchup_probability(team1, team2)

            progress.update(task, completed=100)

        console.print("\n" + "="*60)

        # 检查是否需要交互式输入
        if result.get('need_interactive'):
            # 需要用户输入影响因素的比赛胜率
            interactive_data = result['interactive_data']

            console.print(f"[bold yellow]⚠️  两队当前不在同一分组[/bold yellow]")
            console.print(f"[yellow]{result['reason']}[/yellow]\n")

            console.print(f"[bold cyan]✨ 但可以通过交互式分析计算精确概率！[/bold cyan]\n")

            # 显示必要条件
            console.print("[bold magenta]必要前提条件：[/bold magenta]")
            for prereq in interactive_data['prerequisites']:
                if prereq['pending_match']:
                    console.print(f"  • {prereq['team']} ({prereq['current_record']}) 必须: {prereq['needs']}")
                    console.print(f"    [dim]对手: {prereq['pending_match']['opponent']}[/dim]")

            console.print()

            # 显示影响因素
            if interactive_data['impact_matches']:
                console.print("[bold magenta]以下待定比赛会影响目标分组的构成：[/bold magenta]\n")
                for i, match in enumerate(interactive_data['impact_matches'], 1):
                    console.print(f"  {i}. [cyan]{match['team1']} vs {match['team2']}[/cyan]")
                    console.print(f"     当前战绩: {match['team1_record']} vs {match['team2_record']}")

                console.print("\n" + "━"*60)
                console.print("[bold yellow]请输入各场比赛的胜率估算（用于加权计算）：[/bold yellow]\n")

                # 收集胜率输入
                win_probabilities = {}
                for match in interactive_data['impact_matches']:
                    t1, t2 = match['team1'], match['team2']
                    prompt_text = f"{t1} 战胜 {t2} 的概率 [0-100%，默认50]"
                    prob_input = Prompt.ask(prompt_text, default="50")
                    try:
                        prob = float(prob_input) / 100.0
                        prob = max(0.0, min(1.0, prob))  # 限制在 0-1
                        match_key = tuple(sorted([t1, t2]))
                        win_probabilities[match_key] = prob
                    except ValueError:
                        console.print(f"[yellow]输入无效，使用默认值 50%[/yellow]")
                        match_key = tuple(sorted([t1, t2]))
                        win_probabilities[match_key] = 0.5

                console.print("\n" + "━"*60)
                console.print("[cyan]正在计算所有可能情况...[/cyan]\n")

                # 重新计算，带上用户输入的胜率
                final_result = calculator.calculate_cross_group_probability_interactive(
                    team1, team2, win_probabilities
                )

                # 显示详细结果
                if final_result['scenarios']:
                    console.print(f"[bold green]✨ 加权平均相遇概率: {final_result['weighted_probability']:.1%}[/bold green]\n")

                    console.print("[bold cyan]所有可能情况分析：[/bold cyan]\n")

                    # 创建汇总表格
                    summary_table = Table(show_header=True, header_style="bold magenta")
                    summary_table.add_column("情况", style="cyan", width=8)
                    summary_table.add_column("新增队伍", style="yellow", width=20)
                    summary_table.add_column("发生概率", justify="right", style="green", width=10)
                    summary_table.add_column("配对方案", justify="center", width=12)
                    summary_table.add_column("相遇概率", justify="right", style="bold green", width=10)

                    for i, scenario in enumerate(final_result['scenarios'], 1):
                        pairing_stats = scenario['pairing_stats']
                        pairing_info = f"{pairing_stats['favorable_pairings']}/{pairing_stats['total_pairings']}"

                        new_teams_str = ", ".join(scenario['new_teams']) if scenario['new_teams'] else "无新增"

                        summary_table.add_row(
                            f"情况 {i}",
                            new_teams_str,
                            f"{scenario['probability']:.1%}",
                            pairing_info,
                            f"{pairing_stats['probability']:.1%}"
                        )

                    console.print(summary_table)

                    # 显示每种情况的详细配对方案
                    console.print("\n" + "━"*60)
                    console.print("[bold cyan]详细配对方案：[/bold cyan]\n")

                    for i, scenario in enumerate(final_result['scenarios'], 1):
                        if scenario['probability'] > 0:  # 只显示有可能发生的情况
                            pairing_stats = scenario['pairing_stats']
                            console.print(f"[bold yellow]情况 {i}[/bold yellow] (发生概率 {scenario['probability']:.1%}):")
                            console.print(f"[dim]2-2组队伍: {', '.join(pairing_stats['teams'])}[/dim]\n")

                            # 重新生成该情况的所有配对方案用于展示
                            teams_in_group = [stage.get_team_by_name(t) for t in pairing_stats['teams']]
                            all_pairings = calculator.engine.generate_valid_pairings(teams_in_group)

                            if all_pairings:
                                # 分类配对方案
                                favorable_pairings = []
                                other_pairings = []

                                for pairing in all_pairings:
                                    has_target = False
                                    for pair in pairing:
                                        if (pair[0].name == team1 and pair[1].name == team2) or \
                                           (pair[0].name == team2 and pair[1].name == team1):
                                            has_target = True
                                            break

                                    if has_target:
                                        favorable_pairings.append(pairing)
                                    else:
                                        other_pairings.append(pairing)

                                # 显示包含目标对阵的方案
                                console.print(f"[green]✓ 包含 {team1} vs {team2} 的方案 ({len(favorable_pairings)} 种):[/green]")
                                for j, pairing in enumerate(favorable_pairings, 1):
                                    pairs_str = ", ".join([f"{p[0].name}-{p[1].name}" for p in pairing])
                                    # 高亮目标对阵
                                    pairs_str = pairs_str.replace(f"{team1}-{team2}", f"[bold green]{team1}-{team2}[/bold green]")
                                    pairs_str = pairs_str.replace(f"{team2}-{team1}", f"[bold green]{team2}-{team1}[/bold green]")
                                    console.print(f"  方案 {j}: {pairs_str}")

                                # 显示不包含目标对阵的方案
                                if other_pairings:
                                    console.print(f"\n[dim]✗ 不包含该对阵的方案 ({len(other_pairings)} 种):[/dim]")
                                    for j, pairing in enumerate(other_pairings, 1):
                                        pairs_str = ", ".join([f"{p[0].name}-{p[1].name}" for p in pairing])
                                        console.print(f"  [dim]方案 {j}: {pairs_str}[/dim]")

                            console.print()

                    console.print("━"*60)
                    console.print(f"[bold yellow]📌 说明：[/bold yellow]")
                    console.print("• 发生概率：该情况出现的概率（基于您输入的胜率）", style="dim")
                    console.print("• 配对方案：包含目标对阵的方案数 / 有效配对总数", style="dim")
                    console.print("• 相遇概率：在该情况下两队相遇的概率", style="dim")
                    console.print("• 加权平均：所有情况的相遇概率按发生概率加权平均", style="dim")
                    console.print("• 绿色高亮的配对方案包含目标对阵，灰色的不包含", style="dim")

            else:
                # 没有其他影响因素，直接计算
                final_result = calculator.calculate_cross_group_probability_interactive(
                    team1, team2, {}
                )

                if final_result['scenarios']:
                    scenario = final_result['scenarios'][0]
                    pairing_stats = scenario['pairing_stats']

                    console.print(f"[bold green]✨ 相遇概率: {pairing_stats['probability']:.1%}[/bold green]\n")
                    console.print(f"[dim]目标分组队伍: {', '.join(pairing_stats['teams'])}[/dim]")
                    console.print(f"[dim]有效配对方案: {pairing_stats['total_pairings']} 种[/dim]")
                    console.print(f"[dim]包含该对阵: {pairing_stats['favorable_pairings']} 种[/dim]")

        elif result['can_meet_directly']:
            # 在同一组，可以直接相遇
            console.print(f"[bold green]✨ {team1} vs {team2} 相遇概率: {result['probability']:.1%}[/bold green]\n")

            console.print("[bold cyan]详细分析：[/bold cyan]")
            console.print(result['explanation'])

            if result['pairing_stats']:
                stats = result['pairing_stats']
                console.print(f"\n[dim]该组队伍: {', '.join(stats['team_names'])}[/dim]")

        else:
            # 无法相遇
            console.print(f"[bold red]❌ {team1} 和 {team2} 无法相遇[/bold red]\n")

            console.print(f"[red]原因: {result['reason']}[/red]\n")

            if result['explanation']:
                console.print("[bold cyan]详细说明：[/bold cyan]")
                console.print(result['explanation'])

        console.print("="*60)

    except Exception as e:
        console.print(f"[red]错误: {escape(str(e))}[/red]")
        import traceback
        # 不使用markup格式化traceback，避免括号冲突
        console.print("[dim]详细错误信息:[/dim]")
        console.print(traceback.format_exc(), style="dim", markup=False)




@click.command()
def main():
    """英雄联盟世界赛瑞士轮抽签概率统计工具"""

    # 显示欢迎信息
    welcome_text = """
    [bold cyan]╔══════════════════════════════════════════╗[/bold cyan]
    [bold cyan]║  🏆 LOL世界赛瑞士轮概率计算器 v1.0 🏆  ║[/bold cyan]
    [bold cyan]╚══════════════════════════════════════════╝[/bold cyan]
    """
    console.print(welcome_text)

    while True:
        console.print("\n[bold yellow]功能选择:[/bold yellow]")
        console.print("  1. 📊 查看当前积分榜")
        console.print("  2. 🎯 查看下一轮分组")
        console.print("  3. 🎲 计算两队相遇概率")
        console.print("  0. 👋 退出")

        choice = Prompt.ask("\n请选择功能", choices=["0", "1", "2", "3"])

        if choice == "0":
            console.print("[yellow]感谢使用，再见！👋[/yellow]")
            break
        elif choice == "1":
            display_current_standings()
        elif choice == "2":
            display_next_round_groups()
        elif choice == "3":
            calculate_single_matchup()

        if choice != "0":
            if not Confirm.ask("\n继续使用其他功能吗？", default=True):
                console.print("[yellow]感谢使用，再见！👋[/yellow]")
                break


if __name__ == "__main__":
    main()
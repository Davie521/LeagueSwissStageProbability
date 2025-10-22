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
import time

from .worlds_2025_data import (
    load_current_swiss_stage,
    get_next_round_matchups,
    get_team_stats
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


def calculate_single_matchup():
    """计算两队相遇概率"""
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

    team1 = Prompt.ask("\n请输入第一支队伍名称").upper()
    team2 = Prompt.ask("请输入第二支队伍名称").upper()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]计算概率中...", total=None)

            # 计算概率（现在返回详细信息字典）
            result = calculator.calculate_matchup_probability(team1, team2)

            progress.update(task, completed=100)

        console.print("\n" + "="*60)

        # 显示结果
        if result['can_meet_directly']:
            # 在同一组，可以直接相遇
            console.print(f"[bold green]✨ {team1} vs {team2} 相遇概率: {result['probability']:.1%}[/bold green]\n")

            # 显示详细解释
            console.print("[bold cyan]详细分析：[/bold cyan]")
            console.print(result['explanation'])

            # 如果有配对统计信息，显示在表格中
            if result['pairing_stats']:
                stats = result['pairing_stats']
                console.print(f"\n[dim]该组队伍: {', '.join(stats['team_names'])}[/dim]")

        elif result['paths']:
            # 不在同一组，但有跨组相遇的可能
            console.print(f"[bold yellow]⚠️  两队当前不在同一分组[/bold yellow]")
            console.print(f"[yellow]{result['reason']}[/yellow]\n")

            console.print(f"[bold cyan]但仍有可能在后续轮次相遇！[/bold cyan]\n")

            # 显示详细解释
            console.print("[bold cyan]详细分析：[/bold cyan]")
            console.print(result['explanation'])

            # 显示路径表格
            console.print("\n[bold magenta]可能的相遇路径（条件概率）：[/bold magenta]")

            for i, path in enumerate(result['paths'], 1):
                console.print(f"\n[bold cyan]━━━━━ 路径 {i}：目标分组 {path['target_record']} ━━━━━[/bold cyan]")

                # 创建详细表格
                path_table = Table(show_header=True, header_style="bold yellow", box=None)
                path_table.add_column("队伍", style="cyan", width=10)
                path_table.add_column("当前战绩", justify="center", width=10)
                path_table.add_column("需要", style="yellow", width=30)

                team1_obj = stage.get_team_by_name(team1)
                team2_obj = stage.get_team_by_name(team2)

                path_table.add_row(
                    team1,
                    team1_obj.record,
                    path['team1_needs']
                )
                path_table.add_row(
                    team2,
                    team2_obj.record,
                    path['team2_needs']
                )

                console.print(path_table)

                # 显示条件概率
                console.print(f"\n  [bold green]✨ 相遇概率: {path['probability']:.1%}[/bold green]")
                console.print(f"     [dim]（假设两队都成功到达 {path['target_record']} 组的前提下）[/dim]")

            console.print(f"\n[bold yellow]📌 重要说明：[/bold yellow]")
            console.print("[dim]上述概率为条件概率，表示\"假设两队都到达目标分组\"的前提下相遇的概率。")
            console.print("实际相遇概率还需要考虑两队各自到达目标分组的可能性（取决于比赛结果）。[/dim]")

        else:
            # 无法相遇
            console.print(f"[bold red]❌ {team1} 和 {team2} 无法相遇[/bold red]\n")

            console.print(f"[red]原因: {result['reason']}[/red]\n")

            if result['explanation']:
                console.print("[bold cyan]详细说明：[/bold cyan]")
                console.print(result['explanation'])

        console.print("="*60)

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def calculate_all_matchups():
    """计算某队所有可能的对手概率"""
    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 获取活跃队伍
    active_teams = [t.name for t in stage.get_active_teams()]

    if not active_teams:
        console.print("[red]当前没有活跃的队伍！[/red]")
        return

    console.print("\n[bold]当前仍在比赛的队伍:[/bold]")
    for team in active_teams:
        team_obj = stage.get_team_by_name(team)
        console.print(f"  • {team} ({team_obj.record})")

    team_name = Prompt.ask("\n请输入队伍名称").upper()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]计算所有可能对手的概率...", total=None)

            probabilities = calculator.calculate_all_matchup_probabilities(team_name)

            progress.update(task, completed=100)

        if probabilities:
            # 按概率排序
            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)

            table = Table(title=f"{team_name} 下一轮可能的对手", show_header=True)
            table.add_column("对手", style="cyan", width=10)
            table.add_column("概率", justify="right", style="yellow")
            table.add_column("概率条", width=30)

            for opponent, prob in sorted_probs:
                # 创建概率条
                bar_length = int(prob * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)

                table.add_row(
                    opponent,
                    f"{prob:.1%}",
                    f"[cyan]{bar}[/cyan]"
                )

            console.print("\n")
            console.print(table)
        else:
            console.print(f"[yellow]⚠️ {team_name} 没有可能的对手（可能已经晋级或淘汰）[/yellow]")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


def simulate_advancement():
    """模拟晋级概率"""
    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    active_teams = [t.name for t in stage.get_active_teams()]

    if not active_teams:
        console.print("[red]当前没有活跃的队伍！[/red]")
        return

    console.print("\n[bold]当前仍在比赛的队伍:[/bold]")
    for team in active_teams:
        team_obj = stage.get_team_by_name(team)
        console.print(f"  • {team} ({team_obj.record})")

    team_name = Prompt.ask("\n请输入要模拟的队伍名称").upper()

    try:
        num_sims = int(Prompt.ask("模拟次数", default="10000"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]模拟 {num_sims} 次...", total=None)

            result = calculator.simulate_advancement_probability(team_name, num_sims)

            progress.update(task, completed=100)

        team_obj = stage.get_team_by_name(team_name)

        # 创建结果面板
        content = f"""
队伍: [bold cyan]{team_name}[/bold cyan]
当前战绩: [yellow]{team_obj.record}[/yellow]

[green]晋级概率: {result['qualify']:.1%}[/green]
[red]淘汰概率: {result['eliminate']:.1%}[/red]

基于 {num_sims} 次模拟
        """

        panel = Panel(content, title="模拟结果", border_style="green")
        console.print("\n")
        console.print(panel)

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")


def view_team_details():
    """查看队伍详情"""
    stage = load_current_swiss_stage()

    team_name = Prompt.ask("请输入队伍名称").upper()
    stats = get_team_stats(team_name)

    if not stats:
        console.print(f"[red]队伍 {team_name} 不存在！[/red]")
        return

    # 创建详情面板
    status = "⚔️ 比赛中"
    if stats['is_qualified']:
        status = "✅ 已晋级"
    elif stats['is_eliminated']:
        status = "❌ 已淘汰"

    # 格式化比赛历史
    history_text = ""
    for i, (opponent, won) in enumerate(stats['match_history'], 1):
        if won is None:
            result = "-"
            color = "bright_black"
        elif won:
            result = "✓"
            color = "green"
        else:
            result = "✗"
            color = "red"
        history_text += f"  第{i}轮: [{color}]{result}[/{color}] vs {opponent}\n"

    content = f"""
[bold cyan]队伍信息[/bold cyan]
━━━━━━━━━━━━━━━━━━━━
队伍名称: {stats['name']}
当前战绩: {stats['record']}
状态: {status}

[bold cyan]比赛历史[/bold cyan]
━━━━━━━━━━━━━━━━━━━━
{history_text if history_text else "  暂无比赛记录"}

[bold cyan]已交手队伍[/bold cyan]
━━━━━━━━━━━━━━━━━━━━
  {', '.join(stats['opponents_played']) if stats['opponents_played'] else "无"}
    """

    panel = Panel(content.strip(), title=f"{team_name} 详细信息", border_style="cyan")
    console.print("\n")
    console.print(panel)


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
        console.print("  4. 📈 计算某队所有对手概率")
        console.print("  5. 🔮 模拟晋级/淘汰概率")
        console.print("  6. 🔍 查看队伍详情")
        console.print("  0. 👋 退出")

        choice = Prompt.ask("\n请选择功能", choices=["0", "1", "2", "3", "4", "5", "6"])

        if choice == "0":
            console.print("[yellow]感谢使用，再见！👋[/yellow]")
            break
        elif choice == "1":
            display_current_standings()
        elif choice == "2":
            display_next_round_groups()
        elif choice == "3":
            calculate_single_matchup()
        elif choice == "4":
            calculate_all_matchups()
        elif choice == "5":
            simulate_advancement()
        elif choice == "6":
            view_team_details()

        if choice != "0":
            if not Confirm.ask("\n继续使用其他功能吗？", default=True):
                console.print("[yellow]感谢使用，再见！👋[/yellow]")
                break


if __name__ == "__main__":
    main()
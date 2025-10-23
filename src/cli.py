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
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from pathlib import Path
from datetime import datetime

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from .worlds_2025_data import (
    load_current_swiss_stage,
    get_next_round_matchups
)
from .swiss_engine import ProbabilityCalculator


console = Console()

# 创建输出目录
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def display_current_standings():
    """显示当前积分榜（生成图片）"""
    stage = load_current_swiss_stage()

    # 按战绩排序
    teams_sorted = sorted(stage.teams, key=lambda t: (t.wins, -t.losses), reverse=True)

    # 创建图表
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')

    # 准备表格数据
    table_data = []
    for team in teams_sorted:
        if team.is_qualified:
            status = "[晋级]"
        elif team.is_eliminated:
            status = "[淘汰]"
        else:
            status = "[比赛中]"

        # 格式化对战历史
        history = []
        for opponent, won in team.match_history:
            if won is None:
                history.append(f"? {opponent}")
            elif won:
                history.append(f"W {opponent}")
            else:
                history.append(f"L {opponent}")

        table_data.append([
            team.name,
            f"{team.wins}-{team.losses}",
            status,
            " | ".join(history)
        ])

    # 创建表格
    table = ax.table(
        cellText=table_data,
        colLabels=["队伍", "战绩", "状态", "对战历史"],
        cellLoc='left',
        loc='center',
        colWidths=[0.08, 0.08, 0.12, 0.72]
    )

    # 设置样式
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # 设置标题行样式
    for i in range(4):
        cell = table[(0, i)]
        cell.set_facecolor('#8B5CF6')
        cell.set_text_props(weight='bold', color='white')

    # 设置数据行样式
    for i in range(1, len(table_data) + 1):
        for j in range(4):
            cell = table[(i, j)]
            if i % 2 == 0:
                cell.set_facecolor('#F3F4F6')
            else:
                cell.set_facecolor('#FFFFFF')

            # 根据状态设置颜色
            if j == 2:  # 状态列
                if "[晋级]" in table_data[i-1][2]:
                    cell.set_text_props(color='green', weight='bold')
                elif "[淘汰]" in table_data[i-1][2]:
                    cell.set_text_props(color='red', weight='bold')
                else:
                    cell.set_text_props(color='orange', weight='bold')

    # 添加标题
    plt.title('2025英雄联盟世界赛瑞士轮积分榜', fontsize=16, fontweight='bold', pad=20)

    # 保存图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"standings_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    console.print(f"[green]✅ 积分榜已保存至: {filename}[/green]")


def display_next_round_groups():
    """显示下一轮分组（生成图片）"""
    matchups = get_next_round_matchups()

    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')

    y_position = 0.95
    box_height = 0.15
    margin = 0.02

    for record, confirmed_teams, pending_matchups in matchups:
        # 构建显示内容
        display_items = []
        display_items.extend(confirmed_teams)

        for team1, team2 in pending_matchups:
            display_items.append(f"({team1} vs {team2}) 胜者")

        content = ", ".join(display_items)

        # 绘制分组框
        ax.add_patch(plt.Rectangle((0.05, y_position - box_height), 0.9, box_height,
                                   facecolor='#E0F2FE', edgecolor='#0EA5E9', linewidth=2))

        # 添加战绩标题
        ax.text(0.08, y_position - 0.03, record, fontsize=14, fontweight='bold',
               verticalalignment='top', color='#0369A1')

        # 添加队伍内容
        ax.text(0.08, y_position - 0.08, content, fontsize=11,
               verticalalignment='top', wrap=True)

        y_position -= (box_height + margin)

    # 添加标题
    ax.text(0.5, 0.98, '下一轮可能的对阵组', fontsize=18, fontweight='bold',
           horizontalalignment='center', verticalalignment='top')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # 保存图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"next_round_groups_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    console.print(f"[green]✅ 下轮分组已保存至: {filename}[/green]")


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


def calculate_2_2_matchup_matrix():
    """计算2-2组所有队伍的配对概率矩阵"""
    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    console.print("\n[bold cyan]╔═══════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║     🎯 2-2 组配对概率矩阵计算器 (生死战预测)     ║[/bold cyan]")
    console.print("[bold cyan]╚═══════════════════════════════════════════════════════════╝[/bold cyan]\n")

    try:
        # 第一步：初步分析
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]分析2-2组构成...", total=None)
            result = calculator.calculate_2_2_matchup_matrix()
            progress.update(task, completed=100)

        # 显示当前2-2组队伍
        if result['current_2_2_teams']:
            console.print(f"[bold green]✅ 当前已在2-2组的队伍:[/bold green] {', '.join(result['current_2_2_teams'])}\n")
        else:
            console.print("[dim]当前没有队伍在2-2组[/dim]\n")

        # 显示所有可能进入2-2的队伍
        console.print(f"[bold yellow]📋 所有可能进入2-2组的队伍:[/bold yellow]")
        console.print(f"   {', '.join(result['all_possible_teams'])}\n")

        # 检查是否需要用户输入
        if result['need_input']:
            console.print(f"[bold magenta]⚠️  发现 {len(result['impact_matches'])} 场待定比赛会影响2-2组的构成[/bold magenta]\n")

            # 显示影响比赛
            console.print("[bold cyan]影响2-2组的待定比赛：[/bold cyan]\n")
            for i, match in enumerate(result['impact_matches'], 1):
                console.print(f"  {i}. [cyan]{match['team1']} vs {match['team2']}[/cyan]")
                console.print(f"     当前战绩: {match['team1_record']} vs {match['team2_record']}")

            console.print("\n" + "━"*60)
            console.print("[bold yellow]请输入各场比赛的胜率估算（用于加权计算）：[/bold yellow]\n")

            # 收集胜率输入
            win_probabilities = {}
            for match in result['impact_matches']:
                t1, t2 = match['team1'], match['team2']
                prompt_text = f"{t1} 战胜 {t2} 的概率 [0-100%，默认50]"
                prob_input = Prompt.ask(prompt_text, default="50")
                try:
                    prob = float(prob_input) / 100.0
                    prob = max(0.0, min(1.0, prob))
                    match_key = tuple(sorted([t1, t2]))
                    win_probabilities[match_key] = prob
                except ValueError:
                    console.print(f"[yellow]输入无效，使用默认值 50%[/yellow]")
                    match_key = tuple(sorted([t1, t2]))
                    win_probabilities[match_key] = 0.5

            console.print("\n" + "━"*60)
            console.print("[cyan]正在计算所有可能情况的配对概率...[/cyan]\n")

            # 重新计算，带上用户输入
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"[cyan]枚举 {2**len(result['impact_matches'])} 种情况...", total=None)
                final_result = calculator.calculate_2_2_matchup_matrix(win_probabilities)
                progress.update(task, completed=100)

            console.print("[bold green]✨ 计算完成！[/bold green]\n")

            # 显示队伍进入2-2组的概率
            console.print("━"*60)
            console.print("[bold cyan]📊 各队伍进入2-2组的概率：[/bold cyan]\n")

            team_prob_table = Table(show_header=True, header_style="bold magenta", box=None)
            team_prob_table.add_column("队伍", style="cyan", width=8)
            team_prob_table.add_column("进入概率", justify="right", style="green", width=12)
            team_prob_table.add_column("状态说明", style="dim", width=30)

            for team in final_result['all_possible_teams']:
                prob = final_result['team_probabilities'].get(team, 0.0)

                # 判断状态
                if team in final_result['current_2_2_teams']:
                    status = "已在2-2组"
                    prob_display = "100.0%"
                else:
                    prob_display = f"{prob:.1%}"
                    team_obj = stage.get_team_by_name(team)
                    if team_obj:
                        if team_obj.wins == 1 and team_obj.losses == 2:
                            status = "需要赢下当前比赛"
                        elif team_obj.wins == 2 and team_obj.losses == 1:
                            status = "需要输掉当前比赛"
                        else:
                            status = ""

                team_prob_table.add_row(team, prob_display, status)

            console.print(team_prob_table)

            # 生成配对概率矩阵热力图
            console.print("\n" + "━"*60)
            console.print("[bold cyan]🔥 2-2组配对概率矩阵（加权平均）[/bold cyan]\n")

            _display_probability_heatmap(final_result['all_possible_teams'], final_result['matrix'], stage)

            # 生成热力图图片
            _generate_heatmap_image(final_result['all_possible_teams'], final_result['matrix'], stage, final_result['team_probabilities'])

            # 询问是否查看详细场景
            console.print("\n" + "━"*60)
            if Confirm.ask("\n[yellow]是否查看各个具体情况的详细配对方案？[/yellow]", default=False):
                console.print("\n[bold cyan]📋 详细情况分析：[/bold cyan]\n")

                for i, scenario in enumerate(final_result['scenarios'], 1):
                    if scenario['probability'] > 0.001:  # 只显示概率>0.1%的情况
                        console.print(f"[bold yellow]═══ 情况 {i} ═══[/bold yellow]")
                        console.print(f"[green]发生概率: {scenario['probability']:.2%}[/green]")
                        console.print(f"[dim]2-2组队伍: {', '.join(scenario['teams_in_2_2'])}[/dim]\n")

                        # 显示该情况的配对矩阵
                        _display_probability_heatmap(scenario['teams_in_2_2'], scenario['matrix'], stage, compact=True)
                        console.print()

        else:
            # 没有待定比赛，直接显示结果
            if result['matrix']:
                console.print("[bold cyan]🔥 2-2组配对概率矩阵[/bold cyan]\n")
                _display_probability_heatmap(result['all_possible_teams'], result['matrix'], stage)
            else:
                console.print("[yellow]当前2-2组没有足够队伍进行配对分析[/yellow]")

    except Exception as e:
        console.print(f"[red]错误: {escape(str(e))}[/red]")
        import traceback
        console.print("[dim]详细错误信息:[/dim]")
        console.print(traceback.format_exc(), style="dim", markup=False)


def _generate_heatmap_image(teams: list, matrix: dict, stage, team_probabilities: dict = None):
    """
    生成配对概率矩阵热力图图片

    Args:
        teams: 队伍列表
        matrix: 概率矩阵字典 {(team1, team2): probability}
        stage: SwissStage 对象
        team_probabilities: 队伍进入2-2组的概率（可选）
    """
    import numpy as np

    if not teams:
        console.print("[yellow]没有队伍数据，无法生成热力图[/yellow]")
        return

    # 过滤掉进入概率为0的队伍（只保留能进入2-2组的队伍）
    if team_probabilities:
        filtered_teams = [t for t in teams if team_probabilities.get(t, 0.0) > 0]
        if not filtered_teams:
            console.print("[yellow]没有队伍能够进入2-2组，无法生成热力图[/yellow]")
            return
        teams = filtered_teams
        console.print(f"[dim]热力图将只显示能够进入2-2组的 {len(teams)} 支队伍[/dim]")

    # 创建矩阵数据
    n = len(teams)
    matrix_data = np.zeros((n, n))
    mask = np.zeros((n, n), dtype=bool)  # 用于标记已交手的格子

    for i, t1 in enumerate(teams):
        for j, t2 in enumerate(teams):
            if i != j:
                prob = matrix.get((t1, t2), 0.0)
                matrix_data[i, j] = prob * 100  # 转换为百分比

                # 检查是否已交手
                team1_obj = stage.get_team_by_name(t1)
                team2_obj = stage.get_team_by_name(t2)
                if team1_obj and team2_obj and t2 in team1_obj.opponents_played:
                    mask[i, j] = True

    # 创建图表（根据队伍数量调整大小）
    base_size = max(12, n * 1.5)  # 更大的基础尺寸
    fig, ax = plt.subplots(figsize=(base_size, base_size * 0.85))

    # 设置背景色
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # 使用更好看的颜色方案
    # 创建自定义颜色映射：白色 -> 浅蓝 -> 蓝色 -> 紫色 -> 红色
    from matplotlib.colors import LinearSegmentedColormap
    colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6',
              '#4292c6', '#2171b5', '#08519c', '#08306b']
    n_bins = 100
    cmap = LinearSegmentedColormap.from_list('custom_blue', colors, N=n_bins)

    # 计算字体大小（根据矩阵大小自适应）
    if n <= 6:
        annot_size = 11
        title_size = 20
        label_size = 14
        tick_size = 12
    elif n <= 8:
        annot_size = 10
        title_size = 18
        label_size = 13
        tick_size = 11
    else:
        annot_size = 9
        title_size = 16
        label_size = 12
        tick_size = 10

    # 使用seaborn绘制热力图（不带注释，后面手动添加以控制颜色）
    sns.heatmap(
        matrix_data,
        annot=False,  # 先不添加注释
        cmap=cmap,
        xticklabels=teams,
        yticklabels=teams,
        cbar_kws={
            'label': '配对概率 (%)',
            'shrink': 0.8,
            'aspect': 20,
            'pad': 0.02
        },
        square=True,
        linewidths=1.5,
        linecolor='#e0e0e0',
        vmin=0,
        vmax=max(40, matrix_data.max()),  # 动态设置上限
        ax=ax
    )

    # 手动添加注释，根据背景色自动选择字体颜色
    threshold = max(40, matrix_data.max()) / 2  # 中间值作为阈值
    for i in range(n):
        for j in range(n):
            if i != j:  # 跳过对角线
                value = matrix_data[i, j]
                # 根据背景色深浅选择字体颜色
                text_color = 'white' if value > threshold else '#2c3e50'
                ax.text(j + 0.5, i + 0.5, f'{value:.1f}',
                       ha='center', va='center',
                       fontsize=annot_size, weight='bold',
                       color=text_color, zorder=5)

    # 标记已交手的格子（用更明显的样式）
    for i in range(n):
        for j in range(n):
            if mask[i, j]:
                # 添加半透明灰色覆盖层
                ax.add_patch(plt.Rectangle((j, i), 1, 1,
                                          fill=True, facecolor='gray',
                                          alpha=0.3, zorder=10))
                # 添加X标记
                ax.text(j + 0.5, i + 0.5, '✕', ha='center', va='center',
                       fontsize=annot_size + 6, color='#7f8c8d',
                       alpha=0.8, weight='bold', zorder=11)
            elif i == j:
                # 对角线用不同颜色标记
                ax.add_patch(plt.Rectangle((j, i), 1, 1,
                                          fill=True, facecolor='#ecf0f1',
                                          alpha=0.5, zorder=10))

    # 美化标题（增加间距避免重叠）
    title_text = '2-2 组配对概率矩阵（加权平均）'
    subtitle_text = '✕ = 已交手无法再次对阵'

    plt.title(title_text, fontsize=title_size, fontweight='bold',
             pad=25, color='#2c3e50', loc='center')  # 增加 pad 避免重叠
    plt.text(0.5, 1.04, subtitle_text, transform=ax.transAxes,  # 调整位置
            fontsize=title_size - 6, ha='center', va='bottom',
            color='#7f8c8d', style='italic')

    # 美化轴标签
    plt.xlabel('对手队伍', fontsize=label_size, fontweight='bold',
              color='#34495e', labelpad=10)
    plt.ylabel('队伍', fontsize=label_size, fontweight='bold',
              color='#34495e', labelpad=10)

    # 旋转和美化刻度标签
    ax.set_xticklabels(teams, rotation=45, ha='right', fontsize=tick_size,
                       fontweight='600', color='#2c3e50')
    ax.set_yticklabels(teams, rotation=0, fontsize=tick_size,
                       fontweight='600', color='#2c3e50')

    # 美化colorbar
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=tick_size - 1, colors='#2c3e50')
    cbar.set_label('配对概率 (%)', fontsize=label_size - 1,
                  color='#2c3e50', fontweight='bold')

    # 添加队伍进入概率的美化注释框
    if team_probabilities:
        prob_lines = []
        current_line = []
        count = 0

        # 按概率排序
        sorted_teams = sorted([(t, team_probabilities.get(t, 0.0)) for t in teams],
                            key=lambda x: x[1], reverse=True)

        for team, prob in sorted_teams:
            if prob > 0:
                # 根据概率添加颜色标记
                if prob == 1.0:
                    marker = '●'  # 已在2-2组
                elif prob >= 0.5:
                    marker = '◆'  # 高概率
                else:
                    marker = '◇'  # 低概率

                current_line.append(f"{marker} {team}: {prob:.1%}")
                count += 1
                if count % 4 == 0:  # 每行4个队伍
                    prob_lines.append("    ".join(current_line))
                    current_line = []

        if current_line:  # 添加剩余的队伍
            prob_lines.append("    ".join(current_line))

        # 构建注释文本（使用更清晰的格式）
        prob_header = "各队进入2-2组概率"
        prob_body = "\n".join(prob_lines)
        prob_legend = "● 已在2-2组 (100%)    ◆ 高概率 (≥50%)    ◇ 低概率 (<50%)"

        prob_text = f"{prob_header}\n{prob_body}\n\n{prob_legend}"

        # 美化的注释框（浅色背景，深色字体）
        plt.figtext(0.5, 0.01, prob_text, ha='center', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa',
                            edgecolor='#6c757d', linewidth=2, alpha=0.95),
                   color='#212529', weight='500')

    # 调整布局，为底部注释框留出空间
    if team_probabilities:
        plt.subplots_adjust(bottom=0.20)  # 为底部注释框留出空间
    else:
        plt.subplots_adjust(bottom=0.10)

    # 保存图片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = OUTPUT_DIR / f"matchup_matrix_2_2_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.5)
    plt.close()

    console.print(f"\n[green]✅ 2-2组配对概率矩阵热力图已保存至: {filename}[/green]")


def _display_probability_heatmap(teams: list, matrix: dict, stage, compact: bool = False):
    """
    显示概率热力图矩阵

    Args:
        teams: 队伍列表
        matrix: 概率矩阵字典 {(team1, team2): probability}
        stage: SwissStage 对象
        compact: 是否紧凑显示
    """
    if not teams:
        console.print("[dim]没有队伍数据[/dim]")
        return

    # 创建矩阵表格
    table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 1))

    # 添加表头
    table.add_column("", style="cyan bold", width=6, justify="right")
    for team in teams:
        table.add_column(team, justify="center", width=7)

    # 添加数据行
    for t1 in teams:
        row_data = [t1]

        for t2 in teams:
            if t1 == t2:
                # 对角线
                row_data.append("[dim]-[/dim]")
            else:
                prob = matrix.get((t1, t2), 0.0)

                # 检查是否已交手
                team1_obj = stage.get_team_by_name(t1)
                team2_obj = stage.get_team_by_name(t2)
                already_played = False
                if team1_obj and team2_obj and t2 in team1_obj.opponents_played:
                    already_played = True

                # 根据概率选择颜色和样式
                if already_played:
                    # 已交手，显示为深灰色
                    cell = f"[dim black]0.0%[/dim black]"
                elif prob == 0.0:
                    cell = "[dim]0.0%[/dim]"
                elif prob >= 0.30:
                    # 高概率：红色/品红色
                    cell = f"[bold red]{prob:.1%}[/bold red]"
                elif prob >= 0.20:
                    # 中高概率：黄色
                    cell = f"[bold yellow]{prob:.1%}[/bold yellow]"
                elif prob >= 0.10:
                    # 中等概率：绿色
                    cell = f"[green]{prob:.1%}[/green]"
                elif prob >= 0.05:
                    # 低概率：青色
                    cell = f"[cyan]{prob:.1%}[/cyan]"
                else:
                    # 极低概率：灰色
                    cell = f"[dim]{prob:.1%}[/dim]"

                row_data.append(cell)

        table.add_row(*row_data)

    console.print(table)

    if not compact:
        # 显示图例
        console.print("\n[bold]概率等级图例：[/bold]")
        console.print("  [bold red]≥30%[/bold red]  [bold yellow]20-30%[/bold yellow]  [green]10-20%[/green]  [cyan]5-10%[/cyan]  [dim]<5%[/dim]  [dim black]已交手(0%)[/dim black]")


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
        console.print("  4. 🔥 2-2组配对概率矩阵（生死战预测）")
        console.print("  0. 👋 退出")

        choice = Prompt.ask("\n请选择功能", choices=["0", "1", "2", "3", "4"])

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
            calculate_2_2_matchup_matrix()

        if choice != "0":
            if not Confirm.ask("\n继续使用其他功能吗？", default=True):
                console.print("[yellow]感谢使用，再见！👋[/yellow]")
                break


if __name__ == "__main__":
    main()
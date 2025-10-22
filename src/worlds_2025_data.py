"""
2025英雄联盟世界赛瑞士轮数据
"""
from typing import List, Dict, Tuple
from .models import Team, SwissStage


def create_worlds_2025_teams() -> List[Team]:
    """创建2025世界赛所有队伍"""
    teams = [
        Team("BLG"),
        Team("TES"),
        Team("AL"),
        Team("HLE"),
        Team("GEN"),
        Team("T1"),
        Team("KT"),
        Team("G2"),
        Team("FNC"),
        Team("MKOI"),
        Team("FLY"),
        Team("100T"),
        Team("TSW"),
        Team("PSG"),
        Team("VKS"),
        Team("CFO"),
    ]
    return teams


def get_current_results() -> Dict[str, Tuple[int, int, List[Tuple[str, bool | None]]]]:
    """
    获取当前的比赛结果
    返回格式: {队伍名: (胜场, 负场, [(对手, 是否获胜)])}

    是否获胜可以是：
    - True: 获胜
    - False: 失败
    - None: 待定比赛
    """
    
    results = {
        # ===== 已晋级队伍（3胜）=====
        "KT": (3, 0, [
            ("MKOI", True),  # R1: Win
            ("TSW", True),   # R2: Win (Match 11)
            ("TES", True)    # R3: Win (Match 18, BO3 2-0, 晋级)
        ]),

        "AL": (3, 0, [
            ("HLE", True),   # R1: Win (Match 7)
            ("GEN", True),   # R2: Win (Match 15)
            ("CFO", True)    # R3: Win (Match 19, BO3 2-1, 晋级)
        ]),

        "G2": (3, 1, [
            ("TES", False),  # R1: Loss (Match 8)
            ("MKOI", True),  # R2: Win (Match 12)
            ("BLG", True),   # R3: Win (Match 22, BO1)
            ("FLY", True)    # R4: Win (Match 27, BO3 2-1, 晋级)
        ]),

        "HLE": (3, 1, [
            ("AL", False),   # R1: Loss (Match 7)
            ("PSG", True),   # R2: Win (Match 17)
            ("100T", True),  # R3: Win (Match 23, BO1)
            ("CFO", True)    # R4: Win (Match 26, BO3 2-0, 晋级)
        ]),

        # ===== 2胜1负（等待第4轮晋级赛）=====
        "GEN": (2, 1, [
            ("PSG", True),   # R1: Win (Match 9)
            ("AL", False),   # R2: Loss (Match 15)
            ("T1", True),    # R3: Win (Match 21, BO1)
            ("TES", None)    # R4: vs TES (Match 29) - 待定
        ]),

        "TES": (2, 1, [
            ("G2", True),    # R1: Win (Match 8)
            ("100T", True),  # R2: Win (Match 13)
            ("KT", False),   # R3: Loss (Match 18, BO3 0-2)
            ("GEN", None)    # R4: vs GEN (Match 29) - 待定
        ]),

        # ===== 2胜2负（等待第5轮生死战）=====
        "FLY": (2, 2, [
            ("T1", False),   # R1: Loss (Match 6)
            ("VKS", True),   # R2: Win (Match 10)
            ("TSW", True),   # R3: Win (Match 20, BO1)
            ("G2", False)    # R4: Loss (Match 27, BO3 1-2)
        ]),

        "CFO": (2, 2, [
            ("FNC", True),   # R1: Win (Match 3)
            ("T1", True),    # R2: Win (Match 14)
            ("AL", False),   # R3: Loss (Match 19, BO3 1-2)
            ("HLE", False)   # R4: Loss (Match 26, BO3 0-2)
        ]),

        # ===== 1胜2负（等待第4轮淘汰赛）=====
        "MKOI": (1, 2, [
            ("KT", False),   # R1: Loss (Match 4)
            ("G2", False),   # R2: Loss (Match 12)
            ("FNC", True),   # R3: Win (Match 24, BO3 2-1)
            ("TSW", None)    # R4: vs TSW (Match 28) - 待定
        ]),

        "TSW": (1, 2, [
            ("VKS", True),   # R1: Win (Match 2: TSW 1-0 VKS)
            ("KT", False),   # R2: Loss (Match 11)
            ("FLY", False),  # R3: Loss (Match 20, BO1)
            ("MKOI", None)   # R4: vs MKOI (Match 28) - 待定
        ]),

        "BLG": (1, 2, [
            ("100T", False), # R1: Loss (Match 5)
            ("FNC", True),   # R2: Win (Match 16)
            ("G2", False),   # R3: Loss (Match 22, BO1)
            ("VKS", None)    # R4: vs VKS (Match 30) - 待定
        ]),

        "VKS": (1, 2, [
            ("TSW", False),  # R1: Loss (Match 2: VKS 0-1 TSW)
            ("FLY", False),  # R2: Loss (Match 10)
            ("PSG", True),   # R3: Win (Match 25, BO3 2-1)
            ("BLG", None)    # R4: vs BLG (Match 30) - 待定
        ]),

        "100T": (1, 2, [
            ("BLG", True),   # R1: Win (Match 5)
            ("TES", False),  # R2: Loss (Match 13)
            ("HLE", False),  # R3: Loss (Match 23, BO1)
            ("T1", None)     # R4: vs T1 (Match 31) - 待定
        ]),

        "T1": (1, 2, [
            ("FLY", True),   # R1: Win (Match 6)
            ("CFO", False),  # R2: Loss (Match 14)
            ("GEN", False),  # R3: Loss (Match 21, BO1)
            ("100T", None)   # R4: vs 100T (Match 31) - 待定
        ]),

        # ===== 已淘汰队伍（0-3）=====
        "FNC": (0, 3, [
            ("CFO", False),  # R1: Loss (Match 3)
            ("BLG", False),  # R2: Loss (Match 16)
            ("MKOI", False)  # R3: Loss (Match 24, BO3 1-2, 淘汰)
        ]),

        "PSG": (0, 3, [
            ("GEN", False),  # R1: Loss (Match 9)
            ("HLE", False),  # R2: Loss (Match 17)
            ("VKS", False)   # R3: Loss (Match 25, BO3 1-2, 淘汰)
        ]),
    }
    return results


def load_current_swiss_stage() -> SwissStage:
    """加载当前瑞士轮状态"""
    teams = create_worlds_2025_teams()
    stage = SwissStage(teams=teams)

    # 应用当前结果
    results = get_current_results()

    for team in stage.teams:
        if team.name in results:
            wins, losses, match_history = results[team.name]
            team.wins = wins
            team.losses = losses

            for opponent, won in match_history:
                # 只有已经完成的比赛才加入已交手队伍
                if won is not None:
                    team.opponents_played.add(opponent)
                team.match_history.append((opponent, won))

    # 设置当前轮次（基于已完成的比赛推断）
    max_games = max(team.wins + team.losses for team in stage.teams)
    stage.current_round = max_games + 1

    return stage


def get_next_round_matchups() -> List[Tuple[str, List[str], List[Tuple[str, str]]]]:
    """
    获取下一轮可能的对阵
    返回格式: [(战绩, [已确定的队伍列表], [(队伍A, 队伍B) 待定对阵列表])]
    """
    stage = load_current_swiss_stage()
    matchups = []

    # 2-2 组（生死战，BO3）
    teams_2_2 = [t.name for t in stage.get_teams_by_record(2, 2)]
    # 找出所有 1-2 的待定对阵（这些对阵的胜者将进入 2-2）
    teams_1_2 = stage.get_teams_by_record(1, 2)
    pending_1_2_matchups = []

    # 从 match_history 中提取待定对阵
    for team in teams_1_2:
        # 找到最后一场比赛（待定的比赛）
        if team.match_history and team.match_history[-1][1] is None:
            opponent_name = team.match_history[-1][0]
            # 确保每个对阵只添加一次
            matchup = tuple(sorted([team.name, opponent_name]))
            if matchup not in [tuple(sorted(m)) for m in pending_1_2_matchups]:
                pending_1_2_matchups.append((team.name, opponent_name))

    if teams_2_2 or pending_1_2_matchups:
        matchups.append(("2-2 (生死战 BO3)", teams_2_2, pending_1_2_matchups))

    # 1-2 组（淘汰边缘，BO3）
    teams_1_2_names = [t.name for t in teams_1_2]
    if teams_1_2_names:
        matchups.append(("1-2 (淘汰边缘 BO3)", teams_1_2_names, []))

    # 2-1 组（晋级边缘，BO3）
    teams_2_1 = [t.name for t in stage.get_teams_by_record(2, 1)]
    # 找出所有 1-2 的待定对阵（这些对阵的败者将留在 1-2）
    pending_2_1_to_1_2_matchups = []

    if teams_2_1:
        matchups.append(("2-1 (晋级边缘 BO3)", teams_2_1, pending_2_1_to_1_2_matchups))

    return matchups


def get_team_stats(team_name: str) -> Dict:
    """获取队伍详细信息"""
    stage = load_current_swiss_stage()
    team = stage.get_team_by_name(team_name)

    if not team:
        return None

    return {
        "name": team.name,
        "record": team.record,
        "wins": team.wins,
        "losses": team.losses,
        "is_qualified": team.is_qualified,
        "is_eliminated": team.is_eliminated,
        "is_active": team.is_active,
        "opponents_played": list(team.opponents_played),
        "match_history": team.match_history
    }
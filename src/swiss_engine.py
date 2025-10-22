"""
瑞士轮抽签引擎和概率计算
"""
import random
from typing import List, Dict, Tuple, Set, Optional
from itertools import combinations
from collections import defaultdict
import copy

from .models import Team, Match, SwissStage


class SwissDrawEngine:
    """瑞士轮抽签引擎"""

    def __init__(self, stage: SwissStage):
        self.stage = stage

    def get_possible_matchups(self, teams: List[Team]) -> List[Tuple[Team, Team]]:
        """
        获取所有可能的对阵组合
        考虑规则：不能和已经打过的队伍再打
        """
        possible_matchups = []

        for i, team1 in enumerate(teams):
            for team2 in teams[i + 1:]:
                if team1.can_play_against(team2):
                    possible_matchups.append((team1, team2))

        return possible_matchups

    def is_valid_pairing(self, pairs: List[Tuple[Team, Team]], remaining_teams: Set[Team]) -> bool:
        """检查是否是有效的配对（所有队伍都能找到对手）"""
        if not remaining_teams:
            return True

        # 使用图匹配算法检查是否存在完美匹配
        graph = defaultdict(set)
        for team in remaining_teams:
            for other in remaining_teams:
                if team != other and team.can_play_against(other):
                    graph[team.name].add(other.name)

        # 简单的贪心检查：如果有队伍没有可能的对手，返回False
        for team in remaining_teams:
            if team.name not in graph or len(graph[team.name]) == 0:
                return False

        return True

    def generate_valid_pairings(self, teams: List[Team]) -> List[List[Tuple[Team, Team]]]:
        """生成所有有效的配对方案"""
        # 处理奇数队伍的情况（瑞士轮可能出现奇数队伍）
        if len(teams) % 2 != 0:
            # 对于奇数队伍，返回空列表（需要跨组配对）
            return []

        if len(teams) == 0:
            return [[]]

        all_pairings = []
        possible_matchups = self.get_possible_matchups(teams)

        def backtrack(current_pairs: List[Tuple[Team, Team]], remaining: Set[Team]):
            if not remaining:
                all_pairings.append(current_pairs[:])
                return

            # 选择剩余队伍中的第一个
            team = next(iter(remaining))

            # 尝试为这个队伍找到所有可能的对手
            for other in remaining:
                if other != team and team.can_play_against(other):
                    new_remaining = remaining - {team, other}
                    current_pairs.append((team, other))

                    # 检查剩余队伍是否能完成配对
                    if self.is_valid_pairing(current_pairs, new_remaining):
                        backtrack(current_pairs, new_remaining)

                    current_pairs.pop()

        remaining_set = set(teams)
        backtrack([], remaining_set)

        return all_pairings

    def draw_round(self) -> List[Match]:
        """执行一轮抽签"""
        matches = []

        # 获取所有战绩组合
        record_groups = defaultdict(list)
        for team in self.stage.get_active_teams():
            record_groups[team.record].append(team)

        # 按战绩分组进行抽签
        for record, teams in record_groups.items():
            if len(teams) % 2 != 0:
                # 如果某个战绩的队伍是奇数，需要和相邻战绩的队伍配对
                # 这里简化处理
                continue

            # 随机抽签
            shuffled = teams[:]
            random.shuffle(shuffled)

            # 尝试配对
            valid_pairings = self.generate_valid_pairings(shuffled)
            if valid_pairings:
                # 随机选择一种配对方案
                pairing = random.choice(valid_pairings)
                for team1, team2 in pairing:
                    match = Match(
                        team1=team1.name,
                        team2=team2.name,
                        round_number=self.stage.current_round
                    )
                    matches.append(match)

        return matches


class ProbabilityCalculator:
    """概率计算器"""

    def __init__(self, stage: SwissStage):
        self.stage = stage
        self.engine = SwissDrawEngine(stage)

    def _calculate_cross_group_paths(self, team1: Team, team2: Team) -> List[Dict]:
        """
        计算两支不同战绩队伍可能相遇的路径（条件概率）

        Args:
            team1: 队伍1
            team2: 队伍2

        Returns:
            可能的相遇路径列表，每个路径包含：
            {
                'target_record': str,  # 目标战绩
                'team1_needs': str,  # 队伍1需要做什么
                'team2_needs': str,  # 队伍2需要做什么
                'meetup_probability': float,  # 在该组相遇的概率（假设都到达该组）
                'description': str  # 路径描述
            }
        """
        paths = []

        # 分析两队的战绩
        w1, l1 = team1.wins, team1.losses
        w2, l2 = team2.wins, team2.losses

        def can_reach_record(current_w, current_l, target_w, target_l):
            """检查是否能从当前战绩达到目标战绩"""
            if current_w > target_w or current_l > target_l:
                return False
            if current_w == target_w and current_l == target_l:
                return True
            # 检查是否会提前晋级或淘汰
            if current_w >= 3 or current_l >= 3:
                return False
            if target_w >= 3 or target_l >= 3:
                return False
            return True

        # 遍历所有可能的目标战绩（排除晋级和淘汰）
        possible_records = [
            (1, 1), (2, 1), (1, 2), (2, 2)
        ]

        for target_w, target_l in possible_records:
            # 检查两队是否都能到达这个战绩
            can_t1_reach = can_reach_record(w1, l1, target_w, target_l)
            can_t2_reach = can_reach_record(w2, l2, target_w, target_l)

            if can_t1_reach and can_t2_reach:
                # 计算需要的步骤
                wins_needed_t1 = target_w - w1
                losses_needed_t1 = target_l - l1
                wins_needed_t2 = target_w - w2
                losses_needed_t2 = target_l - l2

                # 检查是否有意义（至少有一队需要移动）
                if wins_needed_t1 == 0 and losses_needed_t1 == 0 and \
                   wins_needed_t2 == 0 and losses_needed_t2 == 0:
                    continue  # 两队已经在同一组，这种情况在上层已经处理

                # 构建路径描述
                t1_needs = self._describe_path(w1, l1, target_w, target_l, team1.name)
                t2_needs = self._describe_path(w2, l2, target_w, target_l, team2.name)

                # 计算在目标组相遇的概率
                # 这里需要考虑该组可能有多少队伍
                # 简化计算：假设该组会有其他队伍，用实际配对计算
                meetup_prob = self._estimate_meetup_probability_in_group(
                    team1, team2, target_w, target_l
                )

                if meetup_prob > 0:
                    description = (
                        f"目标分组：{target_w}-{target_l}\n"
                        f"  • {team1.name} ({w1}-{l1}): {t1_needs}\n"
                        f"  • {team2.name} ({w2}-{l2}): {t2_needs}\n"
                        f"  • 假设两队都到达 {target_w}-{target_l} 组后，在该组相遇的概率: {meetup_prob:.1%}\n"
                        f"\n说明：这是条件概率 - 假设两队都成功到达该分组的前提下相遇的概率。"
                    )

                    paths.append({
                        'target_record': f"{target_w}-{target_l}",
                        'team1_needs': t1_needs,
                        'team2_needs': t2_needs,
                        'probability': meetup_prob,  # 现在是条件概率
                        'description': description,
                        'is_conditional': True  # 标记这是条件概率
                    })

        # 按概率排序
        paths.sort(key=lambda x: x['probability'], reverse=True)

        return paths

    def _estimate_meetup_probability_in_group(self, team1: Team, team2: Team, target_w: int, target_l: int) -> float:
        """
        估算两队在指定战绩组相遇的概率

        这里简化处理：假设该组会有一定数量的队伍
        """
        # 简化估算：
        # - 如果是 2-2 或 1-2 这种关键分组，假设会有 4-6 支队伍
        # - 如果是 2-1 或 1-1，假设会有 2-4 支队伍

        if target_w == 2 and target_l == 2:
            # 生死战，通常队伍较少
            estimated_teams = 4
        elif target_w == 1 and target_l == 2:
            # 淘汰边缘
            estimated_teams = 4
        elif target_w == 2 and target_l == 1:
            # 晋级边缘
            estimated_teams = 4
        else:
            estimated_teams = 4

        # 检查两队是否已经交手过
        if team2.name in team1.opponents_played:
            return 0.0

        # 简化计算：n支队伍配对，两支特定队伍相遇的概率约为 1/(n-1)
        if estimated_teams <= 2:
            return 1.0

        return 1.0 / (estimated_teams - 1)

    def _describe_path(self, current_w: int, current_l: int, target_w: int, target_l: int, team_name: str) -> str:
        """描述从当前战绩到目标战绩需要的步骤"""
        wins_needed = target_w - current_w
        losses_needed = target_l - current_l

        if wins_needed == 0 and losses_needed == 0:
            return f"已在 {target_w}-{target_l} 组"

        parts = []
        if wins_needed > 0:
            parts.append(f"赢 {wins_needed} 场")
        if losses_needed > 0:
            parts.append(f"输 {losses_needed} 场")

        return " 且 ".join(parts) + f" 到达 {target_w}-{target_l} 组"

    def calculate_matchup_probability(
        self, team1_name: str, team2_name: str, num_simulations: int = 10000
    ) -> Dict:
        """
        计算两支队伍相遇的概率（包含详细解释）

        Args:
            team1_name: 队伍1名称
            team2_name: 队伍2名称
            num_simulations: 模拟次数（用于跨分组概率计算）

        Returns:
            包含概率和详细解释的字典:
            {
                'probability': float,  # 相遇概率
                'can_meet_directly': bool,  # 是否能在下一轮直接相遇
                'reason': str,  # 不能直接相遇的原因
                'explanation': str,  # 概率计算的详细解释
                'paths': List[Dict],  # 可能的相遇路径（跨分组时）
                'same_group': bool,  # 是否在同一分组
                'pairing_stats': Dict  # 配对统计信息
            }
        """
        team1 = self.stage.get_team_by_name(team1_name)
        team2 = self.stage.get_team_by_name(team2_name)

        result = {
            'probability': 0.0,
            'can_meet_directly': False,
            'reason': '',
            'explanation': '',
            'paths': [],
            'same_group': False,
            'pairing_stats': {}
        }

        if not team1 or not team2:
            raise ValueError("队伍不存在")

        # 检查是否都在比赛中
        if not team1.is_active or not team2.is_active:
            result['reason'] = f"{team1_name if not team1.is_active else team2_name} 已经不在比赛中（已晋级或已淘汰）"
            result['explanation'] = "只有仍在比赛中的队伍才可能相遇。"
            return result

        # 检查是否已经打过
        if team2_name in team1.opponents_played:
            result['reason'] = "两队已经交手过"
            result['explanation'] = "根据瑞士轮规则，已经交手过的队伍不会再次相遇。"
            return result

        # 检查是否在同一战绩组
        if team1.record == team2.record:
            result['same_group'] = True
            result['can_meet_directly'] = True

            # 计算同组相遇概率
            teams_in_group = self.stage.get_teams_by_record(team1.wins, team1.losses)

            if len(teams_in_group) < 2:
                result['probability'] = 0.0
                result['reason'] = "分组中队伍不足"
                return result

            # 生成所有可能的配对
            all_pairings = self.engine.generate_valid_pairings(teams_in_group)

            if not all_pairings:
                result['probability'] = 0.0
                result['reason'] = "无法生成有效配对"
                result['explanation'] = "由于已交手限制，无法为该组生成有效的配对方案。"
                return result

            # 计算包含目标配对的方案数
            target_pairing_count = 0
            for pairing in all_pairings:
                for pair in pairing:
                    if (pair[0].name == team1_name and pair[1].name == team2_name) or \
                       (pair[0].name == team2_name and pair[1].name == team1_name):
                        target_pairing_count += 1
                        break

            result['probability'] = target_pairing_count / len(all_pairings)

            # 统计信息
            result['pairing_stats'] = {
                'total_pairings': len(all_pairings),
                'favorable_pairings': target_pairing_count,
                'teams_in_group': len(teams_in_group),
                'team_names': [t.name for t in teams_in_group]
            }

            # 详细解释
            result['explanation'] = (
                f"两队都在 {team1.record} 组。\n"
                f"该组共有 {len(teams_in_group)} 支队伍：{', '.join([t.name for t in teams_in_group])}\n"
                f"考虑已交手限制后，共有 {len(all_pairings)} 种有效配对方案。\n"
                f"其中 {target_pairing_count} 种方案包含 {team1_name} vs {team2_name} 这场对阵。\n"
                f"因此相遇概率 = {target_pairing_count}/{len(all_pairings)} = {result['probability']:.1%}"
            )

            return result
        else:
            # 不在同一组，计算跨分组相遇路径
            result['same_group'] = False
            result['can_meet_directly'] = False
            result['reason'] = f"战绩不同（{team1_name}: {team1.record}, {team2_name}: {team2.record}）"

            # 计算可能的相遇路径
            paths = self._calculate_cross_group_paths(team1, team2)
            result['paths'] = paths

            if paths:
                result['explanation'] = (
                    f"{team1_name} 当前战绩 {team1.record}，{team2_name} 当前战绩 {team2.record}。\n\n"
                    f"两队不在同一分组，需要通过比赛结果移动到相同分组才能相遇。\n"
                    f"以下是可能的相遇路径及其条件概率：\n"
                )

                # 不计算总概率，因为现在是条件概率
                result['probability'] = 0.0  # 标记为0，表示这是条件概率情况
            else:
                result['explanation'] = (
                    f"{team1_name} ({team1.record}) 和 {team2_name} ({team2.record}) "
                    f"在当前状态下无法在后续轮次相遇。"
                )

            return result

    def calculate_all_matchup_probabilities(
        self, team_name: str
    ) -> Dict[str, float]:
        """
        计算一支队伍与所有可能对手的匹配概率

        Args:
            team_name: 队伍名称

        Returns:
            对手名称到概率的映射
        """
        team = self.stage.get_team_by_name(team_name)
        if not team or not team.is_active:
            return {}

        probabilities = {}
        teams_in_group = self.stage.get_teams_by_record(team.wins, team.losses)

        for other_team in teams_in_group:
            if other_team.name != team_name and team.can_play_against(other_team):
                result = self.calculate_matchup_probability(team_name, other_team.name)
                # 现在返回的是字典，需要提取probability字段
                prob = result['probability']
                if prob > 0:
                    probabilities[other_team.name] = prob

        return probabilities

    def simulate_advancement_probability(
        self, team_name: str, num_simulations: int = 1000
    ) -> Dict[str, float]:
        """
        模拟队伍晋级/淘汰的概率

        Args:
            team_name: 队伍名称
            num_simulations: 模拟次数

        Returns:
            包含晋级概率和淘汰概率的字典
        """
        team = self.stage.get_team_by_name(team_name)
        if not team:
            raise ValueError(f"队伍 {team_name} 不存在")

        if team.is_qualified:
            return {"qualify": 1.0, "eliminate": 0.0}
        if team.is_eliminated:
            return {"qualify": 0.0, "eliminate": 1.0}

        qualify_count = 0
        eliminate_count = 0

        for _ in range(num_simulations):
            # 创建副本进行模拟
            sim_stage = copy.deepcopy(self.stage)
            sim_team = sim_stage.get_team_by_name(team_name)

            # 模拟直到该队伍晋级或淘汰
            while sim_team.is_active:
                # 简化模拟：50%胜率
                if random.random() < 0.5:
                    sim_team.wins += 1
                else:
                    sim_team.losses += 1

            if sim_team.is_qualified:
                qualify_count += 1
            else:
                eliminate_count += 1

        return {
            "qualify": qualify_count / num_simulations,
            "eliminate": eliminate_count / num_simulations
        }
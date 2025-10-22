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

    def _identify_pending_matches(self) -> List[Dict]:
        """
        识别所有待定比赛（won = None 的比赛）

        Returns:
            待定比赛列表，每个包含：
            {
                'team1': str,  # 队伍1名称
                'team2': str,  # 队伍2名称
                'team1_record': str,  # 队伍1当前战绩
                'team2_record': str,  # 队伍2当前战绩
            }
        """
        pending_matches = []
        processed_pairs = set()

        for team in self.stage.teams:
            if team.match_history:
                # 找到最后一场比赛，检查是否待定
                for opponent_name, result in team.match_history:
                    if result is None:  # 待定比赛
                        # 避免重复添加同一场比赛
                        pair = tuple(sorted([team.name, opponent_name]))
                        if pair not in processed_pairs:
                            opponent = self.stage.get_team_by_name(opponent_name)
                            if opponent:
                                pending_matches.append({
                                    'team1': team.name,
                                    'team2': opponent_name,
                                    'team1_record': team.record,
                                    'team2_record': opponent.record,
                                })
                                processed_pairs.add(pair)

        return pending_matches

    def _find_path_to_target_group(self, team: Team, target_w: int, target_l: int) -> Optional[Dict]:
        """
        判断队伍能否到达目标分组及需要什么结果

        Returns:
            如果能到达，返回：
            {
                'possible': True,
                'wins_needed': int,  # 需要赢几场
                'losses_needed': int,  # 需要输几场
                'pending_match': Dict or None,  # 待定比赛信息
            }
            如果不能到达，返回 None
        """
        current_w, current_l = team.wins, team.losses

        # 检查是否已经在目标分组
        if current_w == target_w and current_l == target_l:
            return {
                'possible': True,
                'wins_needed': 0,
                'losses_needed': 0,
                'pending_match': None,
            }

        # 检查是否已经晋级或淘汰
        if current_w >= 3 or current_l >= 3:
            return None

        # 检查目标分组是否有效
        if target_w >= 3 or target_l >= 3:
            return None

        # 计算需要的胜负场数
        wins_needed = target_w - current_w
        losses_needed = target_l - current_l

        # 检查是否可达
        if wins_needed < 0 or losses_needed < 0:
            return None

        # 检查路径上是否会提前晋级/淘汰
        # 简化处理：只考虑一步到达的情况
        if wins_needed + losses_needed > 1:
            # 需要多场比赛，暂时返回不可达（简化处理）
            return None

        # 找到待定比赛
        pending_match = None
        for opponent_name, result in team.match_history:
            if result is None:
                opponent = self.stage.get_team_by_name(opponent_name)
                if opponent:
                    pending_match = {
                        'opponent': opponent_name,
                        'opponent_record': opponent.record,
                    }
                break

        return {
            'possible': True,
            'wins_needed': wins_needed,
            'losses_needed': losses_needed,
            'pending_match': pending_match,
        }

    def _identify_impact_matches(self, target_w: int, target_l: int, exclude_matches: List[tuple]) -> List[Dict]:
        """
        识别哪些待定比赛会影响目标分组的构成

        Args:
            target_w: 目标分组的胜场数
            target_l: 目标分组的负场数
            exclude_matches: 要排除的比赛（通常是必要条件的比赛）

        Returns:
            影响分组的待定比赛列表
        """
        impact_matches = []
        all_pending = self._identify_pending_matches()

        for match in all_pending:
            # 检查是否在排除列表中
            match_pair = tuple(sorted([match['team1'], match['team2']]))
            if match_pair in exclude_matches:
                continue

            team1 = self.stage.get_team_by_name(match['team1'])
            team2 = self.stage.get_team_by_name(match['team2'])

            if not team1 or not team2:
                continue

            # 检查比赛结果是否会让某队进入目标分组
            # 如果 team1 赢
            if team1.wins + 1 == target_w and team1.losses == target_l:
                impact_matches.append({
                    'match': match,
                    'impact_type': f'{team1.name} 赢则进入 {target_w}-{target_l}',
                    'team_affected': team1.name,
                    'result_needed': 'team1_win',
                })

            # 如果 team1 输
            if team1.wins == target_w and team1.losses + 1 == target_l:
                impact_matches.append({
                    'match': match,
                    'impact_type': f'{team1.name} 输则进入 {target_w}-{target_l}',
                    'team_affected': team1.name,
                    'result_needed': 'team1_lose',
                })

            # 如果 team2 赢
            if team2.wins + 1 == target_w and team2.losses == target_l:
                if not any(im['match'] == match and im['team_affected'] == team2.name
                          for im in impact_matches):
                    impact_matches.append({
                        'match': match,
                        'impact_type': f'{team2.name} 赢则进入 {target_w}-{target_l}',
                        'team_affected': team2.name,
                        'result_needed': 'team2_win',
                    })

            # 如果 team2 输
            if team2.wins == target_w and team2.losses + 1 == target_l:
                if not any(im['match'] == match and im['team_affected'] == team2.name
                          for im in impact_matches):
                    impact_matches.append({
                        'match': match,
                        'impact_type': f'{team2.name} 输则进入 {target_w}-{target_l}',
                        'team_affected': team2.name,
                        'result_needed': 'team2_lose',
                    })

        # 去重：同一场比赛可能因为两个队伍都会影响而重复
        unique_matches = {}
        for im in impact_matches:
            match_key = (im['match']['team1'], im['match']['team2'])
            if match_key not in unique_matches:
                unique_matches[match_key] = im['match']

        return list(unique_matches.values())

    def _simulate_group_with_results(self, target_w: int, target_l: int, match_results: Dict[tuple, str]) -> List[Team]:
        """
        根据指定的比赛结果模拟目标分组的构成

        Args:
            target_w: 目标分组的胜场数
            target_l: 目标分组的负场数
            match_results: 比赛结果字典 {(team1, team2): 'team1_win' or 'team2_win'}

        Returns:
            目标分组中的队伍列表
        """
        # 创建深拷贝以模拟比赛结果
        simulated_stage = copy.deepcopy(self.stage)

        # 应用比赛结果
        for (t1_name, t2_name), result in match_results.items():
            t1 = simulated_stage.get_team_by_name(t1_name)
            t2 = simulated_stage.get_team_by_name(t2_name)

            if t1 and t2:
                if result == 'team1_win':
                    t1.wins += 1
                    t2.losses += 1
                elif result == 'team2_win':
                    t1.losses += 1
                    t2.wins += 1

        # 获取目标分组的队伍
        return simulated_stage.get_teams_by_record(target_w, target_l)

    def _calculate_pairing_probability(self, team1_name: str, team2_name: str, teams_in_group: List[Team]) -> Dict:
        """
        计算两队在指定分组中相遇的概率（考虑已交手限制）

        Args:
            team1_name: 队伍1名称
            team2_name: 队伍2名称
            teams_in_group: 分组中的所有队伍

        Returns:
            {
                'probability': float,  # 相遇概率
                'total_pairings': int,  # 总配对方案数
                'favorable_pairings': int,  # 包含目标对阵的方案数
                'teams': List[str],  # 分组中的队伍名称
            }
        """
        if len(teams_in_group) < 2:
            return {
                'probability': 0.0,
                'total_pairings': 0,
                'favorable_pairings': 0,
                'teams': [],
            }

        # 生成所有有效配对
        all_pairings = self.engine.generate_valid_pairings(teams_in_group)

        if not all_pairings:
            return {
                'probability': 0.0,
                'total_pairings': 0,
                'favorable_pairings': 0,
                'teams': [t.name for t in teams_in_group],
            }

        # 计算包含目标配对的方案数
        target_pairing_count = 0
        for pairing in all_pairings:
            for pair in pairing:
                if (pair[0].name == team1_name and pair[1].name == team2_name) or \
                   (pair[0].name == team2_name and pair[1].name == team1_name):
                    target_pairing_count += 1
                    break

        return {
            'probability': target_pairing_count / len(all_pairings) if all_pairings else 0.0,
            'total_pairings': len(all_pairings),
            'favorable_pairings': target_pairing_count,
            'teams': [t.name for t in teams_in_group],
        }

    def calculate_cross_group_probability_interactive(
        self, team1_name: str, team2_name: str, win_probabilities: Optional[Dict[tuple, float]] = None,
        skip_current_record: bool = False
    ) -> Dict:
        """
        交互式计算跨组相遇概率（基于用户输入的比赛胜率）

        Args:
            team1_name: 队伍1名称
            team2_name: 队伍2名称
            win_probabilities: 待定比赛的胜率字典 {(team1, team2): prob_team1_wins}
                             如果为None，表示需要询问用户
            skip_current_record: 是否跳过当前战绩组（用于处理同组但已确定不同对手的情况）

        Returns:
            详细的分析结果字典
        """
        team1 = self.stage.get_team_by_name(team1_name)
        team2 = self.stage.get_team_by_name(team2_name)

        result = {
            'need_input': False,
            'prerequisites': [],
            'impact_matches': [],
            'scenarios': [],
            'weighted_probability': 0.0,
            'explanation': '',
        }

        if not team1 or not team2:
            return result

        # 查找可能的共同目标分组
        possible_records = [(1, 1), (2, 1), (1, 2), (2, 2)]
        target_record = None

        for target_w, target_l in possible_records:
            # 如果 skip_current_record=True，跳过当前战绩组
            if skip_current_record and team1.wins == target_w and team1.losses == target_l:
                continue

            path1 = self._find_path_to_target_group(team1, target_w, target_l)
            path2 = self._find_path_to_target_group(team2, target_w, target_l)

            if path1 and path1['possible'] and path2 and path2['possible']:
                # 进一步检查：如果两队都在目标分组且都不需要移动，跳过
                if path1['wins_needed'] == 0 and path1['losses_needed'] == 0 and \
                   path2['wins_needed'] == 0 and path2['losses_needed'] == 0:
                    continue  # 已经在同一组但无法相遇（上层已处理）

                target_record = (target_w, target_l)
                result['prerequisites'] = [
                    {
                        'team': team1_name,
                        'current_record': team1.record,
                        'needs': self._describe_path(team1.wins, team1.losses, target_w, target_l, team1_name),
                        'pending_match': path1['pending_match'],
                    },
                    {
                        'team': team2_name,
                        'current_record': team2.record,
                        'needs': self._describe_path(team2.wins, team2.losses, target_w, target_l, team2_name),
                        'pending_match': path2['pending_match'],
                    },
                ]
                break

        if not target_record:
            result['explanation'] = f"{team1_name} 和 {team2_name} 无法到达共同的分组"
            return result

        target_w, target_l = target_record

        # 识别必要条件的比赛（排除在询问列表外）
        exclude_matches = []
        for prereq in result['prerequisites']:
            if prereq['pending_match']:
                exclude_matches.append(tuple(sorted([prereq['team'], prereq['pending_match']['opponent']])))

        # 识别影响目标分组的其他待定比赛
        impact_matches = self._identify_impact_matches(target_w, target_l, exclude_matches)
        result['impact_matches'] = impact_matches

        # 如果没有提供胜率，标记需要用户输入
        if win_probabilities is None:
            result['need_input'] = True
            return result

        # 枚举所有可能的比赛结果组合
        from itertools import product

        if not impact_matches:
            # 没有其他影响因素，直接计算
            match_results = {}
            for prereq in result['prerequisites']:
                if prereq['pending_match']:
                    t1 = prereq['team']
                    t2 = prereq['pending_match']['opponent']
                    match_key = (t1, t2)

                    # 根据需要的结果设置比赛结果
                    if prereq['needs'].startswith('赢'):
                        match_results[match_key] = 'team1_win'
                    elif prereq['needs'].startswith('输'):
                        match_results[match_key] = 'team2_win'

            teams_in_group = self._simulate_group_with_results(target_w, target_l, match_results)
            pairing_stats = self._calculate_pairing_probability(team1_name, team2_name, teams_in_group)

            result['scenarios'].append({
                'description': '唯一情况',
                'probability': 1.0,
                'new_teams': [t.name for t in teams_in_group if t.name not in [team1_name, team2_name]],
                'pairing_stats': pairing_stats,
            })
            result['weighted_probability'] = pairing_stats['probability']
        else:
            # 有其他影响因素，枚举所有组合
            # 为每场影响比赛生成两种结果
            impact_match_outcomes = []
            for match in impact_matches:
                impact_match_outcomes.append([
                    (match, 'team1_win'),
                    (match, 'team2_win'),
                ])

            # 生成所有组合
            for outcome_combo in product(*impact_match_outcomes):
                # 构建比赛结果字典
                match_results = {}

                # 添加必要条件的比赛结果
                for prereq in result['prerequisites']:
                    if prereq['pending_match']:
                        t1 = prereq['team']
                        t2 = prereq['pending_match']['opponent']
                        match_key = (t1, t2)

                        if 'wins_needed' in prereq and prereq.get('wins_needed', 0) > 0:
                            match_results[match_key] = 'team1_win'
                        elif 'losses_needed' in prereq and prereq.get('losses_needed', 0) > 0:
                            match_results[match_key] = 'team2_win'
                        # 根据描述判断
                        elif '赢' in prereq['needs']:
                            match_results[match_key] = 'team1_win'
                        elif '输' in prereq['needs']:
                            match_results[match_key] = 'team2_win'

                # 添加影响因素的比赛结果
                scenario_prob = 1.0
                for match, outcome in outcome_combo:
                    t1 = match['team1']
                    t2 = match['team2']
                    match_key = (t1, t2)
                    match_results[match_key] = outcome

                    # 计算该结果的概率
                    prob_key = tuple(sorted([t1, t2]))
                    if outcome == 'team1_win':
                        scenario_prob *= win_probabilities.get(prob_key, 0.5)
                    else:
                        scenario_prob *= (1 - win_probabilities.get(prob_key, 0.5))

                # 模拟分组构成
                teams_in_group = self._simulate_group_with_results(target_w, target_l, match_results)
                pairing_stats = self._calculate_pairing_probability(team1_name, team2_name, teams_in_group)

                # 构建情况描述
                new_teams = [t.name for t in teams_in_group if t.name not in [team1_name, team2_name]]

                result['scenarios'].append({
                    'description': f"情况 {len(result['scenarios']) + 1}",
                    'probability': scenario_prob,
                    'new_teams': new_teams,
                    'pairing_stats': pairing_stats,
                    'match_results': outcome_combo,
                })

                result['weighted_probability'] += scenario_prob * pairing_stats['probability']

        return result

    def _calculate_cross_group_paths(self, team1: Team, team2: Team) -> List[Dict]:
        """
        计算两支不同战绩队伍可能相遇的路径（条件概率）

        注意：此方法已被 calculate_cross_group_probability_interactive 替代，
        但保留用于向后兼容。

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
            # 检查两队是否都已确定当前组的对手（有待定比赛）
            team1_has_pending = team1.match_history and team1.match_history[-1][1] is None
            team2_has_pending = team2.match_history and team2.match_history[-1][1] is None

            # 如果两队都有待定对手，检查是否对阵的是彼此
            if team1_has_pending and team2_has_pending:
                team1_pending_opponent = team1.match_history[-1][0]
                team2_pending_opponent = team2.match_history[-1][0]

                # 如果他们的待定对手不是彼此，说明无法在当前组相遇
                if team1_pending_opponent != team2_name or team2_pending_opponent != team1_name:
                    # 他们已经确定了其他对手，无法在当前组相遇
                    # 转向跨组计算
                    result['same_group'] = False
                    result['can_meet_directly'] = False
                    result['reason'] = f"两队虽然战绩相同（{team1.record}），但已确定对阵其他队伍（{team1_name} vs {team1_pending_opponent}, {team2_name} vs {team2_pending_opponent}）"

                    # 使用交互式计算检查跨组相遇可能（跳过当前组）
                    interactive_result = self.calculate_cross_group_probability_interactive(
                        team1_name, team2_name, None, skip_current_record=True
                    )

                    if interactive_result.get('need_input'):
                        result['need_interactive'] = True
                        result['interactive_data'] = interactive_result
                        result['explanation'] = (
                            f"{team1_name} 和 {team2_name} 当前都在 {team1.record} 组，但已经确定了本轮对手。\n"
                            f"  • {team1_name} 将对阵 {team1_pending_opponent}\n"
                            f"  • {team2_name} 将对阵 {team2_pending_opponent}\n\n"
                            f"两队只能在后续轮次（根据比赛结果进入新的分组）相遇。\n"
                            f"系统需要您输入相关比赛的胜率估算才能计算精确概率。"
                        )
                    elif interactive_result.get('explanation'):
                        result['explanation'] = (
                            f"{team1_name} 和 {team2_name} 当前都在 {team1.record} 组，但已经确定了本轮对手。\n"
                            f"  • {team1_name} 将对阵 {team1_pending_opponent}\n"
                            f"  • {team2_name} 将对阵 {team2_pending_opponent}\n\n"
                            + interactive_result['explanation']
                        )

                    return result

            # 可以在当前组相遇
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
            # 不在同一组，使用交互式计算检查是否需要用户输入
            result['same_group'] = False
            result['can_meet_directly'] = False
            result['reason'] = f"战绩不同（{team1_name}: {team1.record}, {team2_name}: {team2.record}）"

            # 先调用交互式计算检查是否需要用户输入
            interactive_result = self.calculate_cross_group_probability_interactive(team1_name, team2_name, None)

            if interactive_result.get('need_input'):
                # 需要用户输入，返回相关信息
                result['need_interactive'] = True
                result['interactive_data'] = interactive_result
                result['explanation'] = (
                    f"{team1_name} 当前战绩 {team1.record}，{team2_name} 当前战绩 {team2.record}。\n\n"
                    f"两队不在同一分组，需要通过比赛结果移动到相同分组才能相遇。\n"
                    f"系统需要您输入相关比赛的胜率估算才能计算精确概率。"
                )
            elif interactive_result.get('explanation'):
                # 无法到达共同分组
                result['explanation'] = interactive_result['explanation']
            else:
                # 可以计算但没有影响因素（旧的条件概率路径）
                paths = self._calculate_cross_group_paths(team1, team2)
                result['paths'] = paths

                if paths:
                    result['explanation'] = (
                        f"{team1_name} 当前战绩 {team1.record}，{team2_name} 当前战绩 {team2.record}。\n\n"
                        f"两队不在同一分组，需要通过比赛结果移动到相同分组才能相遇。\n"
                        f"以下是可能的相遇路径及其条件概率：\n"
                    )
                    result['probability'] = 0.0
                else:
                    result['explanation'] = (
                        f"{team1_name} ({team1.record}) 和 {team2_name} ({team2.record}) "
                        f"在当前状态下无法在后续轮次相遇。"
                    )

            return result

    def calculate_all_matchup_probabilities(
        self, team_name: str
    ) -> Dict[str, Dict]:
        """
        计算一支队伍与所有可能对手的匹配概率

        相当于对每个活跃队伍都运行一遍 calculate_matchup_probability

        Args:
            team_name: 队伍名称

        Returns:
            对手名称到详细结果的映射，每个结果包含：
            {
                'probability': float,  # 相遇概率
                'same_group': bool,  # 是否在同一组
                'need_interactive': bool,  # 是否需要交互式输入
                'explanation': str,  # 简要说明
                ...
            }
        """
        team = self.stage.get_team_by_name(team_name)
        if not team or not team.is_active:
            return {}

        probabilities = {}

        # 遍历所有活跃队伍（不仅仅是同组队伍）
        for other_team in self.stage.get_active_teams():
            if other_team.name != team_name:
                # 对每个对手都运行一遍 calculate_matchup_probability
                result = self.calculate_matchup_probability(team_name, other_team.name)

                # 只有在有相遇可能时才添加（概率>0 或需要交互式输入）
                if result['probability'] > 0 or result.get('need_interactive', False):
                    probabilities[other_team.name] = result

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
"""
数据模型定义
"""
from dataclasses import dataclass, field
from typing import List, Set, Optional, Tuple


@dataclass(unsafe_hash=True)
class Team:
    """队伍类"""
    name: str = field(hash=True)
    wins: int = field(default=0, hash=False)
    losses: int = field(default=0, hash=False)
    opponents_played: Set[str] = field(default_factory=set, hash=False)
    match_history: List[Tuple[str, Optional[bool]]] = field(default_factory=list, hash=False)  # (对手名称, 是否获胜，None表示待定)

    @property
    def record(self) -> str:
        """获取战绩字符串"""
        return f"{self.wins}-{self.losses}"

    @property
    def is_qualified(self) -> bool:
        """是否已晋级"""
        return self.wins >= 3

    @property
    def is_eliminated(self) -> bool:
        """是否已淘汰"""
        return self.losses >= 3

    @property
    def is_active(self) -> bool:
        """是否还在比赛中"""
        return not self.is_qualified and not self.is_eliminated

    def can_play_against(self, other: 'Team') -> bool:
        """判断是否可以与另一队伍对战"""
        # 不能和自己打
        if self.name == other.name:
            return False
        # 不能和已经打过的队伍再打
        if other.name in self.opponents_played:
            return False
        return True

    def add_match_result(self, opponent: str, won: Optional[bool]):
        """添加比赛结果（won 为 None 表示待定比赛）"""
        if won is not None:
            self.opponents_played.add(opponent)
        self.match_history.append((opponent, won))
        if won is True:
            self.wins += 1
        elif won is False:
            self.losses += 1


@dataclass
class Match:
    """比赛类"""
    team1: str
    team2: str
    round_number: int
    winner: Optional[str] = None
    match_type: str = "BO1"  # BO1 或 BO3

    @property
    def loser(self) -> Optional[str]:
        """获取失败者"""
        if self.winner == self.team1:
            return self.team2
        elif self.winner == self.team2:
            return self.team1
        return None


@dataclass
class SwissStage:
    """瑞士轮赛事"""
    teams: List[Team]
    matches: List[Match] = field(default_factory=list)
    current_round: int = 1

    def get_teams_by_record(self, wins: int, losses: int) -> List[Team]:
        """获取特定战绩的队伍"""
        return [t for t in self.teams if t.wins == wins and t.losses == losses and t.is_active]

    def get_team_by_name(self, name: str) -> Optional[Team]:
        """通过名称获取队伍"""
        for team in self.teams:
            if team.name == name:
                return team
        return None

    def get_qualified_teams(self) -> List[Team]:
        """获取晋级队伍"""
        return [t for t in self.teams if t.is_qualified]

    def get_eliminated_teams(self) -> List[Team]:
        """获取淘汰队伍"""
        return [t for t in self.teams if t.is_eliminated]

    def get_active_teams(self) -> List[Team]:
        """获取仍在比赛的队伍"""
        return [t for t in self.teams if t.is_active]

    def is_stage_complete(self) -> bool:
        """判断瑞士轮是否结束"""
        return len(self.get_active_teams()) == 0
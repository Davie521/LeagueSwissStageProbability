#!/usr/bin/env python3
"""
测试概率计算功能
"""
from src.worlds_2025_data import load_current_swiss_stage
from src.swiss_engine import ProbabilityCalculator


def test_same_group_probability():
    """测试同组队伍相遇概率"""
    print("=" * 60)
    print("测试 1: 同组队伍相遇概率")
    print("=" * 60)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 测试 GEN vs TES (都是 2-1)
    result = calculator.calculate_matchup_probability("GEN", "TES")

    print(f"\n队伍: GEN vs TES")
    print(f"是否在同一组: {result['same_group']}")
    print(f"能否直接相遇: {result['can_meet_directly']}")
    print(f"相遇概率: {result['probability']:.1%}")
    print(f"\n详细解释:\n{result['explanation']}")

    if result['pairing_stats']:
        stats = result['pairing_stats']
        print(f"\n配对统计:")
        print(f"  - 总配对方案数: {stats['total_pairings']}")
        print(f"  - 包含该对阵的方案数: {stats['favorable_pairings']}")
        print(f"  - 组内队伍数: {stats['teams_in_group']}")


def test_cross_group_probability():
    """测试跨组队伍相遇概率"""
    print("\n\n" + "=" * 60)
    print("测试 2: 跨组队伍相遇概率")
    print("=" * 60)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 测试 BLG (1-2) vs CFO (2-2)
    result = calculator.calculate_matchup_probability("BLG", "CFO")

    print(f"\n队伍: BLG vs CFO")
    print(f"是否在同一组: {result['same_group']}")
    print(f"能否直接相遇: {result['can_meet_directly']}")
    print(f"原因: {result['reason']}")
    print(f"\n详细解释:\n{result['explanation']}")

    if result['paths']:
        print(f"\n可能的相遇路径:")
        for i, path in enumerate(result['paths'], 1):
            print(f"\n  路径 {i}:")
            print(f"    目标分组: {path['target_record']}")
            print(f"    BLG 需要: {path['team1_needs']}")
            print(f"    CFO 需要: {path['team2_needs']}")
            print(f"    条件概率: {path['probability']:.1%}")


def test_already_played():
    """测试已经交手过的队伍"""
    print("\n\n" + "=" * 60)
    print("测试 3: 已交手队伍")
    print("=" * 60)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 测试 GEN vs AL (已经打过)
    result = calculator.calculate_matchup_probability("GEN", "AL")

    print(f"\n队伍: GEN vs AL")
    print(f"能否相遇: {result['can_meet_directly']}")
    print(f"相遇概率: {result['probability']:.1%}")
    print(f"原因: {result['reason']}")
    print(f"\n详细解释:\n{result['explanation']}")


if __name__ == "__main__":
    try:
        test_same_group_probability()
        test_cross_group_probability()
        test_already_played()

        print("\n\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

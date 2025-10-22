#!/usr/bin/env python3
"""
测试详细配对方案展示功能
"""
from src.worlds_2025_data import load_current_swiss_stage
from src.swiss_engine import ProbabilityCalculator


def test_detailed_pairings_display():
    """测试详细配对方案的展示"""
    print("=" * 80)
    print("测试: 详细配对方案展示 (BLG vs TES)")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 使用 T1 赢 100%，MKOI 赢 100%
    win_probabilities = {
        ('100T', 'T1'): 0.0,  # T1 赢
        ('MKOI', 'TSW'): 1.0,  # MKOI 赢
    }

    result = calculator.calculate_cross_group_probability_interactive(
        "BLG", "TES", win_probabilities
    )

    print(f"\n加权平均相遇概率: {result['weighted_probability']:.1%}\n")

    # 只查看发生概率 > 0 的情况
    for i, scenario in enumerate(result['scenarios'], 1):
        if scenario['probability'] > 0:
            pairing_stats = scenario['pairing_stats']

            print(f"情况 {i} (发生概率 {scenario['probability']:.1%}):")
            print(f"  2-2组队伍: {', '.join(pairing_stats['teams'])}")
            print(f"  总配对方案数: {pairing_stats['total_pairings']}")
            print(f"  包含 BLG-TES 的方案数: {pairing_stats['favorable_pairings']}")
            print(f"  相遇概率: {pairing_stats['probability']:.1%}")

            # 重新生成配对方案以展示
            teams_in_group = []
            for team_name in pairing_stats['teams']:
                team = stage.get_team_by_name(team_name)
                if team:
                    # 模拟比赛结果
                    import copy
                    team_copy = copy.deepcopy(team)
                    teams_in_group.append(team_copy)

            # 应用必要的比赛结果
            for team in teams_in_group:
                if team.name == "BLG":
                    team.wins = 2
                    team.losses = 2
                elif team.name == "TES":
                    team.wins = 2
                    team.losses = 2
                elif team.name == "T1":
                    team.wins = 2
                    team.losses = 2
                elif team.name == "MKOI":
                    team.wins = 2
                    team.losses = 2

            all_pairings = calculator.engine.generate_valid_pairings(teams_in_group)

            print(f"\n  所有配对方案:")
            for j, pairing in enumerate(all_pairings, 1):
                pairs_str = ", ".join([f"{p[0].name}-{p[1].name}" for p in pairing])

                # 检查是否包含目标对阵
                has_target = False
                for pair in pairing:
                    if (pair[0].name == "BLG" and pair[1].name == "TES") or \
                       (pair[0].name == "TES" and pair[1].name == "BLG"):
                        has_target = True
                        break

                if has_target:
                    print(f"    ✓ 方案 {j}: {pairs_str}")
                else:
                    print(f"    ✗ 方案 {j}: {pairs_str}")

            print()

    print("=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print("\n说明:")
    print("  ✓ 标记表示该配对方案包含 BLG vs TES")
    print("  ✗ 标记表示该配对方案不包含该对阵")
    print("\n在实际程序中，✓ 的方案会用绿色高亮显示，")
    print("✗ 的方案会用灰色显示，让用户清楚看到哪些配对会导致两队相遇。")


if __name__ == "__main__":
    try:
        test_detailed_pairings_display()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

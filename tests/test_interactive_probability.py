#!/usr/bin/env python3
"""
测试交互式概率计算功能
"""
from src.worlds_2025_data import load_current_swiss_stage
from src.swiss_engine import ProbabilityCalculator


def test_same_group_matchup():
    """测试同组队伍相遇概率（GEN vs TES，都在 2-1）"""
    print("=" * 80)
    print("测试 1: 同组队伍相遇概率 (GEN vs TES)")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

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
        print(f"  - 组内队伍: {', '.join(stats['team_names'])}")

    assert result['same_group'] == True
    assert result['can_meet_directly'] == True
    assert result['probability'] == 1.0  # 只有两队，必然相遇

    print("\n✅ 测试通过！\n")


def test_cross_group_interactive():
    """测试跨组交互式概率计算（BLG vs TES）"""
    print("=" * 80)
    print("测试 2: 跨组交互式概率计算 (BLG 1-2 vs TES 2-1)")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 第一步：检查是否需要交互式输入
    result = calculator.calculate_matchup_probability("BLG", "TES")

    print(f"\n队伍: BLG vs TES")
    print(f"是否在同一组: {result['same_group']}")
    print(f"需要交互式输入: {result.get('need_interactive', False)}")

    if result.get('need_interactive'):
        interactive_data = result['interactive_data']

        print(f"\n必要前提条件:")
        for prereq in interactive_data['prerequisites']:
            print(f"  - {prereq['team']} ({prereq['current_record']}): {prereq['needs']}")
            if prereq['pending_match']:
                print(f"    对手: {prereq['pending_match']['opponent']}")

        print(f"\n影响因素比赛:")
        for match in interactive_data['impact_matches']:
            print(f"  - {match['team1']} ({match['team1_record']}) vs {match['team2']} ({match['team2_record']})")

        # 模拟用户输入（使用默认50%）
        print(f"\n使用默认胜率 50% 进行计算...")
        win_probabilities = {}
        for match in interactive_data['impact_matches']:
            match_key = tuple(sorted([match['team1'], match['team2']]))
            win_probabilities[match_key] = 0.5

        # 计算最终结果
        final_result = calculator.calculate_cross_group_probability_interactive(
            "BLG", "TES", win_probabilities
        )

        print(f"\n加权平均相遇概率: {final_result['weighted_probability']:.2%}")

        print(f"\n所有情况:")
        for i, scenario in enumerate(final_result['scenarios'], 1):
            print(f"\n  情况 {i}:")
            print(f"    新增队伍: {', '.join(scenario['new_teams']) if scenario['new_teams'] else '无'}")
            print(f"    发生概率: {scenario['probability']:.1%}")
            print(f"    配对方案: {scenario['pairing_stats']['favorable_pairings']}/{scenario['pairing_stats']['total_pairings']}")
            print(f"    相遇概率: {scenario['pairing_stats']['probability']:.1%}")

        assert final_result['weighted_probability'] > 0
        assert len(final_result['scenarios']) > 0

        print("\n✅ 测试通过！\n")
    else:
        print(f"\n⚠️  不需要交互式输入（可能已经有简单路径）")
        print(f"原因: {result.get('reason', '未知')}")


def test_cannot_meet():
    """测试无法相遇的情况（GEN vs AL，AL已晋级）"""
    print("=" * 80)
    print("测试 3: 无法相遇 (GEN vs AL - AL已晋级)")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    result = calculator.calculate_matchup_probability("GEN", "AL")

    print(f"\n队伍: GEN vs AL")
    print(f"能否相遇: {result['can_meet_directly']}")
    print(f"相遇概率: {result['probability']:.1%}")
    print(f"原因: {result['reason']}")
    print(f"\n详细解释:\n{result['explanation']}")

    assert result['probability'] == 0.0
    assert "AL" in result['reason']  # AL 不在比赛中

    print("\n✅ 测试通过！\n")


def test_pending_matches_identification():
    """测试待定比赛识别"""
    print("=" * 80)
    print("测试 4: 待定比赛识别")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    pending_matches = calculator._identify_pending_matches()

    print(f"\n找到 {len(pending_matches)} 场待定比赛:")
    for match in pending_matches:
        print(f"  - {match['team1']} ({match['team1_record']}) vs {match['team2']} ({match['team2_record']})")

    # 根据数据，应该有4场待定比赛
    expected_matches = [
        ("GEN", "TES"),  # Match 29
        ("MKOI", "TSW"),  # Match 28
        ("BLG", "VKS"),  # Match 30
        ("100T", "T1"),  # Match 31
    ]

    assert len(pending_matches) == 4
    for match in pending_matches:
        pair = (match['team1'], match['team2'])
        reverse_pair = (match['team2'], match['team1'])
        assert pair in expected_matches or reverse_pair in expected_matches

    print("\n✅ 测试通过！\n")


def test_group_simulation():
    """测试分组模拟"""
    print("=" * 80)
    print("测试 5: 分组模拟")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 模拟：BLG 赢 VKS，TES 输给 GEN，MKOI 赢 TSW，100T 赢 T1
    match_results = {
        ("BLG", "VKS"): "team1_win",  # BLG 赢
        ("GEN", "TES"): "team1_win",  # GEN 赢（TES 输）
        ("MKOI", "TSW"): "team1_win",  # MKOI 赢
        ("100T", "T1"): "team1_win",  # 100T 赢
    }

    teams_in_2_2 = calculator._simulate_group_with_results(2, 2, match_results)

    team_names = [t.name for t in teams_in_2_2]
    print(f"\n模拟后 2-2 组的队伍: {', '.join(team_names)}")

    # 应该包含：FLY, CFO (已经在2-2) + BLG, TES, MKOI, 100T (模拟结果)
    expected_teams = {"FLY", "CFO", "BLG", "TES", "MKOI", "100T"}
    actual_teams = set(team_names)

    print(f"期望队伍: {', '.join(sorted(expected_teams))}")
    print(f"实际队伍: {', '.join(sorted(actual_teams))}")

    assert expected_teams == actual_teams

    print("\n✅ 测试通过！\n")


def test_pairing_probability_with_restrictions():
    """测试带已交手限制的配对概率计算"""
    print("=" * 80)
    print("测试 6: 配对概率计算（考虑已交手限制）")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 使用前面模拟的2-2组
    match_results = {
        ("BLG", "VKS"): "team1_win",
        ("GEN", "TES"): "team1_win",
        ("MKOI", "TSW"): "team1_win",
        ("100T", "T1"): "team1_win",
    }

    teams_in_group = calculator._simulate_group_with_results(2, 2, match_results)

    pairing_stats = calculator._calculate_pairing_probability("BLG", "TES", teams_in_group)

    print(f"\nBLG vs TES 在该组的配对概率:")
    print(f"  - 总配对方案数: {pairing_stats['total_pairings']}")
    print(f"  - 包含该对阵的方案数: {pairing_stats['favorable_pairings']}")
    print(f"  - 相遇概率: {pairing_stats['probability']:.1%}")
    print(f"  - 组内队伍: {', '.join(pairing_stats['teams'])}")

    # BLG 打过 100T，TES 也打过 100T
    # 所以配对时要考虑这些限制
    print(f"\n已交手限制:")
    blg = next(t for t in teams_in_group if t.name == "BLG")
    tes = next(t for t in teams_in_group if t.name == "TES")
    print(f"  - BLG 已对阵: {', '.join(blg.opponents_played)}")
    print(f"  - TES 已对阵: {', '.join(tes.opponents_played)}")

    assert pairing_stats['probability'] > 0
    assert pairing_stats['total_pairings'] > 0

    print("\n✅ 测试通过！\n")


if __name__ == "__main__":
    try:
        test_same_group_matchup()
        test_cross_group_interactive()
        test_cannot_meet()
        test_pending_matches_identification()
        test_group_simulation()
        test_pairing_probability_with_restrictions()

        print("=" * 80)
        print("🎉 所有测试通过！")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ 断言失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

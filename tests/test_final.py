#!/usr/bin/env python3
"""
最终集成测试 - 验证所有功能
"""
from src.worlds_2025_data import load_current_swiss_stage
from src.swiss_engine import ProbabilityCalculator

def main():
    print("=" * 80)
    print("🎉 最终集成测试")
    print("=" * 80)

    stage = load_current_swiss_stage()
    calculator = ProbabilityCalculator(stage)

    # 测试1: 同组队伍
    print("\n✅ 测试1: 同组队伍 (GEN vs TES)")
    result1 = calculator.calculate_matchup_probability("GEN", "TES")
    print(f"   相遇概率: {result1['probability']:.1%}")
    print(f"   是否在同组: {result1['same_group']}")
    assert result1['probability'] == 1.0

    # 测试2: 跨组交互式（检查是否需要输入）
    print("\n✅ 测试2: 跨组队伍 (BLG vs TES)")
    result2 = calculator.calculate_matchup_probability("BLG", "TES")
    print(f"   需要交互式输入: {result2.get('need_interactive', False)}")

    if result2.get('need_interactive'):
        interactive_data = result2['interactive_data']
        print(f"   必要前提条件数: {len(interactive_data['prerequisites'])}")
        print(f"   影响因素比赛数: {len(interactive_data['impact_matches'])}")

        # 使用50%胜率计算
        win_probs = {}
        for match in interactive_data['impact_matches']:
            match_key = tuple(sorted([match['team1'], match['team2']]))
            win_probs[match_key] = 0.5

        final_result = calculator.calculate_cross_group_probability_interactive(
            "BLG", "TES", win_probs
        )
        print(f"   加权平均概率: {final_result['weighted_probability']:.2%}")
        print(f"   情况数量: {len(final_result['scenarios'])}")
        assert final_result['weighted_probability'] > 0
        assert len(final_result['scenarios']) > 0

    # 测试3: 无法相遇
    print("\n✅ 测试3: 无法相遇 (GEN vs AL)")
    result3 = calculator.calculate_matchup_probability("GEN", "AL")
    print(f"   相遇概率: {result3['probability']:.1%}")
    print(f"   原因: {result3['reason']}")
    assert result3['probability'] == 0.0

    # 测试4: 待定比赛识别
    print("\n✅ 测试4: 待定比赛识别")
    pending = calculator._identify_pending_matches()
    print(f"   待定比赛数: {len(pending)}")
    for match in pending:
        print(f"   - {match['team1']} vs {match['team2']}")
    assert len(pending) == 4

    # 测试5: 分组模拟
    print("\n✅ 测试5: 分组模拟")
    match_results = {
        ("BLG", "VKS"): "team1_win",
        ("GEN", "TES"): "team1_win",
        ("MKOI", "TSW"): "team1_win",
        ("100T", "T1"): "team1_win",
    }
    teams_2_2 = calculator._simulate_group_with_results(2, 2, match_results)
    team_names = [t.name for t in teams_2_2]
    print(f"   2-2组队伍: {', '.join(team_names)}")
    assert "BLG" in team_names
    assert "TES" in team_names

    print("\n" + "=" * 80)
    print("🎉 所有测试通过！系统运行正常！")
    print("=" * 80)
    print("\n📝 使用说明:")
    print("   运行 'python3 run.py' 开始使用交互式概率计算系统")
    print("   选择功能 3 来计算两队相遇概率")
    print("\n✨ 新功能亮点:")
    print("   • 智能识别待定比赛")
    print("   • 交互式询问影响因素的胜率")
    print("   • 枚举所有可能情况并加权平均")
    print("   • 考虑已交手限制的精确配对概率")
    print("   • 详细的表格和解释说明")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

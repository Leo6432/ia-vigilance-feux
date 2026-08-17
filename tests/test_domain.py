from ia_vigilance_feux.domain import VigilanceLevel, probabilities_to_score, score_to_level


def test_score_to_level_default_thresholds():
    assert score_to_level(0) == VigilanceLevel.GREEN
    assert score_to_level(25) == VigilanceLevel.YELLOW
    assert score_to_level(50) == VigilanceLevel.ORANGE
    assert score_to_level(75) == VigilanceLevel.RED


def test_probabilities_to_score():
    score = probabilities_to_score(
        {
            VigilanceLevel.GREEN: 0.0,
            VigilanceLevel.YELLOW: 0.0,
            VigilanceLevel.ORANGE: 0.5,
            VigilanceLevel.RED: 0.5,
        }
    )
    assert score == 83.33

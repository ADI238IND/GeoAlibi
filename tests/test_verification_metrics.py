import numpy as np
import pytest
from geoalibi.verification_metrics import transition_counts, summarize_transitions


def mask(values):
    return np.array([values], dtype=bool)


def test_all_abstention_exposes_lost_true_changes_and_removed_false_alarms():
    result = summarize_transitions(transition_counts(mask([1, 1, 1, 0]), mask([0, 0, 0, 0]), mask([1, 1, 0, 1])))
    assert result['removed_true_positive_pixels'] == 2
    assert result['removed_false_positive_pixels'] == 1
    assert result['proposal_retention_fraction'] == 0
    assert result['removed_true_positive_fraction'] == 1
    assert result['net_recall_change'] == -2 / 3


def test_empty_denominators_are_unknown_not_perfect():
    result = summarize_transitions(transition_counts(mask([0, 0]), mask([0, 0]), mask([0, 0])))
    for field in ('proposal_retention_fraction', 'removed_true_positive_fraction', 'removed_false_positive_fraction', 'net_recall_change'):
        assert result[field] is None


def test_added_errors_cannot_be_hidden_by_removed_pixels():
    result = summarize_transitions(transition_counts(mask([1, 0, 0, 0]), mask([0, 1, 1, 1]), mask([0, 0, 0, 1])))
    assert result['removed_false_positive_pixels'] == 1
    assert result['added_false_positive_pixels'] == 2
    assert result['net_false_positive_reduction_pixels'] == -1
    assert result['net_recall_change'] == 1


def test_aggregate_rates_are_pixel_weighted():
    a = transition_counts(mask([1]), mask([0]), mask([1]))
    b = transition_counts(mask([1]*9), mask([1]*9), mask([1]*9))
    result = summarize_transitions({k: a[k] + b[k] for k in a})
    assert result['removed_true_positive_fraction'] == .1
    assert result['proposal_retention_fraction'] == .9


def test_shape_and_type_mismatch_fail():
    with pytest.raises(ValueError):
        transition_counts(mask([1, 0]), mask([0]), mask([1, 0]))
    with pytest.raises(ValueError):
        transition_counts(np.array([[255]], dtype=np.uint8), mask([1]), mask([1]))

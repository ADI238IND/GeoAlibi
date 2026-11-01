import pytest
from geoalibi.evaluation_selection import select_scenes


def members():
    return [f'{folder}/test_{n}.png' for folder in ('A', 'B', 'label') for n in range(12)]


def plan():
    return {'count': 8, 'excluded_parent_scenes': ['test_2.png'], 'rank_prefix': 'fixed:'}


def test_selection_is_order_independent_and_excludes_used_parent():
    selected = select_scenes(members(), plan())
    assert selected == select_scenes(list(reversed(members())), plan())
    assert len(selected) == len(set(selected)) == 8
    assert 'test_2.png' not in selected
    assert selected == select_scenes(members() + ['A/../secret.png', 'README.md'], plan())


def test_missing_labels_and_insufficient_unused_scenes_fail():
    with pytest.raises(ValueError, match='sets differ'):
        select_scenes(members()[:-1], plan())
    p = plan(); p['excluded_parent_scenes'] = [f'test_{n}.png' for n in range(10)]
    with pytest.raises(ValueError, match='Not enough'):
        select_scenes(members(), p)


@pytest.mark.parametrize('count', [0, 17, True, 1.5])
def test_selection_count_is_bounded(count):
    p = plan(); p['count'] = count
    with pytest.raises(ValueError):
        select_scenes(members(), p)


def test_generator_and_duplicate_members():
    assert select_scenes(iter(members()), plan()) == select_scenes(members(), plan())
    with pytest.raises(ValueError, match='Duplicate'):
        select_scenes(members() + [members()[0]], plan())

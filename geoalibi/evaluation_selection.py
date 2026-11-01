"""Deterministic scene selection without inspecting imagery or labels."""
import hashlib
import re


def select_scenes(members, plan):
    if type(plan.get('count')) is not int or not 1 <= plan['count'] <= 16:
        raise ValueError('Select between 1 and 16 scenes.')
    members = tuple(members)
    scene_members = [name for name in members if re.fullmatch(r'(A|B|label)/test_[0-9]+\.png', name)]
    if len(scene_members) != len(set(scene_members)):
        raise ValueError('Duplicate archive scene members are ambiguous.')
    sets = [{name.split('/')[1] for name in members
             if re.fullmatch(folder + r'/test_[0-9]+\.png', name)}
            for folder in ('A', 'B', 'label')]
    if not sets[0] or any(names != sets[0] for names in sets[1:]):
        raise ValueError('Archive A/B/label scene sets differ or are empty.')
    excluded = set(plan['excluded_parent_scenes'])
    eligible = sets[0] - excluded
    if len(eligible) < plan['count']:
        raise ValueError('Not enough unused matching scenes.')
    ranked = sorted(eligible, key=lambda name: (hashlib.sha256((plan['rank_prefix'] + name).encode()).hexdigest(), name))
    return ranked[:plan['count']]

"""Account for both removed false alarms and removed true changes."""
import numpy as np


def transition_counts(proposal, supported, truth):
    arrays = [np.asarray(x) for x in (proposal, supported, truth)]
    if any(x.dtype != bool or x.ndim != 2 or x.shape != arrays[0].shape for x in arrays):
        raise ValueError('Transition masks must be matching two-dimensional boolean arrays.')
    proposal, supported, truth = arrays
    removed = proposal & ~supported
    added = supported & ~proposal
    return {'pixels': int(truth.size), 'truth_change_pixels': int(truth.sum()),
            'proposal_pixels': int(proposal.sum()), 'supported_pixels': int(supported.sum()),
            'proposal_true_positive_pixels': int((proposal & truth).sum()),
            'proposal_false_positive_pixels': int((proposal & ~truth).sum()),
            'removed_true_positive_pixels': int((removed & truth).sum()),
            'removed_false_positive_pixels': int((removed & ~truth).sum()),
            'added_true_positive_pixels': int((added & truth).sum()),
            'added_false_positive_pixels': int((added & ~truth).sum()),
            'retained_proposal_pixels': int((proposal & supported).sum())}


def summarize_transitions(counts):
    def ratio(numerator, denominator):
        return numerator / denominator if denominator else None
    return {**counts,
            'proposal_retention_fraction': ratio(counts['retained_proposal_pixels'], counts['proposal_pixels']),
            'removed_true_positive_fraction': ratio(counts['removed_true_positive_pixels'], counts['proposal_true_positive_pixels']),
            'removed_false_positive_fraction': ratio(counts['removed_false_positive_pixels'], counts['proposal_false_positive_pixels']),
            'net_recall_change': ratio(counts['added_true_positive_pixels'] - counts['removed_true_positive_pixels'], counts['truth_change_pixels']),
            'net_false_positive_reduction_pixels': counts['removed_false_positive_pixels'] - counts['added_false_positive_pixels'],
            'note': 'Removed proposal pixels include review, nuisance rejection, small/omitted regions and filtering; they are not all abstentions. These are pixel transitions, not calibrated selective risk or physical area.'}

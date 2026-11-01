"""Explain diagnostic state and inspection coverage without changing any verdict."""


def assess(report):
    regions = report['regions']; count = report['candidate_count']
    omitted = max(0, count - len(regions))
    supported = report['supported_changed_pixels']
    if not report['alignment']['reliable']:
        code, title = 'alignment_unresolved', 'Alignment needs independent evidence'
        detail = 'The registration reliability gate did not pass. An empty supported mask cannot establish that the scene is unchanged.'
        action = 'Check stationary landmarks and acquisition metadata before interpreting these candidates.'
    elif omitted:
        code, title = 'partial_inspection', 'Candidate inspection is incomplete'
        detail = f'{omitted} eligible regions were omitted from the bounded inspection. Conclusions cover the inspected regions only.'
        action = 'Inspect the omitted candidates separately before drawing a scene-wide conclusion.'
    elif report['counts']['review']:
        code, title = 'review_required', 'Independent evidence is still needed'
        detail = 'Some inspected candidates remain unresolved. Zero supported pixels, when present, do not rule out real change.'
        action = 'Review each unresolved candidate and record independent evidence.'
    elif supported:
        code, title = 'supported_candidates', 'Some candidates survive the tested explanations'
        detail = 'Supported pixels are a diagnostic result. Untested acquisition, seasonal and local appearance effects remain possible.'
        action = 'Inspect the challenge logs and seek an independent observation before acting.'
    elif not count:
        code, title = 'no_candidates', 'No eligible candidates at these settings'
        detail = 'Filtering and the minimum-area setting produced no inspectable regions. This does not prove the scene is unchanged.'
        action = 'Check image quality, footprint and settings; retain this run before any further investigation.'
    else:
        code, title = 'no_supported_candidates', 'No candidates were supported'
        detail = 'The inspected differences were explained by the tested nuisance hypotheses. Unobserved or filtered changes may remain.'
        action = 'Review the explanations and acquisition context before treating this as absence of change.'
    return {'schema': 'geoalibi-assessment-v1', 'code': code, 'title': title, 'detail': detail, 'next_step': action,
            'eligible_regions': count, 'inspected_regions': len(regions), 'omitted_regions': omitted,
            'supported_pixels': supported, 'coverage': report.get('inspection'),
            'scope': 'Automated diagnostic only. Human reviews and provider interpretations do not replace these automated verdicts. Pixel counts are image coordinates, not physical area.'}


def assessment_markdown(report):
    a = assess(report)
    lines = ['# Investigation scope', '', a['title'], '', a['detail'], '',
             f"Eligible regions: {a['eligible_regions']}; inspected: {a['inspected_regions']}; omitted: {a['omitted_regions']}.",
             f"Supported pixels: {a['supported_pixels']}.", '']
    c = a['coverage']
    if c is not None:
        lines.extend([f"Candidate pixels before morphology: {c['proposal_pixels']}; after morphology: {c['morphology_pixels']}.",
                      f"Eligible-region pixels: {c['eligible_region_pixels']}; inspected-region pixels: {c['inspected_region_pixels']}; omitted-region pixels: {c['omitted_region_pixels']}.",
                      f"Pixels in components below minimum area: {c['below_min_area_pixels']}.",
                      'When included, images/omitted_mask.png locates only eligible regions omitted by the inspection cap; images/omitted_overlay.png marks them in purple. Small filtered components are excluded.',
                      'Morphology can add or remove pixels. Region footprint counts are not the supported mask, accuracy, confidence or physical area.', ''])
    else:
        lines.extend(['Detailed pixel coverage was not recorded for this older investigation and has not been reconstructed.', ''])
    return '\n'.join(lines + ['Next: ' + a['next_step'], '', a['scope'],
                             'Unsigned packet checksums establish content consistency, not acquisition authenticity or correctness.', ''])

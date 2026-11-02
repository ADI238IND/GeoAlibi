"""Render a portable rehearsal page from generated scenarios and checked saved evidence."""
import html
import re


def rate(value):
    return 'undefined' if value is None else f'{value * 100:.2f}%'


def render_player(scenarios, evidence, source_hash):
    buttons=[]
    for i, item in enumerate(scenarios):
        case=item['case']; counts=item['counts']
        if not re.fullmatch('[a-z][a-z0-9_-]*',case) or any(type(counts[k]) is not int or counts[k]<0 for k in ('supported','artifact','review')):
            raise ValueError('Invalid procedural scenario identity or counts.')
        buttons.append(f'<button type="button" data-case="{case}" data-title="{html.escape(item["title"],quote=True)}" '
                       f'data-supported="{counts["supported"]}" data-artifact="{counts["artifact"]}" data-review="{counts["review"]}" '
                       f'aria-pressed="{"true" if i==0 else "false"}">{html.escape(item["title"])}</button>')
    rows=[]
    for key,label in [('baseline','RGB baseline'),('unet','Pinned U-Net')]:
        m=evidence['arms'][key]['metrics']
        rows.append('<tr><th>'+label+'</th>'+''.join('<td>'+rate(x)+'</td>' for x in
                    (m['proposals']['f1'],m['supported']['recall'],m['supported']['precision']))+'</tr>')
    zero=sum(evidence['arms'][key]['metrics']['supported']['tp']+evidence['arms'][key]['metrics']['supported']['fp']==0 for key in ('baseline','unet'))
    accepted='Both supported arms accepted zero pixels.' if zero==2 else 'Saved supported masks are diagnostic results.'
    status=f"{accepted} The U-Net registration gate flagged {evidence['pair_count']-evidence['arms']['unet']['registration_flagged_reliable_pairs']}/{evidence['pair_count']} scenes unreliable. Useful proposals do not establish verified-change performance."
    from pathlib import Path
    page=(Path(__file__).parent/'static/demo-player.html').read_text()
    return page.replace('<!--EVIDENCE_STATUS-->',html.escape(status)).replace('<!--SCENARIOS-->',''.join(buttons)).replace('<!--RESULTS-->',''.join(rows)).replace('<!--SOURCE-->',html.escape(source_hash)).replace('<!--PAIR_COUNT-->',str(evidence['pair_count']))


def recording_script(evidence):
    unet=evidence['arms']['unet']; baseline=evidence['arms']['baseline']
    return f'''# GeoAlibi recording rehearsal

Three-minute draft for Aditya Singhal. Confirm the organizer's actual length, format and deliverable requirements before recording or submitting. This draft is not a completed submission.

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | Offline player introduction | Apparent satellite change can come from alignment, lighting or local appearance. GeoAlibi records the alternative explanations and asks for evidence before supporting a candidate. |
| 0:25–0:55 | Generated structural/shadow scenario, compare slider | These images are procedural illustrations. Compare the before image with the candidate overlay. Region counts describe this illustration, not satellite accuracy. |
| 0:55–1:20 | Shift and lighting scenarios | The checks can explain nuisance differences. An empty supported mask alone is not proof that a scene is unchanged. |
| 1:20–2:00 | Download a scenario packet; inspect SUMMARY.md/report/manifest | The packet retains the scope and source/derived images. Unsigned checksums establish content consistency, not acquisition authenticity. If using the local workstation, show a linked continuation and its per-batch limits; the offline gallery does not run new investigations. |
| 2:00–2:40 | Saved satellite-results table and JSON links | On {evidence['pair_count']} frozen full test scenes, U-Net proposal F1 was {rate(unet['metrics']['proposals']['f1'])}, versus {rate(baseline['metrics']['proposals']['f1'])} for RGB proposals. Supported recall was {rate(unet['metrics']['supported']['recall'])}; supported precision is {rate(unet['metrics']['supported']['precision'])}. The existing registration gate flagged {evidence['pair_count']-unet['registration_flagged_reliable_pairs']} of {evidence['pair_count']} scenes unreliable. This small diagnostic is not a full or audited training/geographic-independent benchmark. |
| 2:40–3:00 | Evidence limits and next steps | Independent landmark collection/separate review and corrected real-image Muse/SAM validation are still outstanding. This offline run makes no provider calls. Completed candidate inspection does not certify real-world change. |

Before the final take: retain the exact commit/source manifest and dependency versions, verify the packet, check every spoken metric against recorded-research-evidence.json, and disclose procedural images/cached results. Do not display credentials or billing pages in the recording. A live Meta segment requires secure credentials, existing ledger reconciliation and billing checks; historical $0.54 remains unreconciled. Never reset the ledger to gain testing allowance.

The player contains generated imagery only. No original satellite imagery, model weights or credentials are packaged. Use the local workstation instructions for interactive uploads, review and continuation; no public deployment is needed. Competition submission remains a separate final action after participant requirements are confirmed.
'''

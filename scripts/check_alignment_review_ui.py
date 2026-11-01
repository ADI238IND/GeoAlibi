"""Browser contract test using generated images; no real landmark or benchmark claim."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from geoalibi.alignment_review import build_review
from geoalibi.benchmark_manifest import freeze_dataset


def main():
    out = Path('test-results'); out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='blind-review-ui-') as temporary:
        root = Path(temporary); dataset = root / 'dataset'
        for folder in ('A', 'B', 'label'):
            (dataset / folder).mkdir(parents=True)
            for i in range(2):
                Image.new('RGB' if folder != 'label' else 'L', (256, 256)).save(dataset / folder / f'fixture{i}.png')
        manifest = root / 'inputs.json'; manifest.write_text(json.dumps(freeze_dataset(dataset, 'Generated browser fixtures.')))
        bundle = root / 'bundle'; summary = build_review(dataset, manifest, bundle)
        with sync_playwright() as p:
            options = {'headless': True, 'args': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']}
            if os.getenv('GEOALIBI_TEST_BROWSER'): options['executable_path'] = os.environ['GEOALIBI_TEST_BROWSER']
            browser = p.chromium.launch(**options)
            page = browser.new_page(viewport={'width': 1450, 'height': 1000})
            errors = []; network = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: network.append(request.url) if request.url.startswith(('https:', 'http:')) else None)
            page.goto((bundle / 'review.html').as_uri())
            page.wait_for_function('loaded')
            page.locator('#annotator').fill('fixture-author')
            points = [(30, 30), (210, 30), (30, 210), (210, 210), (90, 90), (150, 150)]
            for i in range(2):
                page.select_option('#scene', str(i)); page.wait_for_function('loaded')
                for x, y in points:
                    for side in ('after', 'before'):
                        canvas = page.locator('#' + side); box = canvas.bounding_box()
                        canvas.click(position={'x': x * box['width'] / 256, 'y': y * box['height'] / 256})
                assert '6/20 points' in page.locator('#progress').inner_text()
            assert page.locator('#export').is_disabled()
            page.locator('#attest').check()
            with page.expect_download() as download:
                page.locator('#draft').click()
            draft_path = root / 'draft.json'; download.value.save_as(draft_path)
            draft = json.loads(draft_path.read_text())
            assert draft['schema'] == 'geoalibi-alignment-draft-v1'
            assert all(len(r['landmarks']) == 6 and 'reviewer' not in r for r in draft['pairs'])
            # Wrong task binding is rejected without replacing the working draft.
            wrong = dict(draft, dataset_manifest_sha256='0' * 64)
            wrong_path = root / 'wrong.json'; wrong_path.write_text(json.dumps(wrong))
            page.locator('#import').set_input_files(wrong_path)
            page.wait_for_function("document.getElementById('status').textContent.startsWith('Import rejected:')")
            page.select_option('#mode', 'review')
            page.locator('#import').set_input_files(draft_path)
            page.wait_for_function("document.getElementById('status').textContent.startsWith('Draft imported.')")
            page.locator('#reviewer').fill(' FIXTURE-AUTHOR '); page.locator('#attest').check()
            assert page.locator('#approve').is_disabled()
            page.locator('#reviewer').fill('fixture-reviewer'); page.locator('#attest').click(); page.locator('#attest').check()
            for i in range(2):
                page.select_option('#scene', str(i)); page.wait_for_function('loaded')
                page.locator('#approve').check()
                if i == 0: assert page.locator('#export').is_disabled()
            assert page.locator('#undo').is_disabled()
            with page.expect_download() as download:
                page.locator('#export').click()
            reviewed_path = root / 'reviewed.json'; download.value.save_as(reviewed_path)
            reviewed = json.loads(reviewed_path.read_text())
            assert all(r['reviewed'] is True and r['reviewer'] == 'fixture-reviewer' for r in reviewed['pairs'])
            # Feed the actual browser export through the real CLI scorer.
            benchmark = root / 'benchmark.json'
            source = json.loads(manifest.read_text())
            benchmark.write_text(json.dumps({'dataset_frozen': True, 'dataset_manifest_sha256': summary['dataset_manifest_sha256'],
                'subset_limit': 0, 'pairs': 2, 'pair_results': [{'file': r['file'], 'source_hashes': r,
                'alignment': {'matrix': [[1, 0, 0], [0, 1, 0]], 'method': 'fixture', 'reliable': False}} for r in source['pairs']]}))
            command = [sys.executable, 'scripts/check_benchmark_alignment.py', str(benchmark), str(reviewed_path), str(dataset),
                       '--dataset-manifest', str(manifest), '--output', str(root / 'scored.json')]
            result = subprocess.run(command, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            scored = json.loads((root / 'scored.json').read_text())
            assert scored['production_reliable_count'] == 0
            assert all(row['transform_rms_px'] < .05 for row in scored['pairs'])
            page.screenshot(path=str(out / 'alignment-review-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(out / 'alignment-review-mobile.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            # Changing the reviewer invalidates all approvals.
            page.locator('#reviewer').fill('third-reviewer'); page.locator('#reviewer').blur()
            assert page.locator('#export').is_disabled()
            assert not errors, errors
            assert not network, network
            browser.close()
        (out / 'alignment-review-ui.json').write_text(json.dumps({'synthetic': True, 'pairs': 2,
            'browser_export_cli_roundtrip': True, 'external_requests': 0, 'page_errors': errors}) + '\n')
        print('Blind review browser/CLI roundtrip passed; generated contract fixtures only.')


if __name__ == '__main__': main()

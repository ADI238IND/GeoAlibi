"""Local browser smoke test; requires Playwright and an installed Chromium binary."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

from geoalibi.demo import pair, scene
from geoalibi.vision import png


def main():
    root = Path(__file__).resolve().parents[1]
    out = Path(os.getenv("GEOALIBI_UI_OUTPUT", str(root / "test-results")))
    out.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(prefix="geoalibi-ui-") as tmp:
        env = {**os.environ, "GEOALIBI_DATA_DIR": tmp, "MODEL_API_KEY": ""}
        with (out / "server.log").open("w") as log:
            server = subprocess.Popen([sys.executable, "-m", "uvicorn", "geoalibi.app:app", "--host", "127.0.0.1", "--port", "8089"], cwd=root, env=env, stdout=log, stderr=log)
            try:
                with httpx.Client(trust_env=False) as client:
                    for attempt in range(100):
                        try:
                            if client.get("http://127.0.0.1:8089/api/status").is_success:
                                break
                        except httpx.ConnectError:
                            time.sleep(.1)
                    else:
                        raise RuntimeError("Local test server did not start.")
                with sync_playwright() as p:
                    options = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]}
                    if os.getenv("GEOALIBI_TEST_BROWSER"):
                        options["executable_path"] = os.environ["GEOALIBI_TEST_BROWSER"]
                    browser = p.chromium.launch(**options)
                    page = browser.new_page(viewport={"width": 1500, "height": 1000}, device_scale_factor=1)
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto("http://127.0.0.1:8089")
                    page.wait_for_function("() => document.querySelector('#meta-state').textContent.includes('not configured')")
                    assert page.locator("#use-meta").is_disabled()
                    page.locator("#run").click()
                    page.locator("#results").wait_for(state="visible")
                    assert page.locator("#count-supported").inner_text() == "2"
                    assert page.locator("#count-review").inner_text() == "4"
                    assert page.locator("#assessment-panel").get_attribute("data-state") == "review_required"
                    page.locator("#inspect-proposals").click()
                    assert page.locator('[data-view="proposal_mask"]').get_attribute("aria-pressed") == "true"
                    page.wait_for_function("() => {const img=document.querySelector('#base-image');return img.complete && img.naturalWidth > 0;}")
                    page.locator('[data-filter="review"]').click()
                    assert page.locator("#regions .region").count() == 4
                    page.locator("#regions .region").first.click()
                    page.get_by_label("Human review decision").select_option("needs_field_check")
                    page.get_by_label("Review evidence note").fill("Third acquisition needed for shadow review.")
                    page.get_by_role("button", name="Save review").click()
                    page.wait_for_function("() => document.querySelector('.review-note').textContent.startsWith('1 review')")
                    page.get_by_label("Evidence source reference").first.fill("field-report-42")
                    page.get_by_label("Evidence observation").first.fill("Independent observation; date uncertain.")
                    page.get_by_role("button", name="Record evidence response").first.click()
                    page.get_by_text("Latest response: provided", exact=True).wait_for()
                    page.get_by_label("Evidence response status").first.select_option("retracted")
                    page.get_by_label("Evidence observation").first.fill("Wrong acquisition date.")
                    page.get_by_role("button", name="Record evidence response").first.click()
                    page.get_by_text("Latest response: retracted", exact=True).wait_for()
                    assert page.get_by_text("Independent observation; date uncertain.", exact=False).count() == 1
                    page.locator('[data-view="heatmap"]').click()
                    page.locator('[data-view="supported_mask"]').click()
                    page.locator('[data-view="swipe"]').click()
                    page.locator("#swipe").fill("72")
                    with page.expect_download() as info:
                        page.locator("#export").click()
                    download = info.value
                    download.save_as(out / "evidence-export.json")
                    assert json.loads((out / "evidence-export.json").read_text())["audit"][0]["decision"] == "needs_field_check"
                    with page.expect_download() as packet_info:
                        page.locator("#packet").click()
                    packet_info.value.save_as(out / "evidence-packet.zip")
                    from geoalibi.dossier import verify_packet
                    assert verify_packet((out / "evidence-packet.zip").read_bytes())["files"]["report.json"]
                    assert verify_packet((out / "evidence-packet.zip").read_bytes())["files"]["SUMMARY.md"]
                    page.screenshot(path=str(out / "desktop.png"), full_page=True)
                    for case in ["shift", "light", "unchanged"]:
                        page.locator(f'[data-case="{case}"]').click()
                        with page.expect_response("**/api/demo"):
                            page.locator("#run").click()
                        page.locator("#loading").wait_for(state="hidden")
                        assert page.locator("#count-supported").inner_text() == "0"
                    a, b, _ = pair("mixed")
                    before, after = Path(tmp) / "a.png", Path(tmp) / "b.png"
                    before.write_bytes(png(a))
                    after.write_bytes(png(b))
                    page.locator("#toggle-upload").click()
                    page.locator("#before").set_input_files(before)
                    page.locator("#after").set_input_files(after)
                    page.locator('#landmark-picker summary').click()
                    page.wait_for_function("() => document.querySelector('#picker-state').textContent.includes('Add 6 more')")
                    def pick(side, x, y):
                        canvas=page.locator('#pick-'+side)
                        # 640 square images are letterboxed inside a 512 × 384 canvas.
                        canvas.click(position={'x':(64+x*.6)*canvas.bounding_box()['width']/512,
                                               'y':y*.6*canvas.bounding_box()['height']/384})
                    page.locator('#pick-before').focus()
                    page.locator('#pick-before').press('ArrowRight')
                    page.locator('#pick-before').press('Enter')
                    page.locator('#pick-after').focus()
                    page.locator('#pick-after').press('ArrowRight')
                    page.locator('#pick-after').press('Enter')
                    assert '1 complete pairs' in page.locator('#picker-state').inner_text()
                    page.locator('#clear-landmarks').click()
                    points=[(50,50),(580,50),(50,580),(580,580),(150,180),(480,440)]
                    for x,y in points:
                        pick('before',x,y)
                        pick('after',x,y)
                    assert page.locator('#use-picked-landmarks').is_enabled()
                    page.locator('#undo-landmark').click()
                    assert page.locator('#use-picked-landmarks').is_disabled()
                    pick('before',480,440)
                    pick('after',480,440)
                    draft_path=Path(tmp)/'landmark-draft.json'
                    with page.expect_download() as draft_download:
                        page.locator('#save-landmark-draft').click()
                    draft_download.value.save_as(draft_path)
                    page.locator('#clear-landmarks').click()
                    page.locator('#restore-landmark-draft').set_input_files(draft_path)
                    page.wait_for_function("() => document.querySelector('#picker-state').textContent.startsWith('Restored 6 pairs')")
                    assert not page.locator('#use-picked-landmarks').is_checked()
                    page.locator('#use-picked-landmarks').check()
                    assert page.get_by_label('Matched image landmarks').is_disabled()
                    page.locator("#title").fill("Browser upload verification")
                    page.get_by_role("button", name="Investigate uploaded pair").click()
                    page.wait_for_function("() => document.querySelector('#run-title').textContent==='Browser upload verification'")
                    assert page.locator("#fixture-badge").is_hidden()
                    assert 'supplied landmarks' in page.locator('#alignment-label').inner_text()
                    changed_before=Path(tmp)/'different-before.png'
                    changed_before.write_bytes(png(b))
                    page.locator('#before').set_input_files(changed_before)
                    assert not page.locator('#use-picked-landmarks').is_checked()
                    assert page.locator('#use-picked-landmarks').is_disabled()
                    assert page.get_by_label('Matched image landmarks').is_enabled()
                    page.wait_for_function("() => document.querySelector('#picker-state').textContent.includes('Add 6 more')")
                    page.locator('#restore-landmark-draft').set_input_files(draft_path)
                    page.get_by_text('Draft does not match these original images and processed dimensions.', exact=True).wait_for()
                    assert page.locator('#use-picked-landmarks').is_disabled()
                    page.reload()
                    page.locator("#history button").first.click()
                    page.locator("#results").wait_for(state="visible")
                    assert page.locator("#run-title").inner_text() == "Browser upload verification"
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.screenshot(path=str(out / "mobile.png"), full_page=True)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Mobile horizontal overflow"
                    page.set_viewport_size({"width": 1500, "height": 1000})
                    page.goto("http://127.0.0.1:8089")
                    scope_a=scene(); scope_b=scope_a.copy()
                    for y in range(20,620,70):
                        for x in range(20,620,70):scope_b[y:y+18,x:x+18]=[240,30,40]
                    scope_before,scope_after=Path(tmp)/'scope-before.png',Path(tmp)/'scope-after.png'
                    scope_before.write_bytes(png(scope_a));scope_after.write_bytes(png(scope_b))
                    page.locator('#toggle-upload').click()
                    page.locator('#before').set_input_files(scope_before)
                    page.locator('#after').set_input_files(scope_after)
                    with page.expect_response('**/api/analyze') as scoped:
                        page.get_by_role('button',name='Investigate uploaded pair').click()
                    scope_report=scoped.value.json()
                    page.locator('#loading').wait_for(state='hidden')
                    assert scope_report['inspection']['omitted_regions'] == 57
                    assert page.locator('#assessment-panel').get_attribute('data-state') == 'partial_inspection'
                    assert '57 omitted' in page.locator('#assessment-coverage').inner_text()
                    page.locator('#inspect-omitted').click()
                    assert page.locator('[data-view="omitted_overlay"]').get_attribute('aria-pressed') == 'true'
                    page.wait_for_function("() => {const img=document.querySelector('#base-image');return img.complete && img.naturalWidth>0;}")
                    assert page.locator('#omission-note').is_visible()
                    page.locator('[data-view="omitted_mask"]').click()
                    page.wait_for_function("() => {const img=document.querySelector('#base-image');return img.complete && img.naturalWidth>0;}")
                    assert '/omitted_mask.png' in page.locator('#base-image').get_attribute('src')
                    page.locator('#inspect-proposals').click()
                    assert page.locator('[data-view="proposal_mask"]').get_attribute('aria-pressed') == 'true'
                    with page.expect_download() as scope_packet:
                        page.locator('#packet').click()
                    scope_packet.value.save_as(out/'partial-inspection-packet.zip')
                    import io,zipfile
                    with zipfile.ZipFile(io.BytesIO((out/'partial-inspection-packet.zip').read_bytes())) as packet:
                        assert 'omitted: 57' in packet.read('SUMMARY.md').decode()
                        from geoalibi.vision import decode_image
                        omission=decode_image(packet.read('images/omitted_mask.png'))
                        assert int((omission[:,:,0]>0).sum()) == scope_report['inspection']['omitted_region_pixels']
                        assert 'images/omitted_overlay.png' in packet.namelist()
                    page.locator('#inspect-omitted').click()
                    page.wait_for_function("() => {const img=document.querySelector('#base-image');return img.complete && img.naturalWidth>0;}")
                    page.screenshot(path=str(out/'inspection-scope-desktop.png'),full_page=True)
                    page.set_viewport_size({'width':390,'height':844})
                    page.screenshot(path=str(out/'inspection-scope-mobile.png'),full_page=True)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    assert not errors, errors
                    browser.close()
                    (out / "ui-results.json").write_text(json.dumps({"status": "passed", "page_errors": errors,
                        "checks": ["fixture investigation", "image assets", "review filtering", "saved reviewer decision", "image views", "swipe", "JSON download", "three nuisance scenarios", "file upload", "visual landmark matching/keyboard/undo/submit/stale reset", "history reload", "390px mobile overflow", "partial inspection counts and packet summary", "spatial omission overlay/mask/packet agreement"]}, indent=2))
                    print("Browser checks passed: fixture, assets, filters, review, views, slider, download, nuisance scenarios, upload, history, mobile.")
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()


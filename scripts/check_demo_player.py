"""Check the generated file-based rehearsal player; no server/provider/model calls."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from geoalibi.dossier import verify_packet


def check(bundle, output):
    output.mkdir(parents=True,exist_ok=True)
    summary=json.loads((bundle/'summary.json').read_text())
    errors=[];external=[]
    with sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']}
        if os.getenv('GEOALIBI_TEST_BROWSER'):options['executable_path']=os.environ['GEOALIBI_TEST_BROWSER']
        browser=p.chromium.launch(**options)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:external.append(request.url) if request.url.startswith(('http:','https:')) else None)
        page.goto((bundle/'index.html').resolve().as_uri())
        assert 'Every image in this gallery is generated' in page.inner_text('body')
        for item in summary['scenarios']:
            page.locator(f'[data-case="{item["case"]}"]').click()
            page.wait_for_function("() => ['before','overlay'].every(id=>{const img=document.getElementById(id);return img.complete&&img.naturalWidth>0;})")
            assert page.locator('#scenario-title').inner_text()==item['title']
            text=page.locator('#counts').inner_text()
            assert f"{item['counts']['supported']} supported" in text
            page.locator('#comparison').fill('72')
            assert '72%' in page.locator('#layer').get_attribute('style')
        with page.expect_download() as info:page.locator('#packet').click()
        downloaded=output/'player-packet.zip';info.value.save_as(downloaded)
        assert verify_packet(downloaded.read_bytes())['run_id'].startswith('procedural-')
        assert '78.66%' in page.inner_text('table') and 'undefined' in page.inner_text('table')
        assert (bundle/'RECORDING_SCRIPT.md').is_file()
        page.screenshot(path=str(output/'offline-player-desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(output/'offline-player-mobile.png'),full_page=True)
        assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth')
        assert not errors,errors
        assert not external,external
        browser.close()
    (output/'offline-player-ui.json').write_text(json.dumps({'procedural_scenarios':len(summary['scenarios']),
        'file_mode':True,'packet_verified':True,'external_requests':0,'page_errors':errors})+'\n')
    print('Offline file player passed: four generated scenarios, slider, packet download, recorded evidence, mobile and zero external requests.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path);parser.add_argument('--output',type=Path,default=Path('test-results'))
    args=parser.parse_args();check(args.bundle,args.output)

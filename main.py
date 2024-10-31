import requests
import os
import time
import traceback
import json
import base64

PHASE_S = 3600*2
INTERVAL_S = 3600*6
STORE_FILE = '/mnt/electri-remain.json'

def update():
    iaaa_res = requests.post(
        'https://iaaa.pku.edu.cn/iaaa/oauthlogin.do',
        data={
            'appid': 'XYYelc_2024',
            'userName': os.environ['IAAA_USERNAME'],
            'password': base64.b64decode(os.environ['IAAA_PASSWORD'].encode()).decode(),
            'redirUrl': 'http://www.xyyelc.pku.edu.cn/auth/token_validate',
        },
    )
    iaaa_res.raise_for_status()
    iaaa_json = iaaa_res.json()
    assert iaaa_json['success'], f'iaaa result is: {iaaa_json["errors"]}'
    iaaa_token = iaaa_json['token']

    s = requests.Session()
    login_res = s.get(
        'http://www.xyyelc.pku.edu.cn/auth/token_validate',
        params={
            'token': iaaa_token,
        },
        allow_redirects=False,
    )
    assert login_res.status_code == 302, f'login result is: HTTP {login_res.status_code}: {login_res.text}'
    login_target = login_res.headers.get('Location', '')
    assert '/index' in login_target, f'login target is: {login_target}'

    remain_res = s.get(
        'http://www.xyyelc.pku.edu.cn/electricity/remain',
    )
    remain_res.raise_for_status()
    remain_txt = remain_res.text

    try:
        remain = float(
            remain_txt
                .partition('<th class="text-nowrap">余量(度)</th>')[2]
                .partition('<td>')[2]
                .partition('</td>')[0]
                .strip()
        )
    except Exception:
        raise ValueError(f'cannot parse remain: {remain_txt}')
    
    return remain

def wait_until_next_tick():
    t = time.time() - PHASE_S
    slp = INTERVAL_S - t % INTERVAL_S
    print('next update in:', int(slp))
    time.sleep(slp)

def store(remain, delta):
    print('store value: remain =', remain, 'delta =', delta)
    with open(STORE_FILE, 'w') as f:
        json.dump([remain, delta], f)

def main():
    delta = 0
    last = update()
    store(last, delta)
    while True:
        wait_until_next_tick()
        try:
            remain = update()
            if remain != last:
                delta = remain - last
                last = remain
        except Exception as e:
            print('error during update:', type(e))
            traceback.print_exc()
            remain = None
        store(remain, delta)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import time
import requests
import random
import os

COORD = os.environ.get('COORD_HOST', 'http://fl-coordinator:9000')

def main():
    while True:
        try:
            # get current round/state
            r = requests.get(COORD)
            state = r.json()
            # create a dummy update value
            value = random.random()
            print('Submitting update', value)
            requests.post(COORD, json={'value': value}, timeout=5)
        except Exception as e:
            print('error', e)
        time.sleep(5)

if __name__ == '__main__':
    main()

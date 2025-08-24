#!/usr/bin/env python3

import os
import sys
from .bundled_adb import fastboot, usb_exceptions
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import base64
import io
import argparse
import importlib.metadata

class BootloaderUnlock:
    def sign_token(self, tok, key_file):
        priv_key = RSA.importKey(open(key_file).read())
        h = SHA256.new(tok)
        signature = PKCS1_v1_5.new(priv_key).sign(h)
        return signature

    def prepare(self):
        try:
            self.dev = fastboot.FastbootCommands()
            self.dev.ConnectDevice()
        except usb_exceptions.DeviceNotFoundError as e:
            print('No device found: {}'.format(e), file=sys.stderr)
            sys.exit(1)
        except usb_exceptions.CommonUsbError as e:
            print('Could not connect to device: {}'.format(e), file=sys.stderr)
            sys.exit(1)

    def __call__(self):
        print('Attempting to unlock bootloader...')
        self.prepare()
        
        try:
            self.dev._SimpleCommand(b'flashing unlock', timeout_ms=60*1000)
            print('Bootloader unlocked successfully!')
        except Exception as e:
            print(f'Error during unlock: {str(e)}')
            try:
                self.dev.Oem('unlock', timeout_ms=60*1000)
                print('Bootloader unlocked via OEM command!')
            except Exception as oem_error:
                print(f'OEM unlock failed: {str(oem_error)}')
                sys.exit(1)
        
        self.dev.Close()

def main():
    parser = argparse.ArgumentParser(
        description='Unlock tool for Spreadtrum/Unisoc bootloader'
    )
    parser.add_argument('--force', '-f', 
                        action='store_true',
                        help='Force unlock without OEM check'
                        )
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' +
                        importlib.metadata.version('unisoc-unlock')
                        )

    args = parser.parse_args()

    if args.force:
        print('Using forced unlock method...')
        cmd = BootloaderUnlock()
        cmd()
    else:
        print('Please use --force flag for unlock attempt')
        sys.exit(1)

if __name__ == '__main__':
    main()

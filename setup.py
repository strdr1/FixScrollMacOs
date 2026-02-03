from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['rumps'],
    'includes': ['Cocoa', 'Quartz', 'AppKit', 'ApplicationServices', 'Foundation'],
    'plist': {
        'LSUIElement': True,  # Hides the app from the Dock (menu bar only)
        'CFBundleName': 'RDP Scroll Fixer',
        'CFBundleDisplayName': 'RDP Scroll Fixer',
        'CFBundleIdentifier': 'com.fixscroll.rdp',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

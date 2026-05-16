[app]
title = ThaiClub AutoBet
package.name = thaiclubAutobet
package.domain = org.thaiclub
source.dir = src
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.2
requirements = python3,kivy==2.3.0,openssl

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 26
android.sdk = 33
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1

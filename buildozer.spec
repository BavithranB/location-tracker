[app]
# App name and package domain
title = Location Tracker
package.name = locationtracker
package.domain = org.example

# Source code location
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Application versioning
version = 0.1
requirements = python3,kivy==2.2.1,plyer==2.1.0,geocoder==1.38.1,requests==2.31.0

# Android specific settings
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_BACKGROUND_LOCATION,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.targetapi = 33

# Orientation
orientation = portrait

# Application features
android.features = FOREGROUND_SERVICE

# Services - since you're tracking location
android.services = 

# Allow using non-commercial python-for-android (fix for some buildozer issues)
p4a.fork = kivy

# Icons and presplash
#icon.filename = %(source.dir)s/data/icon.png
#presplash.filename = %(source.dir)s/data/presplash.png

# Control if the APK should contain the source code
source.include_exts = py,png,jpg,kv,atlas,txt
source.exclude_dirs = tests, bin, venv, .git

# Application dependencies
requirements.source.kivy = ../../kivy

# Allow permission handling at runtime
android.allow_backup = True

# Remove the main bootstrap since we're using P4A
bootstrap = sdl2

# This is required to handle packages with C components properly
android.archs = arm64-v8a, armeabi-v7a
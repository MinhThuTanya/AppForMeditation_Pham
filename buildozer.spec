[app]
# Сборка APK для Android (в WSL / Ubuntu): buildozer android debug
title = Akii
package.name = akii
package.domain = ru.akii
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttf,otf,mp3,txt
source.exclude_dirs = tests, server, tools, data, bin, .buildozer, venv, .venv, akii-ios
version = 1.0
requirements = python3,kivy==2.3.1,kivymd==2.0.0,materialyoucolor,materialshapes,pycairo,asynckivy,asyncgui,exceptiongroup,pillow,plyer,pyjnius,android
icon.filename = assets/icons/icon_512.png
presplash.filename = assets/icons/icon_512.png
presplash.color = #E6EEF9
orientation = portrait
fullscreen = 0

# Android 10 и новее (требование ТЗ)
android.minapi = 29
android.api = 34
android.archs = arm64-v8a, armeabi-v7a
android.permissions = INTERNET, RECORD_AUDIO, POST_NOTIFICATIONS
android.allow_backup = False

# Этап 9.3: зависимость RuStore Pay SDK (версию взять из документации RuStore)
# android.gradle_dependencies = ru.rustore.sdk:pay:<версия>
# Этап 9.4: VK ID SDK для входа через VK ID
# android.gradle_dependencies = com.vk.id:vkid:<версия>

[buildozer]
log_level = 2
warn_on_root = 1

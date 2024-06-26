@echo off

cd /d "%~dp0"

rmdir /s /q .depend
for /d %%d in (.instdist-*) do rmdir /s /q "%%~d"
rmdir /s /q .sconf_temp
rmdir /s /q .test
rmdir /s /q __pycache__
rmdir /s /q build
for /d %%d in (build-local*) do rmdir /s /q "%%~d"

del /q .sconsign.dblite
del /q config.log

REM pause
@echo off

setlocal
set base=%~dp0

call %base%\test

set error=%ERRORLEVEL%

if not %error% == 0 (
    exit /b %error%
)

call %base%\run_its

exit /b %ERRORLEVEL%
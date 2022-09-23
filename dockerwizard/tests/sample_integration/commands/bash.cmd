@echo off

call python %~dp0\bash %*

exit /b %ERRORLEVEL%

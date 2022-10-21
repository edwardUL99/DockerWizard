@echo off

call python %~dp0\npm %*

exit /b %ERRORLEVEL%

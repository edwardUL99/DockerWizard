@echo off

call python %~dp0\docker %*

exit /b %ERRORLEVEL%

@echo off

call python %~dp0\ls %*

exit /b %ERRORLEVEL%

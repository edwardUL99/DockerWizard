@echo off

call python %~dp0\itutils %*

exit /b %ERRORLEVEL%
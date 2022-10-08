@echo off

call python %~dp0\mvn %*

exit /b %ERRORLEVEL%

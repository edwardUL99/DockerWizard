@echo off

set directory=%cd%
cd /d %~dp0

call integration/itutils run "*_integration" -g

set error_level=%ERRORLEVEL%

cd %directory%

exit /b %error_level%
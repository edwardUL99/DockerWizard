@echo off

set directory=%cd%
cd /d %~dp0

call integration/itutils "*_integration" -g

cd %directory%
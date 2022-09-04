@echo off

setlocal
set ARGS=%*

set DOCKER_WIZARD_CMD_NAME=docker-wizard

if "%DOCKER_WIZARD_HOME%" == "" GOTO EMPTY_WIZARD_HOME
if not exist "%DOCKER_WIZARD_HOME%" GOTO NOT_FOUND_HOME

set SCRIPT=%DOCKER_WIZARD_HOME%\main.py

for %%s in ("main.py" "bin" "dockerwizard") do (
	if not exist "%DOCKER_WIZARD_HOME%\%s%" GOTO MALFORMED_WIZARD_HOME
)

python "%SCRIPT%" %ARGS%

exit /b %ERRORLEVEL%

:MALFORMED_WIZARD_HOME
call :Error "Malformed DOCKER_WIZARD_HOME %DOCKER_WIZARD_HOME%. Make sure it points to the root of the project"
exit /b 3
:END 

:EMPTY_WIZARD_HOME
call :Error "To run docker-wizard you need to set DOCKER_WIZARD_HOME to the root of the installed project"
exit /b 1
:END

:NOT_FOUND_HOME
call :Error "DOCKER_WIZARD_HOME %DOCKER_WIZARD_HOME% is not a directory"
exit /b 2
:END


:Error
echo [[31mERROR[0m] %~1
exit /b 0
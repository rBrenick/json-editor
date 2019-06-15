@ECHO OFF
:BEGIN
CLS

ECHO Welcome to json_editor
ECHO Here are the options
ECHO.


ECHO    1 = Install
ECHO    2 = Uninstall
ECHO    3 = Get Latest version of tool
ECHO.
ECHO Advanced:
ECHO    4 = Make New Tool from json_editor

ECHO.
SET /P AREYOUSURE=Choice: 
IF /I "%AREYOUSURE%" EQU "1" GOTO :Install
IF /I "%AREYOUSURE%" EQU "2" GOTO :Uninstall
IF /I "%AREYOUSURE%" EQU "3" GOTO :GetLatest
IF /I "%AREYOUSURE%" EQU "4" GOTO :MakeNewTool

:Install
CALL _install_\install_maya_module.bat
GOTO END

:Uninstall
CALL _install_\uninstall_maya_module.bat
GOTO END

:GetLatest
Powershell.exe -executionpolicy remotesigned -File  _install_\get_latest_version.ps1
GOTO END


:MakeNewTool
Powershell.exe -executionpolicy remotesigned -File  _install_\create_new_tool.ps1


:END
PAUSE



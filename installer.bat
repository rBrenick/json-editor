@ECHO OFF
:BEGIN
CLS

ECHO Welcome to json-editor
ECHO Here are the options
ECHO.


ECHO    1 = Install to Maya
ECHO    2 = Install Standalone
ECHO    3 = Uninstall from Maya
ECHO    4 = Get latest version of tool
ECHO.
ECHO Advanced:
ECHO    5 = Make new tool from template

ECHO.
SET /P AREYOUSURE=Choice: 
IF /I "%AREYOUSURE%" EQU "1" GOTO :Install
IF /I "%AREYOUSURE%" EQU "2" GOTO :InstallStandalone
IF /I "%AREYOUSURE%" EQU "3" GOTO :Uninstall
IF /I "%AREYOUSURE%" EQU "4" GOTO :GetLatest
IF /I "%AREYOUSURE%" EQU "5" GOTO :MakeNewTool

:Install
CALL _setup_\maya\install_maya_module.bat
GOTO END

:Uninstall
CALL _setup_\maya\uninstall_maya_module.bat
GOTO END

:InstallStandalone
CALL _setup_\standalone\create_standalone_venv.bat
GOTO END

:GetLatest
Powershell.exe -executionpolicy remotesigned -File  _setup_\get_latest_version.ps1
GOTO END


:MakeNewTool
Powershell.exe -executionpolicy remotesigned -File  _setup_\create_new_tool.ps1


:END
PAUSE




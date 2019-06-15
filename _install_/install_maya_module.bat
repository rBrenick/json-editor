
:: json_editor is determined by the current folder name
for %%I in (.) do set json_editor=%%~nxI
SET CLEAN_json_editor=%json_editor:-=_%

:: Check if modules folder exists
if not exist %UserProfile%\Documents\maya\modules mkdir %UserProfile%\Documents\maya\modules

:: Delete .mod file if it already exists
if exist %UserProfile%\Documents\maya\modules\%json_editor%.mod del %UserProfile%\Documents\maya\modules\%json_editor%.mod

:: Create file with contents in users maya/modules folder
(echo|set /p=+ %json_editor% 1.0 %CD%\_install_ & echo; & echo icons: ..\%CLEAN_json_editor%\icons)>%UserProfile%\Documents\maya\modules\%json_editor%.mod

:: end print
echo .mod file created at %UserProfile%\Documents\maya\modules\%json_editor%.mod



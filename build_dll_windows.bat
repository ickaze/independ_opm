@echo off
setlocal
cd /d "%~dp0"
set "IOPM_VCVARS="
rem Explicit argument: installation root, VC directory, or vcvarsall.bat.
if not "%~1"=="" (
 call :select "%~1"
 if not defined IOPM_VCVARS goto :notfound
 goto :found
)
rem User override and Visual Studio Developer Command Prompt environment.
if defined IOPM_VS call :select "%IOPM_VS%"
if defined VSINSTALLDIR call :select "%VSINSTALLDIR%"
if defined VCINSTALLDIR call :select "%VCINSTALLDIR%"
if defined VCToolsInstallDir call :select "%VCToolsInstallDir%..\..\.."
if defined IOPM_VCVARS goto :found
rem Probe actual layouts under both 64-bit and 32-bit Program Files.
for %%R in ("%ProgramW6432%" "%ProgramFiles%" "%ProgramFiles(x86)%") do (
 for %%E in (Community Professional Enterprise BuildTools Preview) do (
  call :select "%%~R\Microsoft Visual Studio\2022\%%E"
 )
)
if defined IOPM_VCVARS goto :found
rem vswhere is optional: try PATH and both Installer locations.
for /f "delims=" %%I in ('where vswhere.exe 2^>nul') do call :query "%%I"
for %%R in ("%ProgramW6432%" "%ProgramFiles%" "%ProgramFiles(x86)%") do call :query "%%~R\Microsoft Visual Studio\Installer\vswhere.exe"
if not defined IOPM_VCVARS goto :notfound
:found
echo Using "%IOPM_VCVARS%"
call :build x86 Win32
if errorlevel 1 exit /b 1
call :build x64 x64
if errorlevel 1 exit /b 1
echo Built and tested bin\Win32 and bin\x64.
exit /b 0
:notfound
echo Could not locate VC\Auxiliary\Build\vcvarsall.bat.
echo vswhere.exe is NOT required.
echo Run this script from a VS2022 Developer Command Prompt, or specify the installation:
echo   build_dll_windows.bat "D:\Apps\Visual Studio\2022\Community"
echo Alternatively pass the full path to vcvarsall.bat.
echo Install the Desktop development with C++ workload, MSVC x86/x64 tools and Windows SDK if missing.
exit /b 1
:select
if defined IOPM_VCVARS exit /b 0
if "%~1"=="" exit /b 0
if /i "%~nx1"=="vcvarsall.bat" if exist "%~1" set "IOPM_VCVARS=%~f1"
if defined IOPM_VCVARS exit /b 0
if exist "%~1\VC\Auxiliary\Build\vcvarsall.bat" set "IOPM_VCVARS=%~f1\VC\Auxiliary\Build\vcvarsall.bat"
if defined IOPM_VCVARS exit /b 0
if exist "%~1\Auxiliary\Build\vcvarsall.bat" set "IOPM_VCVARS=%~f1\Auxiliary\Build\vcvarsall.bat"
exit /b 0
:query
if defined IOPM_VCVARS exit /b 0
if not exist "%~1" exit /b 0
for /f "usebackq delims=" %%I in (`"%~1" -latest -version "[17.0,18.0)" -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do call :select "%%I"
exit /b 0
:build
setlocal
call "%IOPM_VCVARS%" %1
if errorlevel 1 exit /b 1
if not exist bin\%2 mkdir bin\%2
if not exist build-dll\%2 mkdir build-dll\%2
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT /LD /DIOPM_BUILD_DLL /Iinclude /Fobuild-dll\%2\ src\ym2151.cpp src\dll_api.cpp /link /DEF:dll\independent_opm.def /OUT:bin\%2\independent_opm.dll /IMPLIB:bin\%2\independent_opm_import.lib
if errorlevel 1 exit /b 1
cl /nologo /O2 /W4 /MT /Iinclude /Fobuild-dll\%2\test_c_api.obj tests\test_c_api.c /Fe:bin\%2\opm_c_api_test.exe /link bin\%2\independent_opm_import.lib
if errorlevel 1 exit /b 1
bin\%2\opm_c_api_test.exe
if errorlevel 1 exit /b 1
cl /nologo /O2 /W4 /MT /Iinclude /Fobuild-dll\%2\dll_client.obj examples\dll_client.c /Fe:bin\%2\opm_dll_example.exe /link bin\%2\independent_opm_import.lib
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT /Iinclude /Fobuild-dll\%2\ src\ym2151.cpp tests\test_dll_equivalence.cpp /Fe:bin\%2\opm_dll_equivalence.exe /link bin\%2\independent_opm_import.lib
if errorlevel 1 exit /b 1
bin\%2\opm_dll_equivalence.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT /Iinclude /Fobuild-dll\%2\ src\ym2151.cpp tests\test_state.cpp /Fe:bin\%2\opm_state_tests.exe /link bin\%2\independent_opm_import.lib
if errorlevel 1 exit /b 1
bin\%2\opm_state_tests.exe
if errorlevel 1 exit /b 1
endlocal
exit /b 0

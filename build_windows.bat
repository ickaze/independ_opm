@echo off
setlocal
cd /d "%~dp0"
where cl >nul 2>nul
if errorlevel 1 (
 echo Run from the Visual Studio 2022 x64 Native Tools Command Prompt.
 exit /b 1
)
if not exist bin mkdir bin
cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp src\main.cpp /Fe:bin\opm_render.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_core.cpp /Fe:bin\opm_tests.exe
if errorlevel 1 exit /b 1
bin\opm_tests.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_precision.cpp /Fe:bin\opm_precision_tests.exe
if errorlevel 1 exit /b 1
bin\opm_precision_tests.exe
if errorlevel 1 exit /b 1
bin\opm_render.exe --demo demo.wav

cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_output_timing.cpp /Fe:bin\opm_output_timing_tests.exe
if errorlevel 1 exit /b 1
bin\opm_output_timing_tests.exe
if errorlevel 1 exit /b 1

cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_random.cpp /Fe:bin\opm_random_tests.exe
if errorlevel 1 exit /b 1
bin\opm_random_tests.exe
if errorlevel 1 exit /b 1

cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_sequence.cpp /Fe:bin\opm_sequence_tests.exe
if errorlevel 1 exit /b 1
bin\opm_sequence_tests.exe
if errorlevel 1 exit /b 1

cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_periodic.cpp /Fe:bin\opm_periodic_tests.exe
if errorlevel 1 exit /b 1
bin\opm_periodic_tests.exe
if errorlevel 1 exit /b 1

cl /nologo /std:c++17 /EHsc /O2 /W4 /Iinclude src\ym2151.cpp tests\test_key_on.cpp /Fe:bin\opm_key_on_tests.exe
if errorlevel 1 exit /b 1
bin\opm_key_on_tests.exe
if errorlevel 1 exit /b 1

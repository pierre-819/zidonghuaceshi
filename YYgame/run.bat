@echo off
chcp 65001 >nul
cd /d %~dp0
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8


echo ============================================
echo   YYgame Web 自动化   有头模式 + 生成报告
echo ============================================
echo.

if "%~1"=="" (
    echo 运行范围: 全部用例
    python -m pytest -v --html=report/report.html --self-contained-html
) else (
    echo 运行范围: %*
    python -m pytest %* -v --html=report/report.html --self-contained-html
)

echo.
echo ============================================
echo   报告: %~dp0report\report.html
echo   日志: %~dp0report\run.log
echo ============================================
pause

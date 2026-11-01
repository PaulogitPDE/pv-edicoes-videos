@echo off
cd /d "%~dp0"
title PV Achadinhos - WhatsApp
:loop
rem pega a versao nova do programa antes de cada inicio (o comando "atualizar" da nuvem reinicia aqui)
git pull --rebase --autostash origin main
node enviador.js
timeout /t 5 >nul
goto loop

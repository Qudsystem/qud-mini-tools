@echo off
setlocal
cd /d "%~dp0.."
git init
git add .
git commit -m "feat: Dragon S1 v0.1.0 prototype"
git branch -M main
echo Repository initialized. Add your remote and push when ready.

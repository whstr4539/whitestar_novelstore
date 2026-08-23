# 彻底停止并重启 Docker Desktop，使 daemon.json 镜像配置生效
Get-Process | Where-Object { $_.Name -like '*Docker*' -or $_.Name -like '*com.docker*' } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 8
Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
Write-Host 'Docker Desktop restart triggered'

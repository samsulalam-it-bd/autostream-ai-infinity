@echo off
echo Running Docker execute...
FOR /F "tokens=*" %%i IN ('docker ps --filter "name=frontend" -q') DO set CONTAINER_ID=%%i
if "%CONTAINER_ID%"=="" (
    echo No frontend container found.
    exit /b 1
)

echo Container is %CONTAINER_ID%
docker exec %CONTAINER_ID% npm install react-rnd date-fns lodash.debounce lucide-react@latest > docker_install_out.txt 2>&1
echo Done running install. >> docker_install_out.txt
docker restart %CONTAINER_ID%
echo Restarted container. >> docker_install_out.txt

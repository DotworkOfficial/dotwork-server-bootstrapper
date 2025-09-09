@echo off
title {{ server_name }}
echo Starting {{ server_name }}...
echo Port: {{ server_port }}
echo Max Players: {{ max_players }}
echo.

java -Xms2G -Xmx2G -jar server.jar nogui

pause
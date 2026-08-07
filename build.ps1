pyinstaller Boxhead.spec --noconfirm
pyinstaller Boxhead_Launcher.spec --noconfirm

Copy-Item -Path "dist\Boxhead.exe" -Destination ".\Boxhead.exe" -Force
Copy-Item -Path "dist\Boxhead_Launcher.exe" -Destination ".\Boxhead_Launcher.exe" -Force

Remove-Item Boxhead_Release.zip -ErrorAction SilentlyContinue
Compress-Archive -Path Boxhead.exe, Boxhead_Launcher.exe, assets, entities, logic, scenes, sounds, version.txt, *.py -DestinationPath Boxhead_Release.zip -Force

Write-Host "Build and packaging complete! Boxhead_Release.zip is ready."

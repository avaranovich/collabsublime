update-agent:
	cd ../cccp & git pull

update-plugin:
	git pull
	cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/ && mkdir -p Collaboration
	cp "Default (Linux).sublime-keymap" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/
	cp "Default (Windows).sublime-keymap" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/
	cp AgentClient.py ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/      
	cp JsonComposer.py ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/ 
	cp cccpClient.py ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/           
	cp "Default (OSX).sublime-keymap" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/ 
	cp "Collaboration.sublime-settings" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/
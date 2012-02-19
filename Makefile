update-agent:
	cd ../cccp & git pull

update-plugin:
	git pull
	cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/ && mkdir -p Collaboration
	cp "Default (Linux).sublime-keymap" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/
	cp "Default (Windows).sublime-keymap" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/
	cp *.py ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/                    
	cp "Default (OSX).sublime-keymap" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/ 
	cp "Main.sublime-menu" ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Collaboration/
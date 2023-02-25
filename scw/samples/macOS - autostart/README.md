# Auto-start on macOS

1. Create a virtual environment and install the config watcher. Let's assume you want to install it inside the `~/scw/` 
   directory.
```shell
mkdir -p ~/scw
cd ~/scw
virtualenv venv 
source venv/bin/activate
pip3 install -U screen-config-watcher
```

2. Prepare the `config.toml` and `ocsw-config.toml` configuration files, and put them in the `~/scw` directory.

3. Tweak contents of the `de.yobasoft.screen-config-watcher.plist`: make sure that the paths are pointing to the right
   directories.

1. Copy the `de.yobasoft.screen-config-watcher.plist` file into the user-specific service directory:
```shell
cp ./de.yobasoft.screen-config-watcher.plist ~/Library/LaunchAgents/
```

2. Load the service:
```shell
launchctl load ~/Library/LaunchAgents/de.yobasoft.screen-config-watcher.plist
```

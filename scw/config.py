from typing import List, Callable, Union

import os
import toml

from scw.log import Log


class Config:
    class Preset:
        def __init__(self, name: str, displays: List[str], profile_name: str, scene_collection_name: str):
            self.name = name
            self.displays = displays
            self.profile_name = profile_name
            self.scene_collection_name = scene_collection_name

        def __str__(self):
            return f"name='{self.name}', displays={self.displays}, profile_name='{self.profile_name}', " \
                   f"scene_collection_name='{self.scene_collection_name}'"

        def __repr__(self):
            return f"Config.Preset(name='{self.name}', displays={self.displays}, profile_name='{self.profile_name}', " \
                   f"scene_collection_name='{self.scene_collection_name}')"

        @staticmethod
        def from_dict(d: dict) -> List['Config.Preset']:
            result = []  # type: List[Config.Preset]

            for key in d:
                preset = Config.Preset(key, d[key]['displays'], d[key]['profile'], d[key]['scene_collection'])
                result.append(preset)

            return result

        def _as_tuple(self) -> tuple:
            return self.name, self.profile_name, self.scene_collection_name, self.displays

        def __eq__(self, other: 'Config.Preset'):
            return self._as_tuple() == other._as_tuple()

        def compare_case_insensitive(self, other: Union['Config.Preset', List[str]], verbose: bool):
            if isinstance(other, Config.Preset):
                displays = other.displays
            elif isinstance(other, list):
                displays = other
            else:
                raise RuntimeError(f'Unexpected other type: {type(other)}')

            if len(self.displays) != len(displays):
                if verbose:
                    Log.debug(f'{self.name} mismatch: number of displays')

                return False

            our_lower = [x.lower() for x in self.displays]
            other_lower = [x.lower() for x in displays]

            mismatch = None
            for display in other_lower:
                if display not in our_lower:
                    mismatch = display
                    break

            if mismatch is not None:
                if verbose:
                    original = displays[other_lower.index(mismatch)]
                    Log.debug(f'{self.name} mismatch: "{original}" not found in preset')
                return False

            return True

    def __init__(self, config_path: str, obwsc_config: str, grace_period: int, presets: List['Config.Preset']):
        self.config_path = config_path
        self.obwsc_config = obwsc_config
        self.grace_period = grace_period
        self.presets = presets
        self.on_change_listeners = []  # type: List[Callable[[Config], None]]

    def find_matching_preset(self, displays: List[str]) -> List['Config.Preset']:
        Log.debug(f'Matching presets against {displays}')

        matches = []

        for preset in self.presets:
            if preset.compare_case_insensitive(displays, True):
                matches.append(preset)

        return matches

    def validate(self) -> bool:
        if not os.path.exists(self.obwsc_config) and os.path.isfile(self.obwsc_config):
            Log.error(f'OBS Websocket Commands Config not found: {self.obwsc_config}')
            return False

        # Make sure that presets are unique enough
        unique_enough = True
        for i in range(len(self.presets)):
            first = self.presets[i]
            for j in range(i + 1, len(self.presets)):
                second = self.presets[j]
                if first.compare_case_insensitive(second, False):
                    Log.error(f'These presets are not unique enough: "{first.name}" and "{second.name}"')
                    unique_enough = False

        return unique_enough

    def subscribe_to_changes(self, listener: Callable[['Config'], None]):
        self.on_change_listeners.append(listener)

    def unsubscribe_from_changes(self, listener: Callable[['Config'], None]):
        try:
            self.on_change_listeners.remove(listener)
        except ValueError as e:
            print(f'Error unsubscribing from config changes: {e}')

    def _as_tuple(self):
        return self.obwsc_config, self.grace_period, self.presets

    def __eq__(self, other: 'Config'):
        return self._as_tuple() == other._as_tuple()

    @staticmethod
    def contents_from_file(file_path):
        file_contents = toml.load(file_path)
        obwsc_config = file_contents['obwsc']['config']
        grace_period = file_contents['settings']['grace_period']
        presets = Config.Preset.from_dict(file_contents['presets'])
        return obwsc_config, grace_period, presets

    @staticmethod
    def load_from_file(file_path) -> 'Config':
        try:
            obwsc_config, grace_period, presets = Config.contents_from_file(file_path)
            res = Config(file_path, obwsc_config, grace_period, presets)
            if not res.validate():
                raise RuntimeError(f'Invalid configuration: {file_path}')
            return res
        except toml.decoder.TomlDecodeError as e:
            raise RuntimeError(str(e))

    def reload(self):
        try:
            new_config = Config.load_from_file(self.config_path)
        except toml.decoder.TomlDecodeError as e:
            Log.error(e)
            return
        except RuntimeError as e:
            Log.error(e)
            return

        changed = (self != new_config)

        if not changed:
            return

        Log.debug(f'Configuration file changed {self.config_path}')

        self.obwsc_config = new_config.obwsc_config
        self.grace_period = new_config.grace_period
        self.presets = new_config.presets

        for listener in self.on_change_listeners:
            listener(self)

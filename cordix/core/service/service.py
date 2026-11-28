from os import PathLike
from pathlib import Path
from uuid import UUID, uuid8

from core import TOMLConfiguration
from core.module import Module
from core.service import ServiceManager
from core.utils import Registry

from cordix.core.plugin import Plugin


class Service:
    def __init__(self, name: str, uuid: UUID, root_dir: Path):

        self._name: str = name
        self._uuid: UUID = uuid

        self._plugins: Registry[Plugin] = Registry(
            index_attributes=["name"], force_key_types=True, key_types=[str]
        )
        self._modules: dict[str, Module] = {}

        # Directories
        self._root_dir: Path = root_dir
        self._config_directory: Path = root_dir / "configs"
        self._plugin_directory: Path = root_dir / "plugins"

        # Configs
        self._main_config: TOMLConfiguration = TOMLConfiguration(
            self._config_directory / "service.toml"
        )
        self._plugin_config: TOMLConfiguration = TOMLConfiguration(
            self._config_directory / "plugin.toml"
        )

    def generate_directories(self) -> None:
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._config_directory.mkdir(parents=True, exist_ok=True)
        self._plugin_directory.mkdir(parents=True, exist_ok=True)

    def save_config(self) -> None:
        if not self._main_config.exists():
            self._main_config.create()

        self._main_config["general.uuid"] = str(self._uuid)
        self._main_config["general.name"] = self._name

    ################## GETTERS ###################

    @property
    def name(self) -> str:
        return self._name

    @property
    def uuid(self) -> UUID:
        return self._uuid

    @property
    def root_directory(self) -> Path:
        return self._root_dir

    @property
    def config_directory(self) -> Path:
        return self._config_directory

    @property
    def plugin_directory(self) -> Path:
        return self._plugin_directory

    @property
    def modules(self) -> dict[str, Module]:
        return self._modules

    @property
    def plugins(self) -> Registry[Plugin]:
        return self._plugins

    @property
    def main_config(self) -> TOMLConfiguration:
        return self._main_config

    @property
    def plugin_config(self) -> TOMLConfiguration:
        return self._plugin_config

    ################## SETTERS ###################

    ################ CLASSMETHODS ################

    @classmethod
    def new(
        cls, service_manager: ServiceManager, name: str, root_dir: PathLike[str]
    ) -> "Service":

        instance = cls(name=name, uuid=uuid8(), root_dir=Path(root_dir))

        instance.generate_directories()
        instance.save_config()
        return instance

    @classmethod
    def from_config(cls, config_path: PathLike[str]) -> "Service":
        config_path = Path(config_path)
        config = TOMLConfiguration(config_path, create_if_not_exists=False)

        if not config.exists():
            raise FileNotFoundError(f"Config file {config_path} does not exist.")

        instance = cls(
            name=config["name"],
            uuid=config["uuid"],
            root_dir=config_path.parent,
        )

        return instance

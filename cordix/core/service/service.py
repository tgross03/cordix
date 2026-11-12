import uuid
from os import PathLike
from pathlib import Path

from cordix.core.bot.manager import BotManager
from cordix.core.config import TOMLConfiguration
from cordix.core.exceptions.services import InvalidServiceError, ServiceExistsError
from cordix.core.module.manager import ModuleManager
from cordix.core.plugin.manager import PluginManager
from cordix.core.service.register import ServiceRegister


class Service:
    def __init__(
        self,
        name: str,
        parent_dir: PathLike | str,
    ) -> None:
        self._name: str = name
        self._root_dir: Path = Path(parent_dir) / self._name
        self._uuid: uuid.UUID | None = None

        self._main_config: TOMLConfiguration = TOMLConfiguration(
            self._root_dir / "cordix.toml"
        )

        if "uuid" in self._main_config:
            self._uuid = uuid.UUID(str(self._main_config["uuid"]))

        self._bot_config: TOMLConfiguration = TOMLConfiguration(
            self._root_dir / "bots.toml"
        )
        self._module_config: TOMLConfiguration = TOMLConfiguration(
            self._root_dir / "modules.toml"
        )
        self._plugin_config: TOMLConfiguration = TOMLConfiguration(
            self._root_dir / "plugins.toml"
        )

        self._bot_manager: BotManager = BotManager(bot_config=self._bot_config)
        self._module_manager: ModuleManager = ModuleManager(
            module_config=self._module_config
        )
        self._plugin_manager: PluginManager = PluginManager(
            plugin_config=self._plugin_config
        )

    def reset_config(self) -> None:
        self._main_config.dump({"uuid": str(self._uuid)})

    def exists(self) -> bool:
        return self._root_dir.exists() and self._root_dir.is_dir()

    def is_valid(self) -> bool:
        return (
            self.exists()
            and self._main_config.exists()
            and self._bot_config.exists()
            and self._module_config.exists()
            and self._plugin_config.exists()
            and (self._root_dir / "plugins").exists()
            and (self._root_dir / "config").exists()
            and (self._root_dir / "config/modules").exists()
            and (self._root_dir / "config/plugins").exists()
        )

    def initialize(self, verbose: int = 1) -> None:

        try:
            ServiceRegister().get_service_by_name(name=self._name)
            raise ServiceExistsError(
                f"There already exists a service with name '{self._name}'!"
            )
        except InvalidServiceError:
            pass

        if verbose >= 2:
            print("Service not already initialized.")

        self._uuid = uuid.uuid4()

        if verbose >= 3:
            print(f"Assigned UUID {self._uuid}.")

        self._root_dir.mkdir()
        (self._root_dir / "plugins").mkdir()
        (self._root_dir / "config").mkdir()

        (self._root_dir / "config/modules").mkdir()
        (self._root_dir / "config/plugins").mkdir()

        if verbose >= 2:
            print(f"Created main directory {self._root_dir} and subdirectories.")

        self._main_config.create()

        self._bot_config.create()
        self._module_config.create()
        self._plugin_config.create()

        self.reset_config()

        self._bot_manager.reset_config()
        self._module_manager.reset_config()
        self._plugin_manager.reset_config()

        if verbose >= 2:
            print("Created default configs.")

        ServiceRegister().register(self)

        if verbose >= 1:
            print(f"Registered service '{self._name}' (UUID: {self._uuid}).")

    # CLASS METHODS

    @classmethod
    def from_path(cls, path: PathLike | str) -> "Service":
        path = Path(path)
        instance = cls(name=path.name, parent_dir=path.parent)

        if not instance.is_valid():
            raise InvalidServiceError(f"There is no valid service at path {path}!")

        return instance

    @classmethod
    def from_name(cls, name: str) -> "Service":
        return ServiceRegister().get_service_by_name(name=name)

    @classmethod
    def from_uuid(cls, unique_id: uuid.UUID | str) -> "Service":
        return ServiceRegister().get_service_by_uuid(unique_id=unique_id)

    # GETTERS

    def get_name(self) -> str:
        return self._name

    def get_root_dir(self) -> PathLike | None:
        return self._root_dir

    def get_uuid(self) -> uuid.UUID | None:
        return self._uuid

    def get_main_config(self) -> TOMLConfiguration:
        return self._main_config

    def get_bot_config(self) -> TOMLConfiguration:
        return self._bot_config

    def get_module_config(self) -> TOMLConfiguration:
        return self._module_config

    def get_plugin_config(self) -> TOMLConfiguration:
        return self._plugin_config

    def get_bot_manager(self) -> BotManager:
        return self._bot_manager

    def get_module_manager(self) -> ModuleManager:
        return self._module_manager

    def get_plugin_manager(self) -> PluginManager:
        return self._plugin_manager

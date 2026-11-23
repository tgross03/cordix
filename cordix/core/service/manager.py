import uuid

from .. import TOMLConfiguration
from ..config import GLOBAL_CONFIG_DIR
from ..utils import Registry
from .service import Service


class ServiceManager:

    def __init__(self):
        self._service_registry: Registry[Service] = Registry[Service](
            index_attributes=["name", "uuid"],
            force_key_types=True,
            key_type=[str, uuid.UUID],
        )
        self._registry_config: TOMLConfiguration = TOMLConfiguration(
            GLOBAL_CONFIG_DIR / "services.toml", create_if_not_exists=True
        )

    def load_services(self, ignore_missing: bool = False) -> None:
        for key, val in self._registry_config:
            try:
                self._service_registry.register(Service.from_config(config_path=val))
            except FileNotFoundError as e:
                if ignore_missing:
                    continue
                else:
                    raise e

    ################## GETTERS ###################

    @property
    def service_registry(self) -> Registry[Service]:
        return self._service_registry

    ################## SETTERS ###################

    ################ CLASSMETHODS ################

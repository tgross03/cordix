from typing import Any

from rich.tree import Tree


class Registry:
    """
    A ``Registry`` contains objects registered by an attribute of the object.
    Each registry can only store one type of object, meaning all objects saved
    in the registry must have the same type.

    The registry is given a list of attributes it uses to index the saved objects.
    This assumes that the given attributes are all (!) unique and constant for each object.
    Therefore, no index may be registered twice, even if it is registered under different
    attributes.

    **Example:**

    Given the following exemplary class, we can create a registry indexing the
    saved instances of the example class by their attributes ``attr1`` and ``attr2``.

    .. code-block:: python

        class Example:
            def __init__(self, attr1, attr2, attr3):
                self.attr1 = attr1
                self.attr2 = attr2
                self.attr3 = attr3

            def __repr__(self):
                return f"Example(attr1={self.attr1}, attr2={self.attr2}, attr3={self.attr3})"


        obj1 = Example(attr1=1, attr2=2, attr3=3)
        obj2 = Example(attr1=4, attr2=5, attr3=6)

        registry = Registry[Example](["attr1", "attr2"])
        registry.register(obj1)
        registry.register(obj2)
        print(registry.items())


    This will output something like

    .. code-block::

        [((1, 2), Example(attr1=1, attr2=2, attr3=3)), ((4, 5), Example(attr1=4, attr2=5, attr3=6))]

    In this example, the attributes ``attr1`` and ``attr2`` are used as indexing attributes.
    Therefore, no object may be registered with an ``attr1`` or ``attr2`` with values
    already registered in the registry.

    For example, registering an object with ``attr1=1`` will of course raise a ``ValueError`` since
    an object with ``attr1=1`` is already registered.
    But, equally, registering an object with ``attr2=1`` will also raise a ``ValueError`` since the
    integer ``1`` is already used as an index. The indices are therefore registered independently
    of the attributes they come from.

    """

    registry_type: type

    def __init__(
        self,
        index_attributes: list[str],
        force_key_types: bool = False,
        key_types: list[type] | None = None,
    ):
        self._joined_registry: dict[Any, Any] = {}
        self._registries: dict[str, dict[Any, Any]] = {attr: {} for attr in index_attributes}
        self._force_key_types: bool = force_key_types
        self._index_attributes: list[str] = index_attributes

        if key_types is not None and len(key_types) != len(index_attributes):
            raise ValueError("The number of key types must match the number of index attributes")

        self._key_types: dict[str, type] = {}
        for i, attr in enumerate(self._index_attributes):
            self._key_types[attr] = object if key_types is None else key_types[i]

        self._key_types_registered: bool = False if key_types is None else True

    @property
    def force_init_types(self) -> bool:
        return self._force_key_types

    @property
    def index_attributes(self) -> list[str]:
        return self._index_attributes

    def __class_getitem__(cls, item: type) -> type[Registry]:
        cls.registry_type = item

        return cls

    def __getitem__(self, key: Any | tuple[str, Any]) -> Any:
        if isinstance(key, tuple):
            attr_name = key[0]
            idx = key[1]

            return self._registries[attr_name][idx]

        else:
            return self._joined_registry[key]

    def __contains__(self, item: Any):
        return item in self.values() or item in self._joined_registry

    def __len__(self) -> int:
        return len(self.values())

    def is_empty(self) -> bool:
        return len(self._joined_registry) == 0

    def items(self) -> list[tuple[tuple[Any], Any]]:
        items = []
        for value in self.values():
            items.append((tuple(self.keys_for_value(value=value)), value))
        return items

    def keys(self, attribute_name: str | None = None) -> list[Any]:
        if attribute_name is None:
            return list(self._joined_registry.keys())
        else:
            return list(self._registries[attribute_name].keys())

    def keys_grouped(self) -> list[tuple[Any]]:
        items = []
        for value in self.values():
            items.append(tuple(self.keys_for_value(value=value)))
        return items

    def keys_for_value(self, value: Any) -> list[Any]:
        return [key for key in self._joined_registry.keys() if self._joined_registry[key] == value]

    def values(self) -> list[Any]:
        return list(set(self._joined_registry.values()))

    def register(self, value: Any) -> None:

        def _type_name(t: type) -> str:
            return t.__module__ + "." + t.__name__

        if not isinstance(value, self.registry_type):
            raise TypeError(
                "The given object cannot be registered in this Registry as it has "
                f"the type '{_type_name(type(value))}'. The registry requires the type "
                f"'{_type_name(self.registry_type)}'."
            )

        if value in self.values():
            raise ValueError("The given object is already registered in this Registry.")

        idcs = []
        for attribute in self._index_attributes:
            index = getattr(value, attribute)

            if index in self._joined_registry:
                raise ValueError(
                    f"There already is a {self.registry_type.__name__} registered with "
                    f"the same {attribute}."
                )

            # Type check
            if (
                self._key_types_registered
                and self._force_key_types
                and not isinstance(index, self._key_types[attribute])
            ):
                raise TypeError(
                    f"The given object cannot be registered in this Registry as its attribute "
                    f" has the type('{attribute}')='{_type_name(type(index))}'. "
                    f"The registry requires type('{attribute}')="
                    f"'{_type_name(self._key_types[attribute])}'."
                )

            idcs.append(index)

        # Initialize key types if first registry entry
        if not self._key_types_registered and self.is_empty() and self._force_key_types:
            for attribute in self._index_attributes:
                self._key_types[attribute] = type(getattr(value, attribute))
            self._key_types_registered = True

        for idx in idcs:
            self._joined_registry[idx] = value

    def unregister_value(self, value: Any) -> None:
        if value not in self.values():
            raise ValueError("The given object is not registered in this Registry.")

        for attribute in self._index_attributes:
            index = getattr(value, attribute)
            del self._joined_registry[index]

    def unregister_index(self, index: Any) -> None:
        if index not in self._joined_registry:
            raise ValueError("The given index is not registered in this Registry.")

        value = self._joined_registry[index]

        keys = self.keys_for_value(value=value)

        for key in keys:
            del self._joined_registry[key]

    def tree_view(self) -> Tree:
        root = Tree(f"{self.registry_type.__name__} Registry")
        items = self.items()
        for keys, value in items:
            root.add(Tree(f"{keys}: {value}"))
        return root

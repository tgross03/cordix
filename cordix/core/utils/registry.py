import copy
from typing import Any

import numpy as np
from rich.tree import Tree

from cordix.core.exceptions.generic import DuplicateKeyError, ReadOnlyError


class Registry:
    """
    A ``Registry`` contains objects registered by attributes of the object.
    The values of these attributes should be unique and constant for each object as they are
    used for identifying the objects.
    Each registry can only store one type of object, meaning all objects saved
    in the registry must have the same type.

    The registry can index objects using multiple attributes. Therefore, an object can be retrieved
    through different keys. This will be explained in the example below by creating an example
    class and two objects of this class.

    .. code-block:: python

        from cordix.core.utils.registry import Registry
        from rich import print # For printing the registry tree

        class ExampleClass:
            def __init__(self, unique_id: int, unique_name: str, some_value: float):
                self.unique_id: int = unique_id
                self.unique_name: str = unique_name
                self.some_value: float = some_value

            def __repr__(self):
                return (
                    f"Example(unique_id={self.unique_id},
                    f"unique_name={self.unique_name}, "
                    f"some_value={self.some_value})"
                )

        obj1 = ExampleClass(0, "Foo", 1.0)
        obj2 = ExampleClass(1, "Bar", 1.5)

    Given these objects, we can now create a registry and register them in it.
    The attributes which will be used to index the objects are specified in the
    `index_attributes` parameter.
    We will be using the attributes ``unique_id`` and ``unique_name``.
    We have to specify the type of the indexed entries by providing it to the class
    on registration.

    .. code-block:: python

        registry = Registry[ExampleClass](["unique_id", "unique_name"])

        registry.register(obj1)
        registry.register(obj2)

        print(registry.tree_view())

    The resulting registry tree will look like this:

    .. code-block::

        ExampleClass Registry
        ├── (0, 'Foo'): ExampleClass(unique_id=0, unique_name=Foo, some_value=1.0)
        └── (1, 'Bar'): ExampleClass(unique_id=1, unique_name=Bar, some_value=1.5)

    We can see that the objects are indexed using the values of their attributes
    ``unique_id`` and``unique_name``.

    We can access the objects using square brackets like for a dictionary. However, we can
    do this in two ways:

        1. Without providing an explicit attribute to access the objects: ``registry[key]``.
        2. By providing an explicit attribute to access the objects: ``registry[attr_name, key]``.

    The first way is useful if your indexing attributes either have different types or if you are
    certain that the attribute values are completely unique across all objects and do not overlap
    with other attribute values. An exemplary application case would be accessing an object based on
    a user input which identifies an object by either a unique ID or a unique name.
    However, this way is technically more unsafe as it could fail if any attribute value is
    present multiple times.

    The second way is the safest as it either returns a unique error or fails if the object is not
    present in the registry. Therefore, it is recommended to avoid unforeseen errors.

    An example of accessing objects with both ways is presented in the following:

    .. code-block:: python

        >>> registry[0]
        ExampleClass(unique_id=0, unique_name=Foo, some_value=1.0)

        >>> registry["unique_id", 0]
        ExampleClass(unique_id=0, unique_name=Foo, some_value=1.0)

    The same works for the other attribute.

    .. code-block:: python

        >>> registry["Foo"]
        ExampleClass(unique_id=0, unique_name=Foo, some_value=1.0)

        >>> registry["unique_name", "Foo"]
        ExampleClass(unique_id=0, unique_name=Foo, some_value=1.0)

    Trying this with the wrong attribute will raise a ``KeyError``.

    .. code-block:: python

        >>> registry["some_value", 1.0]
        KeyError: 'some_value'

    """

    registry_type: type

    def __init__(
        self,
        index_attributes: list[str],
        force_key_types: bool = True,
        key_types: list[type] | None = None,
        read_only: bool = False,
    ):
        """
        Parameters
        ----------

        index_attributes : list[str]

        force_key_types : bool, optional
            Whether to force the type indices being registered.
            Default is ``True``.

        key_types : list[type] | None
            The types of the indexed attributes. The types are only enforced if ``force_key_types``
            is set to ``True``.
            If set to ``None``, the types are determined automatically once the first object is
            registered.
            Default is ``None``.

        read_only : bool, optional
            Whether the registry is read-only.
            Default is ``False``.

        """
        self._registries: dict[str, dict[Any, Any]] = {
            attr: {} for attr in index_attributes
        }
        self._force_key_types: bool = force_key_types
        self._index_attributes: list[str] = index_attributes
        self._read_only: bool = read_only

        if key_types is not None and len(key_types) != len(index_attributes):
            raise ValueError(
                "The number of key types must match the number of index attributes"
            )

        self._key_types: dict[str, type] = {}
        for i, attr in enumerate(self._index_attributes):
            self._key_types[attr] = object if key_types is None else key_types[i]

        self._key_types_registered: bool = key_types is not None

    ################## GETTERS ###################

    @property
    def force_key_types(self) -> bool:
        """
        Returns
        -------
        bool
            Whether to force the type of the indices to the ones that are initially registered.
        """
        return self._force_key_types

    @property
    def index_attributes(self) -> list[str]:
        """
        Returns
        -------
        list[str]
            The names of the indexed attributes.
        """
        return self._index_attributes

    @property
    def read_only(self) -> bool:
        """
        Returns
        -------
        bool
            Whether the registry is read-only.
        """
        return self._read_only

    ################# BUILT-INS ##################

    def __class_getitem__(cls, item: type) -> type["Registry"]:
        cls.registry_type = item

        return cls

    def __getitem__(self, key: Any | tuple[str, Any]) -> Any:
        if isinstance(key, tuple):
            attr_name = key[0]
            idx = key[1]

            return self._registries[attr_name][idx]

        else:
            vals = []
            for attr in self._index_attributes:
                if key in self._registries[attr]:
                    vals.append(self._registries[attr][key])

            if len(vals) == 1:
                return vals[0]
            elif len(vals) == 0:
                raise KeyError(str(key))
            else:
                raise DuplicateKeyError(
                    f"The given key '{key}' appears multiple times in the "
                    "registry. You have to specify the attribute of the given key."
                )

    def __delitem__(self, index: Any | tuple[str, Any]):

        if isinstance(index, tuple):
            attr_name = index[0]
            idx = index[1]
            self.unregister_index(index=idx, attribute=attr_name)

        else:
            self.unregister_index(index=index)

    def __eq__(self, value: "Registry[Any]", /) -> bool:
        for key, registry in value._registries.items():

            if key not in self._registries:
                return False

            if set(registry.keys()) != set(self._registries[key].keys()):
                return False

            if set(registry.values()) != set(self._registries[key].values()):
                return False

        return (
            self.registry_type == value.registry_type
            and self._key_types == value._key_types
            and self._index_attributes == value._index_attributes
        )

    def __ne__(self, value: "Registry[Any]", /) -> bool:
        return not self.__eq__(value)

    def __contains__(self, item: Any):
        return item in self.values() or item in self.keys(attribute=None)

    def __len__(self) -> int:
        return len(self.values())

    ############## (UN)REGISTRATION ##############

    def register(self, value: Any) -> None:
        """
        Register the given value in the registry.

        Parameter
        ---------

        value : Any
        The value to register.

        """

        if self.read_only:
            raise ReadOnlyError("The registry is read-only.")

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

            if index in self._registries[attribute]:
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

        if not self._key_types_registered:
            for attribute in self._index_attributes:
                self._key_types[attribute] = type(getattr(value, attribute))
            self._key_types_registered = True

        for attribute in self._index_attributes:
            index = getattr(value, attribute)
            self._registries[attribute][index] = value

    def unregister_value(self, value: Any) -> None:
        """
        Unregister the given value from the registry.

        Parameter
        ---------

        value : Any
            The value to unregister.

        """

        if self.read_only:
            raise ReadOnlyError("The registry is read-only.")

        if value not in self.values():
            raise ValueError("The given object is not registered in this Registry.")

        for attribute in self._index_attributes:
            index = getattr(value, attribute)
            del self._registries[attribute][index]

    def unregister_index(self, index: Any, attribute: str | None = None) -> None:
        """
        Unregister the given value from the registry.

        Parameter
        ---------

        index : Any
            The index to unregister.

        attribute: str | None, optional
            The attribute of the index to unregister.
            If set to ``None``, all attributes are considered.

            .. warning::

                If the index is registered under multiple attributes, a
                :py:class:`DuplicateKeyError` is raised.

        """

        if self.read_only:
            raise ReadOnlyError("The registry is read-only.")

        if attribute is not None:
            value = self[attribute, index]
            self.unregister_value(value=value)
        else:
            values = []
            for attribute in self._index_attributes:
                try:
                    values.append(self[attribute, index])
                except KeyError:
                    continue

            if len(values) > 1:
                raise DuplicateKeyError(
                    f"The given index '{index}' is registered under"
                    "multiple attributes. Specify the attribute of the "
                    "index to unregister."
                )
            elif len(values) == 0:
                raise KeyError(str(index))
            else:
                self.unregister_value(values[0])

    def clear(self) -> None:

        if self._read_only:
            raise ReadOnlyError("The registry is read-only.")

        self._registries.clear()

    ################### UTILS ####################

    def is_empty(self) -> bool:
        """
        Returns whether the registry is empty.

        Returns
        -------

        bool
            Whether the registry is empty.
        """

        return bool(
            np.sum([len(registry) for registry in self._registries.values()]) == 0
        )

    def items(self) -> list[tuple[dict[str, Any], Any]]:
        """
        Returns a list of tuples containing the keys and entries of the registry.

        Returns
        -------
        list[tuple[dict[str, Any], Any]]
            A list of tuples containing the keys and entries of the registry.
        """

        items = []
        for value in self.values():
            items.append((self.keys_for_entry(entry=value), value))
        return items

    def keys(self, attribute: str | None = None) -> list[Any]:
        """
        Returns a list of keys used to register the entries.
        Either returns all keys if ``attribute_name`` is ``None`` or the keys registered
        for the attribute with name ``attribute_name``.

        Parameters
        ----------

        attribute : str | None, optional
            The name of the attribute to return the keys for.
            If ``None``, returns all keys.
            Default is ``None``.

        Returns
        -------
        list[Any]
            A list of keys used to register the entries.
        """

        if attribute is None:
            keys = []
            for attribute in self._index_attributes:
                keys.extend(list(self._registries[attribute].keys()))
            return list(set(keys))
        else:
            return list(self._registries[attribute].keys())

    def keys_grouped(self) -> list[dict[str, Any]]:
        """
        Returns a dicts of attributes and keys grouped by the object they index.

        Returns
        -------
        list[dict[str, Any]]
            A list of dicts of attributes and keys grouped by the object they index.
        """
        keys = []
        for value in self.values():
            keys.append(self.keys_for_entry(entry=value))
        return keys

    def keys_for_entry(
        self, entry: Any, attribute: str | None = None
    ) -> dict[str, Any]:
        """
        Returns the key(s) used to index the given entry. Can either return all keys
        or a single key if ``attribute`` is specified.

        Parameters
        ----------

        entry: Any
            The entry to get the key(s) for.

        attribute: str | None, optional
            The name of the attribute to get the key for.
            If set to ``None``, all keys for the entry are returned.
            Default is ``None``.

        Returns
        -------
        dict[str, Any]
            A dict containing the key(s) used to index the
            given entry categorized by their attribute.
        """

        val_error = ValueError(
            "The given entry is not registered with this item. "
            "This might indicate a problem with the registry. "
            "Report this issue to the developers."
        )

        if entry not in self:
            raise KeyError(str(entry))
        if attribute is None:
            keys = {}
            for attribute in self._index_attributes:
                for key, value in self._registries[attribute].items():
                    if value == entry:
                        keys[attribute] = key
            if len(keys) != len(self._index_attributes):
                raise val_error
            return keys
        else:
            for key, value in self._registries[attribute].items():
                if value == entry:
                    return {attribute: key}
            raise val_error

    def values(self) -> list[Any]:
        """
        Returns all objects saved in the registry.

        Returns
        -------

        list[Any]
            The list of all objects saved in the registry.
        """
        values = []
        for registry in self._registries.values():
            values.extend(registry.values())
        return list(set(values))

    def tree_view(self) -> Tree:
        """
        Returns all objects saved in the registry.

        Returns
        -------

        :py:class:`rich.tree.Tree`
            The tree view of all objects saved in the registry.
        """
        root = Tree(f"{self.registry_type.__name__} Registry")
        items = self.items()
        for keys, value in items:
            root.add(Tree(f"{keys}: {value}"))
        return root

    def copy(self, read_only: bool = False) -> "Registry[Any]":
        """
        Returns a copy of the registry.

        Parameters
        ----------

        read_only : bool, optional
            Whether the copy should be read-only.
            Default is ``False``.

        Returns
        -------

        :py:class:`Registry`
            The copy of the registry.
        """
        instance = Registry[self.registry_type](
            index_attributes=self._index_attributes,
            force_key_types=self._force_key_types,
            key_types=[self._key_types[attr] for attr in self._index_attributes],
            read_only=read_only,
        )

        for attribute, registry in self._registries.items():
            memo = {id(obj): obj for obj in registry.values()}
            instance._registries[attribute] = copy.deepcopy(registry, memo=memo)
        return instance

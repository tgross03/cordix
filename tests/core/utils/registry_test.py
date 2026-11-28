import pytest
from rich.tree import Tree

from cordix.core.exceptions.generic import DuplicateKeyError, ReadOnlyError
from cordix.core.utils import Registry


class ExampleClass:
    def __init__(self, unique_id: int, unique_name: str, some_value: float):
        self.unique_id: int = unique_id
        self.unique_name: str = unique_name
        self.some_value: float = some_value

    def __repr__(self):
        return (
            f"Example(unique_id={self.unique_id}, "
            f"unique_name={self.unique_name}, "
            f"some_value={self.some_value})"
        )


def _generate_registry(
    force_key_types: bool, init_attribute_types: bool
) -> Registry[ExampleClass]:
    return Registry[ExampleClass](
        index_attributes=["unique_id", "unique_name"],
        force_key_types=force_key_types,
        key_types=[int, str] if init_attribute_types else None,
    )


def _generate_example_objects() -> list[ExampleClass]:
    return [
        ExampleClass(unique_id=1, unique_name="Foo", some_value=1.0),
        ExampleClass(unique_id=2, unique_name="Bar", some_value=2.0),
        ExampleClass(unique_id=3, unique_name="Baz", some_value=3.0),
    ]


def test_registry_non_type_restricted() -> None:
    registry = _generate_registry(force_key_types=False, init_attribute_types=False)
    assert registry.registry_type == ExampleClass
    assert not registry._key_types_registered
    assert registry.is_empty()

    with pytest.raises(ValueError):
        _ = Registry[ExampleClass](
            index_attributes=["unique_id", "unique_name"],
            force_key_types=False,
            key_types=[int],
        )

    objects = _generate_example_objects()
    excluded_object = ExampleClass(unique_id=4, unique_name="Qux", some_value=4.0)

    for obj in objects:
        registry.register(obj)

    assert registry._key_types_registered
    assert set(registry._key_types.values()) == {str, int}
    assert not registry.force_key_types
    assert not registry.read_only
    assert registry.index_attributes == ["unique_id", "unique_name"]

    assert len(registry) == 3

    for obj in objects:
        assert obj in registry
        assert registry[obj.unique_id] == obj
        assert registry[obj.unique_name] == obj
        assert registry["unique_id", obj.unique_id] == obj
        assert registry["unique_name", obj.unique_name] == obj

    assert set(objects) == set(registry.values())

    for indices, obj in registry.items():
        assert indices["unique_id"] == obj.unique_id
        assert indices["unique_name"] == obj.unique_name

    for key in registry.keys():
        assert key in registry

    assert len(registry.keys()) == len(registry._index_attributes) * len(objects)
    assert len(registry.keys(attribute="unique_id")) == len(objects)
    assert len(registry.keys(attribute="unique_name")) == len(objects)

    with pytest.raises(KeyError):
        _ = registry[excluded_object.unique_id]

    with pytest.raises(KeyError):
        _ = registry[excluded_object.unique_name]

    with pytest.raises(KeyError):
        _ = registry["unique_id", excluded_object.unique_id]

    with pytest.raises(KeyError):
        _ = registry["unique_name", excluded_object.unique_name]

    with pytest.raises(ValueError):
        registry.register(objects[0])

    duplicate_key_obj = ExampleClass(unique_id=1, unique_name="Quux", some_value=10.0)

    with pytest.raises(ValueError):
        registry.register(duplicate_key_obj)

    with pytest.raises(KeyError):
        registry.keys_for_entry(entry=excluded_object)

    for obj in objects:
        keys = registry.keys_for_entry(entry=obj)
        for key, val in keys.items():
            assert getattr(obj, key) == val
        for attr in ["unique_id", "unique_name"]:
            keys = registry.keys_for_entry(entry=obj, attribute=attr)
            assert list(keys.keys()) == [attr]
            assert list(keys.values()) == [getattr(obj, attr)]

    for keys in registry.keys_grouped():
        assert set(keys.keys()) == {"unique_id", "unique_name"}

    assert isinstance(registry.tree_view(), Tree)

    copied_registry = registry.copy()
    assert copied_registry is not registry
    assert copied_registry == registry

    wrong_copied_registry = registry.copy()
    wrong_copied_registry.unregister_value(objects[0])
    assert wrong_copied_registry != registry

    for i, obj in enumerate(objects):
        registry.unregister_value(value=obj)
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    with pytest.raises(TypeError):
        registry.register("test")

    with pytest.raises(KeyError):
        registry.unregister_index(index="corge")

    with pytest.raises(ValueError):
        registry.unregister_value(excluded_object)

    for i, obj in enumerate(objects):
        registry.unregister_index(index=obj.unique_id)
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    for i, obj in enumerate(objects):
        registry.unregister_index(index=obj.unique_id, attribute="unique_id")
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    for i, obj in enumerate(objects):
        registry.unregister_index(index=obj.unique_name, attribute="unique_name")
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    for i, obj in enumerate(objects):
        del registry[obj.unique_id]
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    for i, obj in enumerate(objects):
        del registry["unique_id", obj.unique_id]
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    for i, obj in enumerate(objects):
        del registry["unique_name", obj.unique_name]
        assert len(registry) == len(objects) - i - 1
        assert obj not in registry

    assert registry.is_empty()
    registry = copied_registry.copy()

    registry.clear()
    assert registry.is_empty()

    registry = copied_registry.copy(read_only=True)

    with pytest.raises(ReadOnlyError):
        registry.unregister_index(index=objects[0].unique_id, attribute="unique_id")

    with pytest.raises(ReadOnlyError):
        registry.unregister_value(objects[0])

    with pytest.raises(ReadOnlyError):
        registry.register(excluded_object)

    with pytest.raises(ReadOnlyError):
        registry.clear()

    assert registry.read_only

    registry = copied_registry.copy()
    del registry._registries["unique_id"][objects[0].unique_id]

    with pytest.raises(ValueError):
        _ = registry.keys_for_entry(entry=objects[0])

    with pytest.raises(ValueError):
        _ = registry.keys_for_entry(entry=objects[0], attribute="unique_id")

    duplicate_key_obj = ExampleClass(
        unique_id="Foo", unique_name="Quux", some_value=10.0
    )
    registry.register(duplicate_key_obj)

    with pytest.raises(DuplicateKeyError):
        registry.unregister_index(index=duplicate_key_obj.unique_id)

    with pytest.raises(DuplicateKeyError):
        _ = registry["Foo"]


def test_registry_type_restricted() -> None:
    registry = _generate_registry(force_key_types=True, init_attribute_types=True)
    assert registry._key_types_registered
    assert registry.force_key_types
    assert registry.is_empty()

    objects = _generate_example_objects()
    excluded_object = ExampleClass(unique_id="4", unique_name="Qux", some_value=4.0)

    for obj in objects:
        registry.register(obj)

    with pytest.raises(TypeError):
        registry.register(excluded_object)

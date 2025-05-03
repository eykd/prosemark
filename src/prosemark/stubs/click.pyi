"""Type stubs for click package."""

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class Context:
    obj: dict[str, Any]
    def ensure_object(self, class_: type) -> Any: ...

class Parameter:
    name: str

class Option(Parameter): ...

class Argument(Parameter): ...

class Command:
    name: str
    params: list[Parameter]
    callback: Callable[..., Any]
    help: str | None
    epilog: str | None
    short_help: str | None
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

class Group(Command):
    commands: dict[str, Command]

class Path:
    exists: bool
    file_okay: bool
    dir_okay: bool
    writable: bool
    readable: bool
    resolve_path: bool
    allow_dash: bool
    path_type: type

def group(name: str | None = None, **attrs: Any) -> Callable[[F], Group]: ...
def command(name: str | None = None, **attrs: Any) -> Callable[[F], Command]: ...
def argument(*param_decls: str, **attrs: Any) -> Callable[[F], F]: ...
def option(*param_decls: str, **attrs: Any) -> Callable[[F], F]: ...
def pass_context(f: F) -> F: ...
def pass_obj(f: F) -> F: ...
def version_option(version: str | None = None, **kwargs: Any) -> Callable[[F], F]: ...
def echo(message: str | None = None, file: Any = None, nl: bool = True, err: bool = False, color: bool | None = None) -> None: ...
def Path(exists: bool = False, file_okay: bool = True, dir_okay: bool = True, writable: bool = False, readable: bool = True, resolve_path: bool = False, allow_dash: bool = False, path_type: type | None = None) -> Any: ...

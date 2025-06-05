import typing


def patch_forward_ref_evaluate():
    """Patch typing.ForwardRef._evaluate for pydantic v1 compatibility on Python 3.12"""

    orig_fn = typing.ForwardRef._evaluate

    def _evaluate(self, *args, **kwargs):
        # pydantic v1 calls: _evaluate(globalns, localns, recursive_guard)
        # Python 3.12 expects: _evaluate(globalns, localns, type_params=None, *, recursive_guard)
        if len(args) == 3:
            globalns, localns, recursive_guard = args
            type_params = None
        elif len(args) == 4:
            globalns, localns, type_params, recursive_guard = args
        else:
            raise TypeError("Unexpected arguments for ForwardRef._evaluate")
        if recursive_guard is None:
            recursive_guard = set()
        return orig_fn(
            self, globalns, localns, type_params, recursive_guard=recursive_guard
        )

    typing.ForwardRef._evaluate = _evaluate


patch_forward_ref_evaluate()

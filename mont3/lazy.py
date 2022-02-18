from __future__ import annotations

from enum import Enum

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .validation import validate


class Mode(Enum):
    NONE = -1
    SINGLE = 0
    LINE = 1
    TABLE = 2


class LazyAxes(Axes):

    attrs = ["kind", "args", "kwargs", "__str__"]

    def __init__(self, geo):
        self.geo = geo

        self.kind: str = None
        self.args = []
        self.kwargs = {}

    def __getattribute__(self, name: str):
        if name == "attrs" or name in self.attrs:
            return super().__getattribute__(name)

        def store(*args, **kwargs):
            self.kind = name
            self.args = args
            self.kwargs = kwargs

        # TODO: <store:> って表示されるの直したい
        return store

    def __str__(self):
        return f"<LazyAxes: {self.kind}>"


class figure(Axes):

    def __init__(self, strict=True):
        self.lazyaxes: list[tuple[tuple, LazyAxes]] = []
        self.lazyaxes_by_slice: list[tuple[tuple, LazyAxes]] = []
        self.mode = Mode.NONE
        self.strict = strict
        self.rmax = 0
        self.cmax = 0

    def __getitem__(self, key) -> LazyAxes:
        # FIXME: raise error は後で
        if not isinstance(key, tuple):
            key = (slice(None), key)
            # FIXME: 後で1次元だったら転置する。先にテスト書く
        if len(key) != 2:
            raise ValueError

        r, c = key
        if isinstance(r, int):
            self.rmax = max(self.rmax, r + 1)
        if isinstance(c, int):
            self.rmax = max(self.rmax, 1)
            self.cmax = max(self.cmax, c + 1)

        ax = LazyAxes(geo=key)
        if any(isinstance(obj, slice) for obj in key):
            self.lazyaxes_by_slice.append((key, ax))
        else:
            self.lazyaxes.append((key, ax))
        return ax

    def __getattribute__(self, name):
        # TODO: slice(None) とみなしたい
        if name not in dir(Axes):
            return super().__getattribute__(name)

        if self.mode is Mode.NONE:
            self.mode = Mode.SINGLE
        if self.mode is not Mode.SINGLE:
            raise AttributeError("Single mode is selected."
                                 " Get axes via indices. ex) fig[0].plot(...)")
        ax = LazyAxes(geo=(0, 0))
        self.lazyaxes.append(((0, 0), ax))
        return getattr(ax, name)

    def _draw(self):
        # TODO: データがないグラフは消す
        if self.rmax == 0:
            raise ValueError("nothing to plot.")

        fig, axes = plt.subplots(self.rmax, self.cmax, squeeze=False)

        for key, lazy_ax in self.lazyaxes:
            if lazy_ax.kind:
                getattr(axes[key], lazy_ax.kind)(*lazy_ax.args, **lazy_ax.kwargs)

        for key, lazy_ax in self.lazyaxes_by_slice:
            for ax in axes[key].reshape(-1):
                getattr(ax, lazy_ax.kind)(*lazy_ax.args, **lazy_ax.kwargs)

        validate(fig, strict=self.strict)
        return fig, axes

    def show(self):
        # self[:].grid(True)
        self._draw()
        # TODO: これをオブジェクト指向的にやる方法って無いのかな
        plt.tight_layout()
        plt.show()

    def save(self, filename):
        self._draw()
        plt.tight_layout()
        plt.savefig(filename)

    def __str__(self):
        return f"<figure: {id(self)}>"

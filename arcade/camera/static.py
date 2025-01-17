from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Callable, Optional, Tuple, TYPE_CHECKING

from arcade.camera.data_types import CameraData, OrthographicProjectionData, PerspectiveProjectionData
from arcade.camera.projection_functions import (
    generate_view_matrix,
    generate_orthographic_matrix,
    generate_perspective_matrix,
    project_orthographic,
    project_perspective,
    unproject_orthographic,
    unproject_perspective
)

from arcade.window_commands import get_window

from pyglet.math import Mat4, Vec3, Vec2

if TYPE_CHECKING:
    from arcade.application import Window


class _StaticCamera:

    def __init__(self, view_matrix: Mat4, projection_matrix: Mat4,
                 viewport: Optional[Tuple[int, int, int, int]] = None,
                 *,
                 project_method: Optional[Callable[[Vec3, Tuple[int, int, int, int], Mat4, Mat4], Vec2]] = None,
                 unproject_method: Optional[Callable[[Vec2,
                                                      Tuple[int, int, int, int],
                                                      Mat4, Mat4, Optional[float]], Vec3]] = None,
                 window: Optional[Window] = None):
        self._win: Window = window or get_window()
        self._viewport: Tuple[int, int, int, int] = viewport or self._win.ctx.viewport
        self._view = view_matrix
        self._projection = projection_matrix

        self._project_method: Optional[Callable[[Vec3, Tuple, Mat4, Mat4], Vec2]] = project_method
        self._unproject_method: Optional[Callable[[Vec2, Tuple, Mat4, Mat4, Optional[float]], Vec3]] = unproject_method

    def use(self):
        self._win.current_camera = self

        self._win.ctx.viewport = self._viewport
        self._win.ctx.projection_matrix = self._projection
        self._win.ctx.view_matrix = self._view

    @contextmanager
    def activate(self) -> Generator[_StaticCamera, None, None]:
        prev = self._win.ctx.current_camera
        try:
            self.use()
            yield self
        finally:
            prev.use()

    def project(self, world_coordinate: Tuple[float, ...]) -> Tuple[float, float]:
        """
        Take a Vec2 or Vec3 of coordinates and return the related screen coordinate
        """
        if self._project_method is None:
            raise ValueError("This Static Camera was not provided a project method at creation")

        pos = self._project_method(
            Vec3(world_coordinate[0], world_coordinate[1], world_coordinate[2]),
            self._viewport, self._view, self._projection
        )
        return pos.x, pos.y

    def unproject(self,
            screen_coordinate: Tuple[float, float],
            depth: Optional[float] = None) -> Tuple[float, float, float]:
        """
        Take in a pixel coordinate from within
        the range of the window size and returns
        the world space coordinates.

        Essentially reverses the effects of the projector.

        Args:
            screen_coordinate: A 2D position in pixels from the bottom left of the screen.
                               This should ALWAYS be in the range of 0.0 - screen size.
            depth: The depth of the query
        Returns:
            A 3D vector in world space.
        """
        if self._unproject_method is None:
            raise ValueError("This Static Camera was not provided an unproject method at creation")

        pos = self._unproject_method(
            Vec2(screen_coordinate[0], screen_coordinate[1]),
            self._viewport, self._view, self._projection, depth
        )
        return pos.x, pos.y, pos.z

def static_from_orthographic(
        view: CameraData,
        orthographic: OrthographicProjectionData,
        *,
        window: Optional[Window] = None
) -> _StaticCamera:
    return _StaticCamera(
        generate_view_matrix(view),
        generate_orthographic_matrix(orthographic, view.zoom),
        orthographic.viewport, window=window,
        project_method=project_orthographic,
        unproject_method=unproject_orthographic
    )


def static_from_perspective(
        view: CameraData,
        perspective: OrthographicProjectionData,
        *,
        window: Optional[Window] = None
) -> _StaticCamera:
    return _StaticCamera(
        generate_view_matrix(view),
        generate_orthographic_matrix(perspective, view.zoom),
        perspective.viewport, window=window,
        project_method=project_perspective,
        unproject_method=unproject_perspective
    )


def static_from_raw_orthographic(
        projection: Tuple[float, float, float, float],
        near: float = -100.0, far: float = 100.0,
        zoom: float = 1.0,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        up: Tuple[float, float, float] = (0.0, 1.0, 0.0),
        forward: Tuple[float, float, float] = (0.0, 0.0, -1.0),
        viewport: Optional[Tuple[int, int, int, int]] = None,
        *,
        window: Optional[Window] = None
) -> _StaticCamera:
    view = generate_view_matrix(
        CameraData(position, up, forward, zoom)
    )
    proj = generate_orthographic_matrix(
        OrthographicProjectionData(
            projection[0], projection[1], projection[2], projection[3], near, far, viewport or (0, 0, 0, 0)), zoom
    )
    return _StaticCamera(view, proj, viewport, window=window,
                         project_method=project_orthographic,
                         unproject_method=unproject_orthographic)


def static_from_raw_perspective(
        aspect: float, fov: float,
        near: float = -100.0, far: float = 100.0,
        zoom: float = 1.0,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        up: Tuple[float, float, float] = (0.0, 1.0, 0.0),
        forward: Tuple[float, float, float] = (0.0, 0.0, -1.0),
        viewport: Optional[Tuple[int, int, int, int]] = None,
        *,
        window: Optional[Window] = None
) -> _StaticCamera:
    view = generate_view_matrix(
        CameraData(position, up, forward, zoom)
    )
    proj = generate_perspective_matrix(
        PerspectiveProjectionData(aspect, fov, near, far, viewport or (0, 0, 0, 0)), zoom
    )

    return _StaticCamera(view, proj, viewport, window=window,
                         project_method=project_perspective,
                         unproject_method=unproject_perspective)


def static_from_matrices(
        view: Mat4, projection: Mat4,
        viewport: Optional[Tuple[int, int, int, int]],
        *,
        window: Optional[Window]=None,
        project_method: Optional[Callable[[Vec3, Tuple[int, int, int, int], Mat4, Mat4], Vec2]]=None,
        unproject_method: Optional[Callable[[Vec2, Tuple[int, int, int, int], Mat4, Mat4, Optional[float]], Vec3]]=None
) -> _StaticCamera:
    return _StaticCamera(view, projection, viewport, window=window,
                         project_method=project_method, unproject_method=unproject_method)

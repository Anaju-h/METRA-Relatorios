from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import (
    QLineF,
    QPointF,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QKeyEvent,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QStyle,
    QStyleOptionGraphicsItem,
    QWidget,
)


DEFAULT_COLOR = "#EB2323"

HANDLE_SIZE = 10.0
MIN_SHAPE_SIZE = 8.0
MIN_LINE_LENGTH = 8.0


# =================================================================
# FUNÇÕES VISUAIS
# =================================================================


def normalized_color(
    value: str | None,
) -> QColor:
    color = QColor(
        value
        or DEFAULT_COLOR
    )

    if not color.isValid():
        return QColor(
            DEFAULT_COLOR
        )

    return color


def create_annotation_pen(
    color: str,
    stroke_width: float,
) -> QPen:
    pen = QPen(
        normalized_color(
            color
        )
    )

    pen.setWidthF(
        float(
            stroke_width
        )
    )

    pen.setCapStyle(
        Qt.PenCapStyle.RoundCap
    )

    pen.setJoinStyle(
        Qt.PenJoinStyle.RoundJoin
    )

    return pen


def create_clean_style_option(
    option: QStyleOptionGraphicsItem,
) -> QStyleOptionGraphicsItem:
    clean_option = QStyleOptionGraphicsItem(
        option
    )

    clean_option.state &= (
        ~QStyle.StateFlag.State_Selected
    )

    return clean_option


# =================================================================
# MIXIN PARA FORMAS REDIMENSIONÁVEIS
# =================================================================


class ResizableShapeMixin:
    HANDLE_TOP_LEFT = "top_left"
    HANDLE_TOP = "top"
    HANDLE_TOP_RIGHT = "top_right"
    HANDLE_RIGHT = "right"
    HANDLE_BOTTOM_RIGHT = "bottom_right"
    HANDLE_BOTTOM = "bottom"
    HANDLE_BOTTOM_LEFT = "bottom_left"
    HANDLE_LEFT = "left"

    def initialize_resizable_shape(
        self,
    ) -> None:
        self.active_handle: Optional[str] = None

        self.resize_start_scene_pos: (
            QPointF
            | None
        ) = None

        self.resize_start_rect: (
            QRectF
            | None
        ) = None

        self.operation_registered = False

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

        self.setAcceptHoverEvents(
            True
        )

    def handle_rectangles(
        self,
    ) -> dict[str, QRectF]:
        rectangle = self.rect()

        half = HANDLE_SIZE / 2

        points = {
            self.HANDLE_TOP_LEFT:
                rectangle.topLeft(),

            self.HANDLE_TOP:
                QPointF(
                    rectangle.center().x(),
                    rectangle.top(),
                ),

            self.HANDLE_TOP_RIGHT:
                rectangle.topRight(),

            self.HANDLE_RIGHT:
                QPointF(
                    rectangle.right(),
                    rectangle.center().y(),
                ),

            self.HANDLE_BOTTOM_RIGHT:
                rectangle.bottomRight(),

            self.HANDLE_BOTTOM:
                QPointF(
                    rectangle.center().x(),
                    rectangle.bottom(),
                ),

            self.HANDLE_BOTTOM_LEFT:
                rectangle.bottomLeft(),

            self.HANDLE_LEFT:
                QPointF(
                    rectangle.left(),
                    rectangle.center().y(),
                ),
        }

        return {
            name: QRectF(
                point.x() - half,
                point.y() - half,
                HANDLE_SIZE,
                HANDLE_SIZE,
            )
            for name, point in points.items()
        }

    def handle_at(
        self,
        position: QPointF,
    ) -> str | None:
        if not self.isSelected():
            return None

        for name, rectangle in (
            self.handle_rectangles()
            .items()
        ):
            if rectangle.contains(
                position
            ):
                return name

        return None

    def draw_handles(
        self,
        painter: QPainter,
    ) -> None:
        if not self.isSelected():
            return

        painter.save()

        painter.setPen(
            QPen(
                QColor(
                    "#0067B1"
                ),
                1.2,
            )
        )

        painter.setBrush(
            QBrush(
                QColor(
                    "#FFFFFF"
                )
            )
        )

        for rectangle in (
            self.handle_rectangles()
            .values()
        ):
            painter.drawRect(
                rectangle
            )

        painter.restore()

    def mousePressEvent(
        self,
        event,
    ) -> None:
        self.active_handle = (
            self.handle_at(
                event.pos()
            )
        )

        scene = self.scene()

        if (
            scene is not None
            and hasattr(
                scene,
                "save_history_state",
            )
        ):
            scene.save_history_state()

            self.operation_registered = True

        if self.active_handle:
            self.resize_start_scene_pos = (
                event.scenePos()
            )

            self.resize_start_rect = QRectF(
                self.rect()
            )

            event.accept()

            return

        super().mousePressEvent(
            event
        )

    def mouseMoveEvent(
        self,
        event,
    ) -> None:
        if (
            not self.active_handle
            or self.resize_start_scene_pos
            is None
            or self.resize_start_rect
            is None
        ):
            super().mouseMoveEvent(
                event
            )

            self.keep_shape_inside_image()

            return

        current_scene_pos = (
            self.clamp_scene_point(
                event.scenePos()
            )
        )

        start_local = (
            self.mapFromScene(
                self.resize_start_scene_pos
            )
        )

        current_local = (
            self.mapFromScene(
                current_scene_pos
            )
        )

        delta = (
            current_local
            - start_local
        )

        rectangle = QRectF(
            self.resize_start_rect
        )

        if self.active_handle in {
            self.HANDLE_TOP_LEFT,
            self.HANDLE_LEFT,
            self.HANDLE_BOTTOM_LEFT,
        }:
            rectangle.setLeft(
                rectangle.left()
                + delta.x()
            )

        if self.active_handle in {
            self.HANDLE_TOP_RIGHT,
            self.HANDLE_RIGHT,
            self.HANDLE_BOTTOM_RIGHT,
        }:
            rectangle.setRight(
                rectangle.right()
                + delta.x()
            )

        if self.active_handle in {
            self.HANDLE_TOP_LEFT,
            self.HANDLE_TOP,
            self.HANDLE_TOP_RIGHT,
        }:
            rectangle.setTop(
                rectangle.top()
                + delta.y()
            )

        if self.active_handle in {
            self.HANDLE_BOTTOM_LEFT,
            self.HANDLE_BOTTOM,
            self.HANDLE_BOTTOM_RIGHT,
        }:
            rectangle.setBottom(
                rectangle.bottom()
                + delta.y()
            )

        rectangle = rectangle.normalized()

        if rectangle.width() < MIN_SHAPE_SIZE:
            rectangle.setWidth(
                MIN_SHAPE_SIZE
            )

        if rectangle.height() < MIN_SHAPE_SIZE:
            rectangle.setHeight(
                MIN_SHAPE_SIZE
            )

        self.prepareGeometryChange()

        self.setRect(
            rectangle
        )

        self.keep_shape_inside_image()

        self.update()

        event.accept()

    def mouseReleaseEvent(
        self,
        event,
    ) -> None:
        resizing = bool(
            self.active_handle
        )

        self.active_handle = None

        self.resize_start_scene_pos = None
        self.resize_start_rect = None

        if resizing:
            self.keep_shape_inside_image()

            self.finish_registered_operation()

            event.accept()

            return

        super().mouseReleaseEvent(
            event
        )

        self.keep_shape_inside_image()

        self.finish_registered_operation()

    def clamp_scene_point(
        self,
        point: QPointF,
    ) -> QPointF:
        scene = self.scene()

        if (
            scene is None
            or not hasattr(
                scene,
                "image_rect",
            )
            or scene.image_rect.isNull()
        ):
            return point

        rectangle = scene.image_rect

        return QPointF(
            min(
                max(
                    point.x(),
                    rectangle.left(),
                ),
                rectangle.right(),
            ),
            min(
                max(
                    point.y(),
                    rectangle.top(),
                ),
                rectangle.bottom(),
            ),
        )

    def keep_shape_inside_image(
        self,
    ) -> None:
        scene = self.scene()

        if (
            scene is None
            or not hasattr(
                scene,
                "image_rect",
            )
            or scene.image_rect.isNull()
        ):
            return

        image_rectangle = scene.image_rect

        scene_bounds = (
            self.mapRectToScene(
                self.rect()
            )
        )

        delta_x = 0.0
        delta_y = 0.0

        if scene_bounds.left() < image_rectangle.left():
            delta_x = (
                image_rectangle.left()
                - scene_bounds.left()
            )

        elif scene_bounds.right() > image_rectangle.right():
            delta_x = (
                image_rectangle.right()
                - scene_bounds.right()
            )

        if scene_bounds.top() < image_rectangle.top():
            delta_y = (
                image_rectangle.top()
                - scene_bounds.top()
            )

        elif scene_bounds.bottom() > image_rectangle.bottom():
            delta_y = (
                image_rectangle.bottom()
                - scene_bounds.bottom()
            )

        if (
            delta_x != 0.0
            or delta_y != 0.0
        ):
            self.moveBy(
                delta_x,
                delta_y,
            )

    def finish_registered_operation(
        self,
    ) -> None:
        if not self.operation_registered:
            return

        self.operation_registered = False

        scene = self.scene()

        if (
            scene is not None
            and hasattr(
                scene,
                "finalize_change",
            )
        ):
            scene.finalize_change()


# =================================================================
# RETÂNGULO
# =================================================================


class ResizableRectangleItem(
    ResizableShapeMixin,
    QGraphicsRectItem,
):
    def __init__(
        self,
        rectangle: QRectF | None = None,
    ):
        QGraphicsRectItem.__init__(
            self,
            rectangle
            or QRectF(),
        )

        self.initialize_resizable_shape()

        self.setData(
            0,
            "rectangle",
        )

    def boundingRect(
        self,
    ) -> QRectF:
        return (
            QGraphicsRectItem
            .boundingRect(self)
            .adjusted(
                -HANDLE_SIZE,
                -HANDLE_SIZE,
                HANDLE_SIZE,
                HANDLE_SIZE,
            )
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        QGraphicsRectItem.paint(
            self,
            painter,
            create_clean_style_option(
                option
            ),
            widget,
        )

        self.draw_handles(
            painter
        )


# =================================================================
# CÍRCULO
# =================================================================


class ResizableEllipseItem(
    ResizableShapeMixin,
    QGraphicsEllipseItem,
):
    def __init__(
        self,
        rectangle: QRectF | None = None,
    ):
        QGraphicsEllipseItem.__init__(
            self,
            rectangle
            or QRectF(),
        )

        self.initialize_resizable_shape()

        self.setData(
            0,
            "circle",
        )

    def boundingRect(
        self,
    ) -> QRectF:
        return (
            QGraphicsEllipseItem
            .boundingRect(self)
            .adjusted(
                -HANDLE_SIZE,
                -HANDLE_SIZE,
                HANDLE_SIZE,
                HANDLE_SIZE,
            )
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        QGraphicsEllipseItem.paint(
            self,
            painter,
            create_clean_style_option(
                option
            ),
            widget,
        )

        self.draw_handles(
            painter
        )


# =================================================================
# LINHA
# =================================================================


class ResizableLineItem(
    QGraphicsLineItem,
):
    HANDLE_START = "start"
    HANDLE_END = "end"

    def __init__(
        self,
        line: QLineF | None = None,
    ):
        super().__init__(
            line
            or QLineF()
        )

        self.active_handle: (
            str
            | None
        ) = None

        self.operation_registered = False

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

        self.setAcceptHoverEvents(
            True
        )

        self.setData(
            0,
            "line",
        )

    def handle_rectangles(
        self,
    ) -> dict[str, QRectF]:
        line = self.line()

        half = HANDLE_SIZE / 2

        return {
            self.HANDLE_START:
                QRectF(
                    line.p1().x() - half,
                    line.p1().y() - half,
                    HANDLE_SIZE,
                    HANDLE_SIZE,
                ),

            self.HANDLE_END:
                QRectF(
                    line.p2().x() - half,
                    line.p2().y() - half,
                    HANDLE_SIZE,
                    HANDLE_SIZE,
                ),
        }

    def handle_at(
        self,
        point: QPointF,
    ) -> str | None:
        if not self.isSelected():
            return None

        for name, rectangle in (
            self.handle_rectangles()
            .items()
        ):
            if rectangle.contains(
                point
            ):
                return name

        return None

    def mousePressEvent(
        self,
        event,
    ) -> None:
        self.active_handle = (
            self.handle_at(
                event.pos()
            )
        )

        scene = self.scene()

        if (
            scene is not None
            and hasattr(
                scene,
                "save_history_state",
            )
        ):
            scene.save_history_state()

            self.operation_registered = True

        if self.active_handle:
            event.accept()

            return

        super().mousePressEvent(
            event
        )

    def mouseMoveEvent(
        self,
        event,
    ) -> None:
        if not self.active_handle:
            super().mouseMoveEvent(
                event
            )

            self.keep_line_inside_image()

            return

        scene_point = (
            self.clamp_scene_point(
                event.scenePos()
            )
        )

        local_point = (
            self.mapFromScene(
                scene_point
            )
        )

        line = QLineF(
            self.line()
        )

        if (
            self.active_handle
            == self.HANDLE_START
        ):
            line.setP1(
                local_point
            )

        else:
            line.setP2(
                local_point
            )

        if line.length() >= MIN_LINE_LENGTH:
            self.prepareGeometryChange()

            self.setLine(
                line
            )

            self.update()

        event.accept()

    def mouseReleaseEvent(
        self,
        event,
    ) -> None:
        resizing = bool(
            self.active_handle
        )

        self.active_handle = None

        if resizing:
            self.finish_registered_operation()

            event.accept()

            return

        super().mouseReleaseEvent(
            event
        )

        self.keep_line_inside_image()

        self.finish_registered_operation()

    def clamp_scene_point(
        self,
        point: QPointF,
    ) -> QPointF:
        scene = self.scene()

        if (
            scene is None
            or not hasattr(
                scene,
                "image_rect",
            )
            or scene.image_rect.isNull()
        ):
            return point

        rectangle = scene.image_rect

        return QPointF(
            min(
                max(
                    point.x(),
                    rectangle.left(),
                ),
                rectangle.right(),
            ),
            min(
                max(
                    point.y(),
                    rectangle.top(),
                ),
                rectangle.bottom(),
            ),
        )

    def keep_line_inside_image(
        self,
    ) -> None:
        scene = self.scene()

        if (
            scene is None
            or not hasattr(
                scene,
                "image_rect",
            )
            or scene.image_rect.isNull()
        ):
            return

        point_1 = self.mapToScene(
            self.line().p1()
        )

        point_2 = self.mapToScene(
            self.line().p2()
        )

        image_rectangle = scene.image_rect

        minimum_x = min(
            point_1.x(),
            point_2.x(),
        )

        maximum_x = max(
            point_1.x(),
            point_2.x(),
        )

        minimum_y = min(
            point_1.y(),
            point_2.y(),
        )

        maximum_y = max(
            point_1.y(),
            point_2.y(),
        )

        delta_x = 0.0
        delta_y = 0.0

        if minimum_x < image_rectangle.left():
            delta_x = (
                image_rectangle.left()
                - minimum_x
            )

        elif maximum_x > image_rectangle.right():
            delta_x = (
                image_rectangle.right()
                - maximum_x
            )

        if minimum_y < image_rectangle.top():
            delta_y = (
                image_rectangle.top()
                - minimum_y
            )

        elif maximum_y > image_rectangle.bottom():
            delta_y = (
                image_rectangle.bottom()
                - maximum_y
            )

        if (
            delta_x != 0.0
            or delta_y != 0.0
        ):
            self.moveBy(
                delta_x,
                delta_y,
            )

    def boundingRect(
        self,
    ) -> QRectF:
        margin = max(
            HANDLE_SIZE,
            self.pen().widthF() * 2,
        )

        return (
            super()
            .boundingRect()
            .adjusted(
                -margin,
                -margin,
                margin,
                margin,
            )
        )

    def shape(
        self,
    ) -> QPainterPath:
        path = QPainterPath()

        line = self.line()

        path.moveTo(
            line.p1()
        )

        path.lineTo(
            line.p2()
        )

        stroker = QPainterPathStroker()

        stroker.setWidth(
            max(
                12.0,
                self.pen().widthF() + 8.0,
            )
        )

        return stroker.createStroke(
            path
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()

        painter.setPen(
            self.pen()
        )

        painter.drawLine(
            self.line()
        )

        if self.isSelected():
            painter.setPen(
                QPen(
                    QColor(
                        "#0067B1"
                    ),
                    1.2,
                )
            )

            painter.setBrush(
                QColor(
                    "#FFFFFF"
                )
            )

            for rectangle in (
                self.handle_rectangles()
                .values()
            ):
                painter.drawEllipse(
                    rectangle
                )

        painter.restore()

    def finish_registered_operation(
        self,
    ) -> None:
        if not self.operation_registered:
            return

        self.operation_registered = False

        scene = self.scene()

        if (
            scene is not None
            and hasattr(
                scene,
                "finalize_change",
            )
        ):
            scene.finalize_change()


# =================================================================
# SETA
# =================================================================


class ResizableArrowItem(
    ResizableLineItem,
):
    def __init__(
        self,
        line: QLineF | None = None,
    ):
        super().__init__(
            line
        )

        self.setData(
            0,
            "arrow",
        )

    @property
    def start_point(
        self,
    ) -> QPointF:
        return self.line().p1()

    @property
    def end_point(
        self,
    ) -> QPointF:
        return self.line().p2()

    def set_points(
        self,
        start_point: QPointF,
        end_point: QPointF,
    ) -> None:
        self.prepareGeometryChange()

        self.setLine(
            QLineF(
                start_point,
                end_point,
            )
        )

        self.update()

    def update_path(
        self,
    ) -> None:
        self.prepareGeometryChange()

        self.update()

    def arrow_polygon(
        self,
    ) -> QPolygonF:
        line = self.line()

        if line.length() <= 0:
            return QPolygonF()

        stroke_width = float(
            self.data(3)
            or self.pen().widthF()
            or 3.0
        )

        head_length = max(
            14.0,
            min(
                30.0,
                stroke_width * 5.5,
            ),
        )

        head_half_width = max(
            6.0,
            min(
                17.0,
                stroke_width * 2.8,
            ),
        )

        direction_x = (
            line.dx()
            / line.length()
        )

        direction_y = (
            line.dy()
            / line.length()
        )

        perpendicular_x = (
            -direction_y
        )

        perpendicular_y = (
            direction_x
        )

        tip = line.p2()

        base_center = QPointF(
            tip.x()
            - direction_x
            * head_length,
            tip.y()
            - direction_y
            * head_length,
        )

        left = QPointF(
            base_center.x()
            + perpendicular_x
            * head_half_width,
            base_center.y()
            + perpendicular_y
            * head_half_width,
        )

        right = QPointF(
            base_center.x()
            - perpendicular_x
            * head_half_width,
            base_center.y()
            - perpendicular_y
            * head_half_width,
        )

        return QPolygonF(
            [
                tip,
                left,
                right,
            ]
        )

    def boundingRect(
        self,
    ) -> QRectF:
        line_rectangle = QRectF(
            self.line().p1(),
            self.line().p2(),
        ).normalized()

        polygon_rectangle = (
            self.arrow_polygon()
            .boundingRect()
        )

        rectangle = (
            line_rectangle
            .united(
                polygon_rectangle
            )
        )

        margin = max(
            HANDLE_SIZE,
            self.pen().widthF() * 3,
        )

        return rectangle.adjusted(
            -margin,
            -margin,
            margin,
            margin,
        )

    def shape(
        self,
    ) -> QPainterPath:
        line_path = QPainterPath()

        line_path.moveTo(
            self.line().p1()
        )

        line_path.lineTo(
            self.line().p2()
        )

        stroker = QPainterPathStroker()

        stroker.setWidth(
            max(
                12.0,
                self.pen().widthF() + 8.0,
            )
        )

        result = stroker.createStroke(
            line_path
        )

        polygon = self.arrow_polygon()

        if not polygon.isEmpty():
            polygon_path = QPainterPath()

            polygon_path.addPolygon(
                polygon
            )

            result = result.united(
                polygon_path
            )

        return result

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()

        color = normalized_color(
            str(
                self.data(4)
                or DEFAULT_COLOR
            )
        )

        pen = create_annotation_pen(
            color.name(),
            float(
                self.data(3)
                or 3.0
            ),
        )

        painter.setPen(
            pen
        )

        polygon = self.arrow_polygon()

        line = self.line()

        if polygon.count() >= 3:
            base_center = QPointF(
                (
                    polygon[1].x()
                    + polygon[2].x()
                )
                / 2,
                (
                    polygon[1].y()
                    + polygon[2].y()
                )
                / 2,
            )

            painter.drawLine(
                QLineF(
                    line.p1(),
                    base_center,
                )
            )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            painter.setBrush(
                color
            )

            painter.drawPolygon(
                polygon
            )

        else:
            painter.drawLine(
                line
            )

        if self.isSelected():
            painter.setPen(
                QPen(
                    QColor(
                        "#0067B1"
                    ),
                    1.2,
                )
            )

            painter.setBrush(
                QColor(
                    "#FFFFFF"
                )
            )

            for rectangle in (
                self.handle_rectangles()
                .values()
            ):
                painter.drawEllipse(
                    rectangle
                )

        painter.restore()


# =================================================================
# CENA
# =================================================================


class AnnotationScene(QGraphicsScene):
    tool_changed = Signal(str)

    history_changed = Signal(
        bool,
        bool,
    )

    annotations_changed = Signal()

    TOOL_SELECT = "select"
    TOOL_RECTANGLE = "rectangle"
    TOOL_CIRCLE = "circle"
    TOOL_LINE = "line"
    TOOL_ARROW = "arrow"
    TOOL_TEXT = "text"
    TOOL_MARKER = "marker"

    VALID_TOOLS = {
        TOOL_SELECT,
        TOOL_RECTANGLE,
        TOOL_CIRCLE,
        TOOL_LINE,
        TOOL_ARROW,
        TOOL_TEXT,
        TOOL_MARKER,
    }

    def __init__(self):
        super().__init__()

        self.current_tool = (
            self.TOOL_SELECT
        )

        self.start_pos: (
            QPointF
            | None
        ) = None

        self.temp_item = None

        self.annotation_items: list[
            QGraphicsItem
        ] = []

        self.background_item = None

        self.image_rect = QRectF()

        self.next_marker_index = 1

        self.default_font_size = 18
        self.default_stroke_width = 3.0
        self.default_color = DEFAULT_COLOR

        self.undo_stack: list[
            list[dict]
        ] = []

        self.redo_stack: list[
            list[dict]
        ] = []

        self.history_locked = False

    # =============================================================
    # FUNDO
    # =============================================================

    def set_background_item(
        self,
        item,
    ) -> None:
        self.background_item = item

        self.image_rect = QRectF(
            item.boundingRect()
        )

        self.setSceneRect(
            self.image_rect
        )

    # =============================================================
    # CONFIGURAÇÕES
    # =============================================================

    def set_tool(
        self,
        tool: str,
    ) -> None:
        if tool not in self.VALID_TOOLS:
            return

        self.current_tool = tool

        self.tool_changed.emit(
            tool
        )

    def reset_to_select(
        self,
    ) -> None:
        self.current_tool = (
            self.TOOL_SELECT
        )

        self.start_pos = None

        self.temp_item = None

        self.tool_changed.emit(
            self.TOOL_SELECT
        )

    def set_default_font_size(
        self,
        value: int,
    ) -> None:
        self.default_font_size = max(
            8,
            min(
                96,
                int(
                    value
                ),
            ),
        )

    def set_default_stroke_width(
        self,
        value: float,
    ) -> None:
        self.default_stroke_width = max(
            1.0,
            min(
                20.0,
                float(
                    value
                ),
            ),
        )

    def set_default_color(
        self,
        color: str,
    ) -> None:
        self.default_color = (
            normalized_color(
                color
            )
            .name()
            .upper()
        )

    def create_pen(
        self,
        stroke_width: float,
        color: str | None = None,
    ) -> QPen:
        return create_annotation_pen(
            color
            or self.default_color,
            stroke_width,
        )

    # =============================================================
    # POSIÇÃO
    # =============================================================

    def clamp_point_to_image(
        self,
        point: QPointF,
    ) -> QPointF:
        if self.image_rect.isNull():
            return point

        return QPointF(
            min(
                max(
                    point.x(),
                    self.image_rect.left(),
                ),
                self.image_rect.right(),
            ),
            min(
                max(
                    point.y(),
                    self.image_rect.top(),
                ),
                self.image_rect.bottom(),
            ),
        )

    # =============================================================
    # MOUSE
    # =============================================================

    def mousePressEvent(
        self,
        event,
    ) -> None:
        position = self.clamp_point_to_image(
            event.scenePos()
        )

        if (
            self.current_tool
            == self.TOOL_SELECT
        ):
            super().mousePressEvent(
                event
            )

            return

        if self.current_tool in {
            self.TOOL_RECTANGLE,
            self.TOOL_CIRCLE,
            self.TOOL_LINE,
            self.TOOL_ARROW,
        }:
            self.clearSelection()

            self.start_pos = position

            if (
                self.current_tool
                == self.TOOL_RECTANGLE
            ):
                item = ResizableRectangleItem()

            elif (
                self.current_tool
                == self.TOOL_CIRCLE
            ):
                item = ResizableEllipseItem()

            elif (
                self.current_tool
                == self.TOOL_LINE
            ):
                item = ResizableLineItem(
                    QLineF(
                        position,
                        position,
                    )
                )

            else:
                item = ResizableArrowItem(
                    QLineF(
                        position,
                        position,
                    )
                )

            item.setData(
                3,
                self.default_stroke_width,
            )

            item.setData(
                4,
                self.default_color,
            )

            item.setPen(
                self.create_pen(
                    self.default_stroke_width,
                    self.default_color,
                )
            )

            self.addItem(
                item
            )

            self.temp_item = item

            return

        if self.current_tool in {
            self.TOOL_TEXT,
            self.TOOL_MARKER,
        }:
            self.save_history_state()

            self.clearSelection()

            if (
                self.current_tool
                == self.TOOL_MARKER
            ):
                content = (
                    f"{self.next_marker_index:02d}"
                )

            else:
                content = "Texto"

            item = QGraphicsSimpleTextItem(
                content
            )

            font = item.font()

            font.setPointSize(
                self.default_font_size
            )

            font.setBold(
                self.current_tool
                == self.TOOL_MARKER
            )

            item.setFont(
                font
            )

            item.setPos(
                position
            )

            item.setBrush(
                normalized_color(
                    self.default_color
                )
            )

            item.setData(
                0,
                self.current_tool,
            )

            item.setData(
                1,
                (
                    content
                    if (
                        self.current_tool
                        == self.TOOL_MARKER
                    )
                    else None
                ),
            )

            item.setData(
                2,
                self.default_font_size,
            )

            item.setData(
                3,
                self.default_stroke_width,
            )

            item.setData(
                4,
                self.default_color,
            )

            self.configure_text_item(
                item
            )

            self.addItem(
                item
            )

            self.annotation_items.append(
                item
            )

            if (
                self.current_tool
                == self.TOOL_MARKER
            ):
                self.next_marker_index += 1

            item.setSelected(
                True
            )

            self.finalize_change()

            self.reset_to_select()

            return

        super().mousePressEvent(
            event
        )

    def mouseMoveEvent(
        self,
        event,
    ) -> None:
        if (
            self.temp_item is not None
            and self.start_pos is not None
        ):
            current_position = (
                self.clamp_point_to_image(
                    event.scenePos()
                )
            )

            if isinstance(
                self.temp_item,
                (
                    ResizableRectangleItem,
                    ResizableEllipseItem,
                ),
            ):
                self.temp_item.setRect(
                    QRectF(
                        self.start_pos,
                        current_position,
                    ).normalized()
                )

            elif isinstance(
                self.temp_item,
                ResizableArrowItem,
            ):
                self.temp_item.set_points(
                    self.start_pos,
                    current_position,
                )

            elif isinstance(
                self.temp_item,
                ResizableLineItem,
            ):
                self.temp_item.setLine(
                    QLineF(
                        self.start_pos,
                        current_position,
                    )
                )

            return

        super().mouseMoveEvent(
            event
        )

    def mouseReleaseEvent(
        self,
        event,
    ) -> None:
        if self.temp_item is not None:
            item = self.temp_item

            annotation_type = (
                item.data(0)
            )

            valid = True

            if annotation_type in {
                "rectangle",
                "circle",
            }:
                rectangle = item.rect()

                valid = (
                    rectangle.width()
                    >= MIN_SHAPE_SIZE
                    and rectangle.height()
                    >= MIN_SHAPE_SIZE
                )

            elif annotation_type in {
                "line",
                "arrow",
            }:
                valid = (
                    item.line().length()
                    >= MIN_LINE_LENGTH
                )

            if valid:
                self.save_history_state()

                self.annotation_items.append(
                    item
                )

                item.setSelected(
                    True
                )

                self.finalize_change()

            else:
                self.removeItem(
                    item
                )

            self.temp_item = None
            self.start_pos = None

            self.reset_to_select()

            return

        super().mouseReleaseEvent(
            event
        )

    # =============================================================
    # ITENS
    # =============================================================

    def configure_text_item(
        self,
        item,
    ) -> None:
        item.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        item.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )

        item.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

    # =============================================================
    # EXCLUSÃO
    # =============================================================

    def delete_selected(
        self,
    ) -> None:
        selected = [
            item
            for item in self.selectedItems()
            if item in self.annotation_items
        ]

        if not selected:
            return

        self.save_history_state()

        for item in selected:
            self.annotation_items.remove(
                item
            )

            self.removeItem(
                item
            )

        self.recalculate_next_marker()

        self.finalize_change()

    def clear_annotations(
        self,
        register_history: bool = True,
    ) -> None:
        if (
            register_history
            and self.annotation_items
        ):
            self.save_history_state()

        for item in list(
            self.annotation_items
        ):
            self.removeItem(
                item
            )

        self.annotation_items.clear()

        self.next_marker_index = 1

        if register_history:
            self.finalize_change()

    # =============================================================
    # TECLADO
    # =============================================================

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ) -> None:
        if (
            event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
            and event.key()
            == Qt.Key.Key_Z
        ):
            self.undo()

            return

        if (
            event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
            and event.key()
            == Qt.Key.Key_Y
        ):
            self.redo()

            return

        if event.key() in {
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace,
        }:
            self.delete_selected()

            return

        if event.key() == Qt.Key.Key_Escape:
            self.reset_to_select()

            self.clearSelection()

            return

        super().keyPressEvent(
            event
        )

    # =============================================================
    # HISTÓRICO
    # =============================================================

    def save_history_state(
        self,
    ) -> None:
        if self.history_locked:
            return

        self.undo_stack.append(
            self.serialize_annotations()
        )

        if len(self.undo_stack) > 50:
            self.undo_stack.pop(
                0
            )

        self.redo_stack.clear()

        self.emit_history_state()

    def undo(
        self,
    ) -> None:
        if not self.undo_stack:
            return

        current = self.serialize_annotations()

        previous = self.undo_stack.pop()

        self.redo_stack.append(
            current
        )

        self.restore_annotations(
            previous
        )

        self.emit_history_state()

    def redo(
        self,
    ) -> None:
        if not self.redo_stack:
            return

        current = self.serialize_annotations()

        next_state = self.redo_stack.pop()

        self.undo_stack.append(
            current
        )

        self.restore_annotations(
            next_state
        )

        self.emit_history_state()

    def reset_history(
        self,
    ) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()

        self.emit_history_state()

    def emit_history_state(
        self,
    ) -> None:
        self.history_changed.emit(
            bool(
                self.undo_stack
            ),
            bool(
                self.redo_stack
            ),
        )

    def finalize_change(
        self,
    ) -> None:
        self.annotations_changed.emit()

        self.emit_history_state()

    # =============================================================
    # SERIALIZAÇÃO
    # =============================================================

    def serialize_annotations(
        self,
    ) -> list[dict]:
        result = []

        for item in self.annotation_items:
            annotation_type = str(
                item.data(0)
            )

            color = str(
                item.data(4)
                or DEFAULT_COLOR
            ).upper()

            stroke_width = float(
                item.data(3)
                or 3.0
            )

            position = item.pos()

            if annotation_type in {
                "rectangle",
                "circle",
            }:
                rectangle = item.rect()

                result.append(
                    {
                        "annotation_type":
                            annotation_type,

                        "x":
                            rectangle.x()
                            + position.x(),

                        "y":
                            rectangle.y()
                            + position.y(),

                        "width":
                            rectangle.width(),

                        "height":
                            rectangle.height(),

                        "end_x":
                            None,

                        "end_y":
                            None,

                        "text":
                            None,

                        "marker_text":
                            None,

                        "font_size":
                            self.default_font_size,

                        "stroke_width":
                            stroke_width,

                        "color":
                            color,
                    }
                )

            elif annotation_type in {
                "line",
                "arrow",
            }:
                line = item.line()

                result.append(
                    {
                        "annotation_type":
                            annotation_type,

                        "x":
                            line.x1()
                            + position.x(),

                        "y":
                            line.y1()
                            + position.y(),

                        "end_x":
                            line.x2()
                            + position.x(),

                        "end_y":
                            line.y2()
                            + position.y(),

                        "width":
                            0.0,

                        "height":
                            0.0,

                        "text":
                            None,

                        "marker_text":
                            None,

                        "font_size":
                            self.default_font_size,

                        "stroke_width":
                            stroke_width,

                        "color":
                            color,
                    }
                )

            elif annotation_type in {
                "text",
                "marker",
            }:
                result.append(
                    {
                        "annotation_type":
                            annotation_type,

                        "x":
                            position.x(),

                        "y":
                            position.y(),

                        "width":
                            0.0,

                        "height":
                            0.0,

                        "end_x":
                            None,

                        "end_y":
                            None,

                        "text":
                            (
                                item.text()
                                if annotation_type
                                == "text"
                                else None
                            ),

                        "marker_text":
                            (
                                str(
                                    item.data(1)
                                    or item.text()
                                )
                                if annotation_type
                                == "marker"
                                else None
                            ),

                        "font_size":
                            int(
                                item.data(2)
                                or 18
                            ),

                        "stroke_width":
                            stroke_width,

                        "color":
                            color,
                    }
                )

        return result

    def restore_annotations(
        self,
        annotations_data: list[dict],
    ) -> None:
        self.history_locked = True

        try:
            self.clear_annotations(
                register_history=False
            )

            for data in annotations_data:
                self.add_annotation_from_data(
                    data
                )

            self.recalculate_next_marker()

            self.clearSelection()

            self.reset_to_select()

        finally:
            self.history_locked = False

        self.annotations_changed.emit()

    # =============================================================
    # RECRIAR ITEM
    # =============================================================

    def add_annotation_from_data(
        self,
        data: dict,
    ):
        annotation_type = str(
            data.get(
                "annotation_type",
                "",
            )
        ).lower()

        color = str(
            data.get(
                "color",
                DEFAULT_COLOR,
            )
            or DEFAULT_COLOR
        ).upper()

        stroke_width = float(
            data.get(
                "stroke_width",
                3.0,
            )
            or 3.0
        )

        item = None

        if annotation_type == "rectangle":
            item = ResizableRectangleItem(
                QRectF(
                    float(data.get("x", 0)),
                    float(data.get("y", 0)),
                    float(data.get("width", 0)),
                    float(data.get("height", 0)),
                )
            )

        elif annotation_type == "circle":
            item = ResizableEllipseItem(
                QRectF(
                    float(data.get("x", 0)),
                    float(data.get("y", 0)),
                    float(data.get("width", 0)),
                    float(data.get("height", 0)),
                )
            )

        elif annotation_type == "line":
            item = ResizableLineItem(
                QLineF(
                    float(data.get("x", 0)),
                    float(data.get("y", 0)),
                    float(data.get("end_x", 0)),
                    float(data.get("end_y", 0)),
                )
            )

        elif annotation_type == "arrow":
            item = ResizableArrowItem(
                QLineF(
                    float(data.get("x", 0)),
                    float(data.get("y", 0)),
                    float(data.get("end_x", 0)),
                    float(data.get("end_y", 0)),
                )
            )

        elif annotation_type in {
            "text",
            "marker",
        }:
            content = (
                str(
                    data.get(
                        "text",
                        "Texto",
                    )
                    or "Texto"
                )
                if annotation_type
                == "text"
                else str(
                    data.get(
                        "marker_text",
                        "01",
                    )
                    or "01"
                )
            )

            item = QGraphicsSimpleTextItem(
                content
            )

            item.setPos(
                float(data.get("x", 0)),
                float(data.get("y", 0)),
            )

            font = item.font()

            font.setPointSize(
                int(
                    data.get(
                        "font_size",
                        18,
                    )
                    or 18
                )
            )

            font.setBold(
                annotation_type
                == "marker"
            )

            item.setFont(
                font
            )

            item.setBrush(
                normalized_color(
                    color
                )
            )

            item.setData(
                1,
                (
                    content
                    if annotation_type
                    == "marker"
                    else None
                ),
            )

            item.setData(
                2,
                int(
                    data.get(
                        "font_size",
                        18,
                    )
                    or 18
                ),
            )

            self.configure_text_item(
                item
            )

        if item is None:
            return None

        item.setData(
            0,
            annotation_type,
        )

        item.setData(
            3,
            stroke_width,
        )

        item.setData(
            4,
            color,
        )

        if annotation_type in {
            "rectangle",
            "circle",
            "line",
            "arrow",
        }:
            item.setPen(
                self.create_pen(
                    stroke_width,
                    color,
                )
            )

        self.addItem(
            item
        )

        self.annotation_items.append(
            item
        )

        return item

    def recalculate_next_marker(
        self,
    ) -> None:
        highest = 0

        for item in self.annotation_items:
            if item.data(0) != "marker":
                continue

            text = str(
                item.data(1)
                or ""
            ).strip()

            if text.isdigit():
                highest = max(
                    highest,
                    int(
                        text
                    ),
                )

        self.next_marker_index = highest + 1
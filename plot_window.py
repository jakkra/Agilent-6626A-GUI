from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class PlotWindow(QWidget):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Plot of channel {self.channel}")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout()
        self.graphicsView = QGraphicsView()
        layout.addWidget(self.graphicsView)
        self.setLayout(layout)

        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.plotWidget = pg.PlotWidget()
        self.plotWidget.setLabel("bottom", "Time")
        self.plotWidget.setTitle(f"Output current channel {self.channel}")
        self.scene.addWidget(self.plotWidget)

    def update_plot(self, voltage_data, current_data):
        self.plotWidget.clear()
        max_value = max(voltage_data)
        min_value = min(voltage_data)
        range_padding = 0.3 * (max_value - min_value)
        y_min = min_value - range_padding
        y_max = max_value + range_padding

        if max_value >= 1:
            self.plotWidget.setLabel("left", "Current (A)")
            self.plotWidget.plot(
                voltage_data, pen="b", symbol="o", symbolSize=5, symbolBrush=("g")
            )
        elif max_value >= 0.001:
            self.plotWidget.setLabel("left", "Current (mA)")
            y_min *= 1000
            y_max *= 1000
            self.plotWidget.plot(
                [x * 1000 for x in voltage_data],
                pen="g",
                symbol="o",
                symbolSize=5,
                symbolBrush=("g"),
            )
        else:
            self.plotWidget.setLabel("left", "Current (uA)")
            y_min *= 1000000
            y_max *= 1000000
            self.plotWidget.plot(
                [x * 1000000 for x in voltage_data],
                pen="g",
                symbol="o",
                symbolSize=5,
                symbolBrush=("g"),
            )

        # self.plotWidget.setYRange(y_min, y_max)

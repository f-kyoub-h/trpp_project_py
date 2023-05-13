import sys
import psycopg2
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from SentimentModel import SentimentModel
from math import ceil
from config import host, user, password, dbname, port


def create_pie_chart(data: object, listBool) -> QWidget:
    # Создание серии диаграммы
    series = QPieSeries()
    series.setHoleSize(0.5)

    # Добавление данных в серию
    for label, (value, color) in data.items():
        _slice = QPieSlice(label, value)
        _slice.setBrush(color)
        series.append(_slice)

    # Создание диаграммы
    chart = QChart()
    chart.addSeries(series)
    chart.setTitleFont(QFont("Times font", 20))
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.setAnimationEasingCurve(QEasingCurve.InCurve)
    chart.setAnimationDuration(2500)
    for i in range(3):
        chart.legend().markers()[i].setFont(QFont("Times font", 15))

    chart.setBackgroundVisible(False)
    if listBool:
        chart.setTitle(f"Диаграмма оценки")
    else:
        chart.legend().hide()

    # Создание виджета для отображения диаграммы
    chart_view = QChartView(chart)

    return chart_view


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("mainWindow.ui", self)
        self.pushButton.clicked.connect(self.go_to_screen2)
        self.pushButton.setStyleSheet("background-color : lightgrey")
        self.resButton.setEnabled(False)
        self.resButton.clicked.connect(self.go_to_screen3)
        self.resButton.setStyleSheet("background-color : lightgrey")

    def go_to_screen2(self):
        screen2.init_ui(self.plainTextEdit.toPlainText())
        self.plainTextEdit.clear()
        self.resButton.setEnabled(True)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def go_to_screen3(self):
        screen3.get_last_res()
        self.plainTextEdit.clear()
        widget.setCurrentIndex(widget.currentIndex() + 2)


class Screen2(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data")
        self.layout = QVBoxLayout()

        self.pie_chart = QWidget()
        self.pie_button = QPushButton("Return")

    def init_ui(self, text_to_analyze: str):
        self.pie_chart = QWidget()
        post_text = text_to_analyze.lower()
        sent_model = SentimentModel()
        predictions = sent_model.predict(post_text)
        results = [float('{:.3f}'.format(predictions[_type] * 100)) for
                   _type in ["POSITIVE", "NEUTRAL", "NEGATIVE"]]
        pred_str = f"POSITIVE: {results[0]}%\nNEUTRAL: {results[1]}%\nNEGATIVE: {results[2]}%"

        # формирование и выполнение запроса
        query = "INSERT INTO story (text, positive, neutral, negative)" \
                f" VALUES ('{text_to_analyze}', {results[0]}, {results[1]}, {results[2]})"
        curs.execute(query)
        # "подтверждение" запроса
        conn.commit()

        self.pie_chart = create_pie_chart({"POSITIVE": (results[0], QtGui.QColor("#32CD32")),
                                           "NEUTRAL": (results[1], QtGui.QColor("#F5D572")),
                                           "NEGATIVE": (results[2], QtGui.QColor("#FF3E3E"))}, listBool=True)
        self.pie_chart.setFont(QFont("Times font", 20))
        self.pie_button.clicked.connect(self.go_to_main_screen)

        self.pie_chart.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.pie_chart)
        self.layout.addWidget(self.pie_button)

        self.setLayout(self.layout)

    def go_to_main_screen(self):
        self.layout.removeWidget(self.pie_chart)
        self.layout.removeWidget(self.pie_button)
        widget.setCurrentIndex(widget.currentIndex() - 1)

    # вывод всех текстов за одну сессию (кроме последнего)
    def get_table(self):
        query = "SELECT ROW_NUMBER() over() as number,* FROM story ORDER BY number DESC"
        curs.execute(query)
        result_table = curs.fetchall()
        for row in result_table:
            print(row[1:])

    # очистка бд при удалении объекта
    def __del__(self):
        self.get_table()
        query = "DELETE FROM story *"
        curs.execute(query)
        conn.commit()


class Screen3(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
    def get_last_res(self):
        query = "SELECT ROW_NUMBER() over() as number,* FROM story ORDER BY number DESC"
        curs.execute(query)
        result_table = curs.fetchall()
        for row in result_table:
            line_layout = QHBoxLayout()
            row_pie = create_pie_chart({"POSITIVE": (row[3], QtGui.QColor("#32CD32")),
                                        "NEUTRAL": (row[4], QtGui.QColor("#F5D572")),
                                        "NEGATIVE": (row[2], QtGui.QColor("#FF3E3E"))}, listBool=False)

            pred_str = f"POSITIVE: {row[3]}%\nNEUTRAL: {row[4]}%\nNEGATIVE: {row[2]}%"
            line_layout.addWidget(row_pie)
            text_label = QLabel()
            text_label.setAlignment(Qt.AlignCenter)
            stat_label = QLabel(pred_str)
            stat_label.setAlignment(Qt.AlignCenter)
            text_label.setText(row[1])
            line_layout.addWidget(stat_label)
            line_layout.addWidget(text_label)
            self.layout.addLayout(line_layout)
        self.setLayout(self.layout)



# подключение к бд
conn = psycopg2.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    dbname=dbname,
)
curs = conn.cursor()

app = QApplication(sys.argv)
widget = QStackedWidget()
main_window = MainWindow()
screen2 = Screen2()
screen3 = Screen3()

widget.addWidget(main_window) # 0
widget.addWidget(screen2) # 1
widget.addWidget(screen3) # 2

widget.setWindowIcon(QIcon("minimalistic_icon.png"))
widget.setWindowTitle("QRage")
widget.show()
sys.exit(app.exec_())

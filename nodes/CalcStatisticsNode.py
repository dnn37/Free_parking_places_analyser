from collections import deque
import numpy as np

from elements.FrameElement import FrameElement
from elements.VideoEndBreakElement import VideoEndBreakElement
from utils_local.utils import profile_time


class CalcStatisticsNode:
    """Модуль для расчета загруженности парковки (вычисление статистик)"""

    def __init__(self, config: dict) -> None:
        config_general = config["general"]

        self.time_buffer_analytics = config_general[
            "buffer_analytics"
        ]  # размер времени буфера в минутах
        self.min_time_life_track = config_general[
            "min_time_life_track"
        ]  # минимальное время жизни трека в сек
        self.count_parking_buffer_frames = config_general["count_parking_buffer_frames"]
        self.parking_buffer = deque(maxlen=self.count_parking_buffer_frames)  # создали буфер значений количества свободных мест
         #FIXME тк пока что только для 1 парковки
        self.road1_max = config_general["road1_max"] #максимальная вместимость парковки1
        

    @profile_time 
    def process(self, frame_element: FrameElement) -> FrameElement:
        # Выйти из обработки если это пришел VideoEndBreakElement а не FrameElement
        if isinstance(frame_element, VideoEndBreakElement):
            return frame_element
        assert isinstance(
            frame_element, FrameElement
        ), f"CalcStatisticsNode | Неправильный формат входного элемента {type(frame_element)}"

        buffer_tracks = frame_element.buffer_tracks

        info_dictionary = {}  # информация по текущему кадру
        
        parking_activity = {
            1: [0,self.road1_max],
            
        }  # всего 1 дорога (занулим стартовое значение)

        # Посчитаем число машин которые давно живут и имеют значения парковки
        
       
        for _, track_element in buffer_tracks.items():
            if (
                track_element.timestamp_last - track_element.timestamp_init_road
                > self.min_time_life_track #трек не случайный для парковки !!! здесь отсекаются случайные машины
                and track_element.start_road is not None
            ):
                key = track_element.start_road
                parking_activity[key][0] += 1

        self.parking_buffer.append(max((parking_activity[1][1] - parking_activity[1][0]),0))# добавили число свободных мест в текущем кадре на парковке 1
        # Переведем значения в число свободных мест на парковке 
    
        parking_activity[1][0] = round(np.mean(self.parking_buffer)) # число свободных мест FIXME рассчитано на 1 дорогу
        
        info_dictionary[1] = max(parking_activity[1][0],0)
        # Запись результатов обработки:
        frame_element.info = info_dictionary

        return frame_element

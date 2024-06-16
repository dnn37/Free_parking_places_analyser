import logging

from elements.FrameElement import FrameElement
from elements.TrackElement import TrackElement
from elements.VideoEndBreakElement import VideoEndBreakElement
from utils_local.utils import profile_time, intersects_central_point

logger = logging.getLogger("buffer_tracks")


class TrackerInfoUpdateNode:
    """Модуль обновления актуальных треков"""

    def __init__(self, config: dict) -> None:
        config_general = config["general"]

        self.size_buffer_analytics = (
            config_general["buffer_analytics"] * 60
        )  # число секунд в буфере аналитики
        # добавим мин времени жизни чтобы при расчете статистики были именно
        # машины за последие buffer_analytics минут(то есть если трек давно не появлялся - удаляем):
        self.size_buffer_analytics += config_general["min_time_life_track"]
        self.buffer_tracks = {}  # Буфер актуальных треков

    @profile_time 
    def process(self, frame_element: FrameElement) -> FrameElement:
        # Выйти из обработки если это пришел VideoEndBreakElement а не FrameElement
        if isinstance(frame_element, VideoEndBreakElement):
            return frame_element
        assert isinstance(
            frame_element, FrameElement
        ), f"TrackerInfoUpdateNode | Неправильный формат входного элемента {type(frame_element)}"

        id_list = frame_element.id_list

        for i, id in enumerate(id_list):
            start_road_id = intersects_central_point(
                tracked_xyxy=frame_element.tracked_xyxy[i],
                polygons=frame_element.roads_info,
            )
            # Обновление или создание нового трека
            if id not in self.buffer_tracks:
                # Создаем новый ключ
                self.buffer_tracks[id] = TrackElement(
                    id=id,
                    timestamp_first=frame_element.timestamp,
                )
            else:
                # Обновление времени последнего обнаружения (last)
                self.buffer_tracks[id].update(frame_element.timestamp)

            # Поиск пересечения с полигонами парковок
            
           #определили принадлежит ли машина парковке
                
                # Проверка того, что отработка функции дала актуальный номер дороги:
            if self.buffer_tracks[id].start_road is None and start_road_id is not None \
                  and self.buffer_tracks[id].timestamp_init_road is None:#начальное время трека еще не инициализироалось
                # Тогда сохраняем время такого момента: FIXME для нескольких парковок нужна более сложная логика
                self.buffer_tracks[id].timestamp_init_road = frame_element.timestamp
            self.buffer_tracks[id].start_road = start_road_id # в любом случае меняем start_road_id        

         #FIXME надо все проверять и если дорога стала None - ставить none
         #далее удалять все с долгим временем жизни и None
        # Удаление старых айдишников из словаря если их время жизни > size_buffer_analytics
            
        keys_to_remove = []
        for key, track_element in sorted(self.buffer_tracks.items()):  # Сортируем элементы по ключу
            if self.buffer_tracks[id].start_road is not None or self.buffer_tracks[id].timestamp_init_road is not None or ((frame_element.timestamp - track_element.timestamp_first) < self.size_buffer_analytics):
                break  # Прерываем цикл, если значение time_delta меньше check
            else:
                keys_to_remove.append(key)  # Добавляем ключ для удаления (трек лежит вне парковки и является давнешним )

        for key in keys_to_remove:
            self.buffer_tracks.pop(key)  # Удаляем элемент из словаря
            logger.info(f"Removed tracker with key {key}")

        # Запись результатов обработки:
        frame_element.buffer_tracks = self.buffer_tracks

        return frame_element

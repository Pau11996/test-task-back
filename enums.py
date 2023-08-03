from enum import Enum


class TaskStatus(str, Enum):
    COMPLETED = 'completed'
    IN_PROGRESS = 'inprogress'
    ALL = 'all'

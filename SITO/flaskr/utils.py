import datetime

from SITO.flaskr.models import Habits


def check_habits(uuid):
    time = datetime.datetime.now()
    day_slot = set_day_slot(time)
    habit = Habits.query.filter_by(dog=uuid).first()
    if habit:
        mean_time = getattr(habit, day_slot)
        if mean_time:
            if mean_time.hour == time.hour and time.minute - 15 < mean_time.minute < time.minute + 15:
                print("Passeggiata di routine")
                return True
        else:
            return False
    else:
        return False


def set_day_slot(time):
    if 00 < time.hour <= 12:
        day_slot = "morning"
    elif 12 < time.hour <= 18:
        day_slot = "afternoon"
    elif 18 < time.hour <= 23:
        day_slot = "evening"
    else:
        day_slot = None
    return str(day_slot)

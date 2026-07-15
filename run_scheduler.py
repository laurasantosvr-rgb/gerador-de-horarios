from src.services.excel_reader import ExcelReader
from src.services.data_validator import DataValidator
from src.services.data_loader import DataLoader
from src.services.schedule_exporter import ScheduleExporter
from src.scheduler.monthly_scheduler import MonthlyScheduler
from src.services.schedule_importer import ScheduleImporter
from src.services.history_manager import HistoryManager


def gerar_horario(
    excel_file,
    start_date,
    end_date,
    previous_schedule_file=None,
):

    data = ExcelReader(excel_file).load()

    DataValidator().validate(data)

    hotel = DataLoader(data).load()

    history = HistoryManager()
    previous_schedule = None

    if previous_schedule_file is not None:

        previous_schedule = ScheduleImporter().load(
            previous_schedule_file,
            hotel,
        )

        history.update(
            previous_schedule,
            hotel,
            previous_schedule_file,
        )

    scheduler = MonthlyScheduler()

    schedule = scheduler.generate(
        hotel,
        history,
        previous_schedule,
        start_date,
        end_date,
    )

    schedule.validate_day_offs()

    output = "Horario_Gerado.xlsx"

    ScheduleExporter().export(
        schedule,
        hotel,
        output,
    )

    return output
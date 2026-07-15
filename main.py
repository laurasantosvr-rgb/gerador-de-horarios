from src.services.excel_reader import ExcelReader
from src.services.data_validator import DataValidator
from src.services.data_loader import DataLoader
from src.services.schedule_exporter import ScheduleExporter
from src.scheduler.monthly_scheduler import MonthlyScheduler
from datetime import date
from src.services.schedule_importer import ScheduleImporter
from src.services.history_manager import HistoryManager

def main():

    import traceback

    reader = ExcelReader()

    try:

        data = reader.load()
        validator = DataValidator()
        validator.validate(data)
        hotel = DataLoader(data).load()

        start_date = date(
            2026,
            6,
            29,
        )

        end_date = date(
            2026,
            8,
            2,
        )

        history = HistoryManager()
        
        previous_schedule = None

        previous_schedule_path = None
        # No futuro virá da interface

        if previous_schedule_path:

            previous_schedule = ScheduleImporter().load(
                previous_schedule_path,
                hotel,
            )

            history.update(
                previous_schedule,
                hotel,
                previous_schedule_path,
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

        for assignment in schedule.assignments:
            print(
        assignment.day,
        assignment.unit,
        assignment.employee_id,
    )

        exporter = ScheduleExporter()

        exporter.export(
            schedule,
            hotel,
            "Horario_Julho_2026.xlsx",
        )

        print(len(hotel.substitutions))

        for s in hotel.substitutions:
            print(
                s.employee_id,
                s.substitute_id,
                s.priority,
            )

        print("\n✅ Horário exportado com sucesso!")

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()

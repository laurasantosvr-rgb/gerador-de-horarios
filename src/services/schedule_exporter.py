from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.styles import PatternFill
from openpyxl.styles import Border, Side
from openpyxl.utils import get_column_letter
from datetime import timedelta

from src.models import day_off, schedule

class ScheduleExporter:
    """Exporta o horário para Excel."""

    def export(
        self,
        schedule,
        hotel,
        filename: str,
    ) -> None:

        workbook = Workbook()

        sheet = workbook.active
        sheet.title = "Horário"

        day_columns = self._create_header(
            sheet,
            schedule,
        )

        employee_rows = self._write_employees(
            sheet,
            hotel,
        )

        self._highlight_weekends(
            sheet,
            day_columns,
        )

        self._fill_schedule(
            sheet,
            schedule,
            hotel,
            employee_rows,
            day_columns,
        )

        self._format_sheet(
            sheet,
        )

        workbook.save(filename)

    def _create_header(
        self,
        sheet,
        schedule,
    ):
        """
    Cria o cabeçalho do horário.
    """

        header = [
            "Colaborador",
        ]

        days = []

        current_day = schedule.start_date

        while current_day <= schedule.end_date:

            days.append(current_day)

            current_day += timedelta(days=1)


        weekdays = [
            "Seg",
            "Ter",
            "Qua",
            "Qui",
            "Sex",
            "Sáb",
            "Dom",
        ]

        day_columns = {}

        column = 2

        for day in days:

            header.append(day)

            day_columns[day] = column

            column += 1

        sheet.append(header)

        for day, column in day_columns.items():

            cell = sheet.cell(
                row=1,
                column=column,
            )

            cell.number_format = "DD-MM-YYYY"

            if day.weekday() >= 5:

                cell.fill = PatternFill(
                    fill_type="solid",
                    start_color="D9D9D9",
                    end_color="D9D9D9",
                )

            else:

                cell.fill = PatternFill(
                    fill_type="solid",
                    start_color="E7E6E6",
                    end_color="E7E6E6",
                )

            cell.font = Font(
                bold=True,
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

        sheet.row_dimensions[1].height = 25

        # Coluna "Colaborador"
        sheet["A1"].fill = PatternFill(
            fill_type="solid",
            start_color="D9D9D9",
            end_color="D9D9D9",
        )

        return day_columns

    
    def _highlight_weekends(
        self,
        sheet,
        day_columns,
    ):
        """
    Destaca as colunas de sábado e domingo.
    """

        weekend_fill = PatternFill(
            fill_type="solid",
            start_color="F2F2F2",
            end_color="F2F2F2",
        )

        for day, column in day_columns.items():

            if day.weekday() >= 5:

                for row in range(
                    1,
                    sheet.max_row + 1,
                ):

                    sheet.cell(
                        row=row,
                        column=column,
                    ).fill = weekend_fill

    def _write_employees(
        self,
        sheet,
        hotel,
    ):
        """
    Escreve os colaboradores agrupados
    pela unidade principal.

    Devolve:
        {employee_id: linha}
    """

        employee_rows = {}

        row = 2

        units = sorted(
            hotel.units.values(),
            key=lambda unit: unit.nome,
        )

        for unit in units:

            employees = sorted(
                [
                    employee
                    for employee in hotel.employees.values()
                    if employee.unidade_principal == unit.nome
                ],
                key=lambda employee: employee.nome,
            )

            for employee in employees:

                employee_rows[
                    employee.id
                ] = row

                cell = sheet.cell(
                    row=row,
                    column=1,
                )

                cell.value = employee.nome

                cell.fill = self._unit_fill(
                    employee.unidade_principal,
                )

                cell.font = Font(
                    bold=True,
                )

                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                )

                row += 1

        return employee_rows
    
    def _unit_fill(
        self,
        unit_name,
    ):
        """
    Devolve a cor associada à unidade.
    """

        colors = {
            "HM": "DDEBF7",   # azul claro
            "B": "E2F0D9",    # verde claro
            "JP": "F4CCCC",    # vermelho claro
            "AP": "FCE4D6",    # laranja claro
            "Lavandaria": "E4D7F5",    # lilás claro
        }

        return PatternFill(
            fill_type="solid",
            start_color=colors.get(
                unit_name,
                "FFFFFF",
            ),
            end_color=colors.get(
                unit_name,
                "FFFFFF",
            ),
        )
    
    def _fill_schedule(
        self,
        sheet,
        schedule,
        hotel,
        employee_rows,
        day_columns,
    ):
        """
    Preenche o horário dos colaboradores.
    """

        print("=" * 50)
        print("Período do horário")
        print(schedule.start_date)
        print(schedule.end_date)
        print("=" * 50)

    # ==========================
    # Trabalho
    # ==========================

        for assignment in schedule.assignments:

            employee = hotel.employees[assignment.employee_id]

            row = employee_rows[
                assignment.employee_id
            ]

            column = day_columns[
                assignment.day
            ]       

            cell = sheet.cell(
                row=row,
                column=column,
            )


            text = (
                f"{assignment.unit}"
            )


            if cell.value:

                cell.value += " / " + text

            else:

                cell.value = text

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        # ==========================
        # Folgas
        # ==========================

        for day_off in schedule.day_offs:

            row = employee_rows[
                day_off.employee_id
            ]

            print("Intervalo do horário:")
            print(min(day_columns.keys()), "->", max(day_columns.keys()))

            print("Folga:")
            print(day_off.day)
            if day_off.day not in day_columns:

                print("\n===== ERRO =====")
                print("Folga fora do intervalo:", day_off.day)
                print(
                    "Intervalo disponível:",
                    min(day_columns.keys()),
                    "->",
                    max(day_columns.keys())
                )

                raise KeyError(day_off.day)

            column = day_columns[
                day_off.day
            ]
            cell = sheet.cell(
                row=row,
                column=column,
            )

            cell.value = "F"

            cell.fill = PatternFill(
                fill_type="solid",
                start_color="FFF2CC",
                end_color="FFF2CC",
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

            translation = {
                0: "segunda",
                1: "terça",
                2: "quarta",
                3: "quinta",
                4: "sexta",
                5: "sábado",
                6: "domingo",
            }

        for fixed_day in hotel.fixed_days_off:

            row = employee_rows[
                fixed_day.employee_id
            ]

            for day, column in day_columns.items():

                if (
                    translation[day.weekday()]
                    != fixed_day.weekday
                ):
                    continue

                cell = sheet.cell(
                    row=row,
                    column=column,
                )
                 
                cell.value = "F"

                cell.fill = PatternFill(
                    fill_type="solid",
                    start_color="FFF2CC",
                    end_color="FFF2CC",
                )

                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                )

        for employee in hotel.employees.values():

            if employee.trabalha_fins_de_semana:
                continue

            row = employee_rows[employee.id]

            for day, column in day_columns.items():

                if day.weekday() not in (5, 6):
                    continue

                cell = sheet.cell(
                    row=row,
                    column=column,
                )

                cell.value = "F"

                cell.fill = PatternFill(
                    fill_type="solid",
                    start_color="FFF2CC",
                    end_color="FFF2CC",
                )

                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                )   

        # ==========================
        # Férias
        # ==========================

        ferias_fill = PatternFill(
            fill_type="solid",
            start_color="FCE4EC",   # rosa bebé
            end_color="FCE4EC",
        )

        for vacation in hotel.vacations:

            row = employee_rows[vacation.colaborador_id]

            day = vacation.data_inicio

            while day <= vacation.data_fim:

                if day in day_columns:

                    column = day_columns[day]

                    cell = sheet.cell(
                        row=row,
                        column=column,
                    )

                    cell.value = "Férias"

                    cell.fill = ferias_fill

                    cell.alignment = Alignment(
                        horizontal="center",
                        vertical="center",
                    )

                day += timedelta(days=1)

    def _format_sheet(
        self,
        sheet,
    ):
        """
    Aplica a formatação geral da folha.
    """

        sheet.freeze_panes = "B2"

        for column in sheet.columns:

            length = max(
                len(str(cell.value))
                if cell.value is not None
                else 0
                for cell in column
            )

            sheet.column_dimensions[
                get_column_letter(column[0].column)
            ].width = length + 2

        thin = Side(
            border_style="thin",
            color="D9D9D9",
        )

        border = Border(
            left=thin,
            right=thin,
            top=thin,
            bottom=thin,
        )

        for row in sheet.iter_rows():
        
            sheet.row_dimensions[
                row[0].row
            ].height = 35

            for cell in row:

                cell.border = border

                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                )
    
    
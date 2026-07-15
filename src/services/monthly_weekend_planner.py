import calendar
import random

from datetime import date, timedelta

from datetime import date
from src.services.weekend_scorer import WeekendScorer

class MonthlyWeekendPlanner:

    def __init__(self):

        self.weekend_scorer = WeekendScorer()

    def plan(
        self,
        schedule,
        previous_schedule,
        hotel,
        start_date,
        end_date,
    ):

        self.hotel = hotel 

        self._initialize_state()

        months = self._months_to_plan(
            previous_schedule,
            start_date,
            end_date,
        )

        for year, month in months:

            self._plan_month(
                schedule,
                previous_schedule,
                hotel,
                year,
                month,
            )

    def _months_to_plan(
        self,
        previous_schedule,
        start_date: date,
        end_date: date,
    ) -> list[tuple[int, int]]:
        """
    Devolve os meses que ainda
    necessitam de planeamento
    de fins de semana.
    """

        months = []

        current = date(
            start_date.year,
            start_date.month,
            1,
        )

        last = date(
            end_date.year,
            end_date.month,
            1,
        )

        while current <= last:

            month = (
                current.year,
                current.month,
            )

            if (
                previous_schedule is None
                or month not in previous_schedule.weekend_plan
            ):
                months.append(
                    month,
                )

            # Avança para o mês seguinte
            if current.month == 12:

                current = date(
                    current.year + 1,
                    1,
                    1,
                )

            else:

                current = date(
                    current.year,
                    current.month + 1,
                    1,
                )

        return months
    
    def _plan_month(
        self,
        schedule,
        previous_schedule,
        hotel,
        year,
        month,
    ):
        """
    Planeia todos os fins de semana
    de um mês.
    """

        weekends = self._month_weekends(
            year,
            month,
        )

        # Mistura a ordem dos fins de semana.
        # A seed garante que o mesmo mês
        # produz sempre a mesma ordem.
        rng = random.Random(f"{year}-{month}")
        rng.shuffle(weekends)

        employees = self._employees_in_priority_order(
            hotel,
        )

        employees.sort(
            key=lambda employee: (
                not self._has_vacation_in_month(
                    hotel,
                    employee,
                    year,
                    month,
                ),  
            ),
        )

        for employee in employees:

            self._plan_employee(
                schedule,
                previous_schedule,
                hotel,
                employee,
                year,
                month,
                weekends,
            )

    def _month_weekends(
        self,
        year: int,
        month: int,
    ) -> list[tuple[date, date]]:
        """
    Devolve todos os fins de semana
    completos (sábado e domingo)
    de um mês.
    """

        weekends = []

        for week in calendar.monthcalendar(
            year,
            month,
        ):

            saturday = week[5]
            sunday = week[6]

            if saturday == 0 or sunday == 0:
                continue

            weekends.append(
                (
                    date(
                        year,
                        month,
                        saturday,
                    ),
                    date(
                        year,
                        month,
                        sunday,
                    ),
            )   
            )

        return weekends
    
    def _employees_in_priority_order(
        self,
        hotel,
    ):
        """
    Devolve os colaboradores pela ordem
    em que devem ser planeados.
    """

        substitution = []

        fixed = []

        rotating = []

        for employee in hotel.employees.values():

            if not employee.ativo:
                continue

            # Os colaboradores com folgas fixas
            # não entram neste planeamento.
            if self._has_fixed_days_off(
                employee,
                hotel,
            ):
                continue

            if self._is_in_substitution_group(
                employee,
                hotel,
            ):
                substitution.append(
                    employee,
                )

            elif self._can_rotate(
                employee,
                hotel,
            ):
                rotating.append(
                    employee,
                )

            else:
                fixed.append(
                    employee,
                )

        fixed.sort(
            key=lambda employee: employee.unidade_principal,
        )

        return (
            substitution
            + fixed
            + rotating
        )
    
    def _plan_employee(
        self,
        schedule,
        previous_schedule,
        hotel,
        employee,
        year,
        month,
        weekends,
    ):
        """
    Planeia o fim de semana mensal
    de um colaborador.
    """
        

        # Já recebeu um fim de semana
        # neste mês num horário anterior.
        if (
            previous_schedule is not None
            and previous_schedule.has_weekend_in_month(
                employee.id,
                year,
                month,
            )   
        ):
            return

        # Já foi planeado neste processo.
        if schedule.has_weekend_in_month(
            employee.id,
            year,
            month,
        ):
            return

        weekend = self._best_weekend(
            schedule,
            previous_schedule,
            hotel,
            employee,
            year,
            month,
            weekends,
        )

        if weekend is None:
            return

        saturday, sunday = weekend

        schedule.add_weekend(
            employee.id,
            saturday,
            sunday,
        )

        self._assign_weekend(
            employee,
            weekend,
        )

    def _best_weekend(
        self,
        schedule,
        previous_schedule,
        hotel,
        employee,
        year,
        month,
        weekends,
    ):
        """
    Devolve o melhor fim de semana
    para o colaborador.
    """

        candidates = []

        for weekend in weekends:

            if not self._is_valid_weekend(
                schedule,
                previous_schedule,
                hotel,
                employee,
                weekend,
            ):
                continue

            candidates.append(
                weekend,
            )

        if not candidates:
            return None

        #
        # 1. Fins de semana que ligam
        # dois períodos de férias.
        #

        bridging = self._bridging_vacation_weekends(
            hotel,
            employee,
            candidates,
        )

        if bridging:
            candidates = bridging

        else:

            #
            # 2. Fins de semana consecutivos
            # a um período de férias.
            #             

            adjacent = self._adjacent_vacation_weekends(
                hotel,
                employee,
                candidates,
            )

            if adjacent:
                candidates = adjacent

        #
        # 3. Escolher o melhor segundo
        # o WeekendScorer.
        #

        return min(
            candidates,
            key=lambda weekend: self.weekend_scorer.score(
                schedule,
                previous_schedule,
                hotel,
                employee,
                weekend,
                self,
            ),
        )       

    def _assign_weekend(
        self,
        employee,
        weekend,
    ):
        """
    Atualiza o estado interno após
    atribuir um fim de semana.
    """

        saturday, sunday = weekend

        self.employee_weekends[
            employee.id
        ] = weekend

        self._update_unit_weekends(
            employee,
            saturday,
        )

        self._update_rotation_weekends(
            employee,
            saturday,
        )

    def _update_unit_weekends(
        self,
        employee,
        saturday,
    ):
        """
    Atualiza o número de colaboradores
    fixos da unidade atribuídos ao
    mesmo fim de semana.
    """

        if self._can_rotate(
            employee,
            self.hotel,
        ):
            return

        key = (
            employee.unidade_principal,
            saturday,
        )

        self.unit_weekends[
            key
        ] = (
            self.unit_weekends.get(
                key,
                0,
            )
            + 1
        )

    def _update_rotation_weekends(
        self,
        employee,
        saturday,
    ):
        """
    Atualiza o número de colaboradores
    rotativos atribuídos ao mesmo
    fim de semana.
    """

        if not self._can_rotate(
            employee,
            self.hotel,
        ):
            return

        self.rotation_weekends[
            saturday
        ] = (
            self.rotation_weekends.get(
                saturday,
                0,
            )
            + 1
        )

    def _is_in_substitution_group(
        self,
        employee,
        hotel,
    ) -> bool:
        """
    Indica se o colaborador pertence
    a um grupo de substituição.
    """

        return any(
            substitution.employee_id == employee.id
            or substitution.substitute_id == employee.id
            for substitution in hotel.substitutions
        )
    
    def _can_rotate(
        self,
        employee,
        hotel,
    ) -> bool:
        """
    Indica se o colaborador pode
    rodar entre unidades.
    """

        return employee.pode_rodar


    def _initialize_state(self):
        """
    Inicializa o estado interno
    do planeamento mensal de fins
    de semana.
    """

        # Colaboradores da mesma unidade
        # já atribuídos por fim de semana.
        self.unit_weekends = {}

        # Colaboradores rotativos
        # já atribuídos por fim de semana.
        self.rotation_weekends = {}

        # Fins de semana já atribuídos
        # a cada colaborador.
        self.employee_weekends = {}

        # Plano mensal antes de ser
        # aplicado ao Schedule.
        self.weekend_plan = {}


    def _get_weekends(
        self,
        year,
        month,
    ):
        """
        Devolve todos os fins de semana completos do mês.
        """

        weekends = []

        _, last_day = calendar.monthrange(
            year,
            month,
        )

        saturday = None

        for day in range(1, last_day + 1):

            current = date(
                year,
                month,
                day,
            )

            if current.weekday() == 5:
                saturday = current

            elif (
                current.weekday() == 6
                and saturday is not None
            ):

                weekends.append(
                    (
                        saturday,
                        current,
                    )
                )

        return weekends
    
    def _has_fixed_days_off(
        self,
        employee,
        hotel,
    ) -> bool:

        return any(
            day.employee_id == employee.id
            for day in hotel.fixed_days_off
        )
    
    def _is_valid_weekend(
        self,
        schedule,
        previous_schedule,
        hotel,
        employee,
        weekend,
    ) -> bool:
        """
    Verifica se um fim de semana pode ser
    atribuído ao colaborador.
    """

        if self._already_has_weekend(
            schedule,
            previous_schedule,
            employee,
            weekend,
        ):
            return False

        if self._violates_substitution(
            schedule,
            previous_schedule,
            hotel,
            employee,
            weekend,
        ):
            return False

        return True
    
    def _already_has_weekend(
        self,
        schedule,
        previous_schedule,
        employee,
        weekend,
    ) -> bool:
        """
    Verifica se o colaborador já
    possui um fim de semana
    atribuído neste mês.
    """

        saturday, _ = weekend

        if (
            previous_schedule is not None
            and previous_schedule.has_weekend_in_month(
                employee.id,
                saturday.year,
                saturday.month,
            )
        ):
            return True

        return schedule.has_weekend_in_month(
            employee.id,
            saturday.year,
            saturday.month,
        )
    
    def _violates_substitution(
        self,
        schedule,
        previous_schedule,
        hotel,
        employee,
        weekend,
    ) -> bool:
        """
    Verifica se o fim de semana
    coincide com o da respetiva
    substituição.
    """

        partner = self._substitution_partner(
            employee,
            hotel,
        )

        if partner is None:
            return False

        saturday, sunday = weekend

        month = (
            saturday.year,
            saturday.month,
        )

        # Horário atual
        partner_weekend = schedule.get_weekend(
            partner.id,
            *month,
        )

        if partner_weekend == weekend:
            return True

        # Horário anterior
        if previous_schedule is not None:

            partner_weekend = previous_schedule.get_weekend(
                partner.id,
                *month,
            )

            if partner_weekend == weekend:
                return True

        return False
    
    def _substitution_partner(
        self,
        employee,
        hotel,
    ):
        """
    Devolve o colaborador do mesmo
    grupo de substituição.
    """

        for substitution in hotel.substitutions:

            if substitution.employee_id == employee.id:

                return hotel.employees[
                    substitution.substitute_id
                ]

            if substitution.substitute_id == employee.id:

                return hotel.employees[
                    substitution.employee_id
                ]

        return None
    
    def _vacation_adjacent_weekends(
        self,
        hotel,
        employee,
        candidates,
        ):
        """
    Devolve os fins de semana que ficam
    imediatamente antes ou depois
    de um período de férias.
    """

        preferred = []

        for saturday, sunday in candidates:

            for vacation in hotel.vacations:

                if vacation.colaborador_id != employee.id:
                    continue

                #
                # Fim de semana imediatamente
                # antes das férias.
                #

                if vacation.data_inicio - timedelta(days=2) == saturday:
                    preferred.append((saturday, sunday))
                    break

                #
                # Fim de semana imediatamente
                # depois das férias.
                #

                if vacation.data_fim + timedelta(days=1) == saturday:
                    preferred.append((saturday, sunday))
                    break

        return preferred
    
    def _bridging_vacation_weekends(
        self,
        hotel,
        employee,
        candidates,
    ):
        """
    Devolve os fins de semana que unem
    dois períodos de férias consecutivos.
    """

        preferred = []

        vacations = sorted(
            (
                vacation
                for vacation in hotel.vacations
                if vacation.colaborador_id == employee.id
            ),
            key=lambda vacation: vacation.data_inicio,
        )

        for saturday, sunday in candidates:

            for i in range(len(vacations) - 1):

                current = vacations[i]
                nxt = vacations[i + 1]

                if (
                    current.data_fim + timedelta(days=1)
                    == saturday
                    and
                    nxt.data_inicio - timedelta(days=1)
                    == sunday
                ):
                    preferred.append(
                        (saturday, sunday)
                    )

        return preferred
    
    def _adjacent_vacation_weekends(
        self,
        hotel,
        employee,
        candidates,
    ):
        """
    Devolve os fins de semana que ficam
    imediatamente antes ou depois
    de um período de férias.
    """

        preferred = []

        vacations = [
            vacation
            for vacation in hotel.vacations
            if vacation.colaborador_id == employee.id
        ]

        for weekend in candidates:

            saturday, sunday = weekend

            for vacation in vacations:

                #
                # Fim de semana imediatamente
                # antes das férias.
                #

                if (
                    vacation.data_inicio
                    - timedelta(days=2)
                    == saturday
                ):
                    preferred.append(
                        weekend,
                    )
                    break

                #
                # Fim de semana imediatamente
                # depois das férias.
                #

                if (
                    vacation.data_fim
                    + timedelta(days=1)
                    == saturday
                ):
                    preferred.append(
                        weekend,
                    )
                    break

        return preferred
    
    def _has_vacation_in_month(
        self,
        hotel,
        employee,
        year,
        month,
    ) -> bool:
        """
    Indica se o colaborador tem
    férias durante este mês.
    """

        for vacation in hotel.vacations:

            if vacation.colaborador_id != employee.id:
                continue

            #
            # Há pelo menos um dia de férias
            # neste mês.
            #

            if (
                vacation.data_inicio.year == year
                and vacation.data_inicio.month == month
            ) or (
                vacation.data_fim.year == year
                and vacation.data_fim.month == month
            ):
                return True

        return False
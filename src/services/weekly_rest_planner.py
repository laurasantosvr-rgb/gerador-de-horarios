from calendar import week
from datetime import date
from datetime import timedelta
from src.models import employee, schedule
from src.services.rest_scorer import RestScorer
from src.enums.rest_pattern import RestPattern

class WeeklyRestPlanner:
    """Garante duas folgas consecutivas por semana."""

    AVOID_DAY_PENALTY = 1000

    def __init__(self,
                 coverage_evaluator,
                ):

        self.rest_scorer = RestScorer()
        
        self.coverage_evaluator = coverage_evaluator

        self.week_patterns = {}

    def plan(
        self,
        schedule,
        previous_schedule,
        history,
        hotel,
        start_date,
        end_date,
    ):

        """
    Planeia todas as folgas semanais do período.
    """ 
        
        self.previous_schedule = previous_schedule

        self.history = history
    
        self.start_date = start_date

        self.end_date = end_date

        self.planning_days = self._planning_days(
            start_date,
            end_date,
        )

        self._initialize_state()

        weeks = self._get_weeks(
            start_date,
            end_date,
        )

        employees = self._employees_in_priority_order(
            hotel,
        )
        for week in weeks:

            for employee in employees:

                if not self._needs_weekly_rest(
                    employee,
                    hotel,
                ):
                    continue

                self._plan_employee(
                    schedule,
                    hotel,
                    employee,
                    week,
                    weeks,
                )

    def _initialize_state(self):
        """
    Inicializa o estado do planeamento.

    Estas estruturas vão sendo atualizadas à medida
    que os pares de folgas são atribuídos.
    """

        # Conjunto dos dias de folga
        # já atribuídos a cada colaborador
        self.employee_day_offs = {}

        # Número de colaboradores de folga
        # por unidade e por dia
        self.unit_day_offs = {}

        # Número de colaboradores rotativos
        # de folga por dia
        self.rotation_day_offs = {}

        # Número total de colaboradores
        # de folga ao fim de semana
        self.weekend_day_offs = {}

        # Número total de colaboradores
        # de folga por dia
        self.total_day_offs = {}

        #
        # Colaboradores de férias por dia.
        #
        self.vacation_day_offs = {}

        #
        # Colaboradores de férias por unidade e dia.
        #
        self.unit_vacation_day_offs = {}

        self.rotation_vacation_day_offs = {}

        self.fixed_day_offs = {}

        self.unit_fixed_day_offs = {}

        self.rotation_fixed_day_offs = {}

    def _plan_employee(
        self,
        schedule,
        hotel,
        employee,
        week,
        weeks,
    ):
        """
    Planeia as folgas do colaborador
    para uma única semana.
    """

        pattern = self._week_rest_pattern(
            schedule,
            employee,
            week,
            weeks,
        )

        key = (
            employee.id,
            week[0],
        )

        self.week_patterns[key] = pattern

        # -----------------------------
        # Duas folgas consecutivas
        # -----------------------------

        if pattern == RestPattern.CONSECUTIVE_PAIR:

            pair = self._best_pair(
                schedule,
                hotel,
                employee,
                week,
            )

            if pair is None:

                if self._repair_substitution_conflict(
                    schedule,
                    hotel,
                    employee,
                    week,
                ):

                    pair = self._best_pair(
                        schedule,
                        hotel,
                        employee,
                        week,
                    )

            if pair is None:

                print(
                    "SEM PAR:",
                    employee.nome,
                    week,
                )
                return

            self._assign_rest_days(
                schedule,
                hotel,
                employee,
                pair,
            )

        # -----------------------------
        # Uma folga isolada
        # -----------------------------

        elif pattern == RestPattern.SINGLE_DAY:

            day = self._best_single_day(
                schedule,
                hotel,
                employee,
                week,
            )

            if day is None:

                if self._repair_substitution_conflict(
                    schedule,
                    hotel,
                    employee,
                    week,
                ):

                    #
                    # Tentar novamente
                    #

                    day = self._best_single_day(
                        schedule,
                        hotel,
                        employee,
                        week,
                    )

            if day is None:

                print(
                    "SEM SINGLE:",
                    employee.nome,
                    week,
                )
                return

            self._assign_rest_days(
                schedule,
                hotel,
                employee,
                [day],
        )
            
    def _week_rest_pattern(
        self,
        schedule,
        employee,
        week,
        weeks,
    ) -> RestPattern:
        """
    Devolve o padrão de descanso da semana.
    """

        #
        # Tem fim de semana nesta semana?
        #

        if self._has_weekend_off(
            schedule,
            employee,
            week,
        ):
            return RestPattern.SINGLE_DAY

        #
        # É a semana imediatamente a seguir
        # ao fim de semana?
        #

        index = weeks.index(week)

        if index > 0:

            previous_week = weeks[index - 1]

            if self._has_weekend_off(
                schedule,
                employee,
                previous_week,
            ):
                return RestPattern.SINGLE_DAY

        #
        # Caso contrário
        #

        return RestPattern.CONSECUTIVE_PAIR
    
    def _get_weeks(
        self,
        start_date,
        end_date,
    ):

        weeks = []

        current = start_date

        while current <= end_date:

            week = []

            for i in range(7):

                day = current + timedelta(days=i)

                if day > end_date:
                    break

                week.append(day)

            weeks.append(week)

            current += timedelta(days=7)

        return weeks
    
    def _get_rest_pairs(      
        self,
        week,
    ):
        """
    Devolve todos os pares de dias
    consecutivos de uma semana.
    """

        pairs = []

        for i in range(len(week) - 1):

            pair = (
                    week[i],
                    week[i + 1],
                )
        
            pairs.append(pair)

        return pairs
    
    def _get_single_days(
        self,
        week,
    ):
        """
    Devolve todos os dias úteis possíveis
    para uma folga isolada.
    """

        return [
            day
            for day in week
        ]
    
    def _has_fixed_days_off(
        self,
        employee,
        hotel,
    ) -> bool:
        """
    Verifica se o colaborador tem
    folgas fixas.
    """

        return any(
            fixed_day.employee_id == employee.id
            for fixed_day in hotel.fixed_days_off
        )
    
    def _is_valid_single_day(
        self,
        schedule,
        hotel,
        employee,
        day,
    ):
        
        #
        # O WeeklyRestPlanner não pode atribuir
        # sábados ou domingos, exceto para
        # prolongar férias.
        #

        if (
            day.weekday() in (5, 6)
            and
            not self._extends_vacation_single_day(
                hotel,
                employee,
                day,
            )
        ):
            return False

        return self.is_valid_days(
            schedule,
            hotel,
            employee,
            [day],
        )
    
    def _is_valid_pair(
        self,
        schedule,
        hotel,
        employee,
        pair,
    ):
        if (
            any(day.weekday() in (5, 6) for day in pair)
            and
            not self._extends_vacation(
                hotel,
                employee,
                pair,
            )
        ):
            return False

        return self.is_valid_days(
            schedule,
            hotel,
            employee,
            pair,
        )
    
    def is_valid_days(
        self,
        schedule,
        hotel,
        employee,
        days,
    ) -> bool:
        """
    Verifica se um conjunto de dias de folga
    satisfaz todas as Hard Constraints.
    """

        if self._violates_substitution(
            schedule,
            hotel,
            employee,
            days,
        ):
            return False

        if self._violates_five_day_rule(
            schedule,
            hotel,
            employee,
            days,
        ):
        
            print("5 days", employee.nome, days)
            return False
        
        if self._creates_three_consecutive_days_off(
            schedule,
            hotel,
            employee,
            days,
        ):
            return False

        return True
    
    def _best_pair(
        self,
        schedule,
        hotel,
        employee,
        week,
        avoid_days=None,
    ):
        """
    Escolhe o melhor par de folgas
    para uma determinada semana.
    """

        valid_pairs = []
        
        # -----------------------------
        # 1. Tenta cumprir todas as regras
        # -----------------------------

        for pair in self._get_rest_pairs(
            week,
        ):
            if any(
                self._is_vacation_day(
                    hotel,
                    employee,
                    day,
                )
                for day in pair
            ):
                continue

            if self._is_valid_pair(
                schedule,
                hotel,
                employee,
                pair,
            ):
                valid_pairs.append(
                    pair,
                )

        preferred_pairs = []
        avoided_pairs = []

        if avoid_days is None:
            avoid_days = set()

        for pair in valid_pairs:

            if any(day in avoid_days for day in pair):
                avoided_pairs.append(pair)
            else:
                preferred_pairs.append(pair)

        pairs = preferred_pairs

        if not pairs:
            pairs = avoided_pairs


        # -----------------------------
        # 3. Escolhe o melhor candidato
        # -----------------------------

        best_pair = None
        best_score = None

        for pair in pairs:

            score = self.rest_scorer.score_pair(
                schedule,
                hotel,
                employee,
                pair,
                self,
            )

            if (
                best_score is None
                or score < best_score
            ):
                best_score = score
                best_pair = pair

        return best_pair

    
    def _best_single_day(
        self,
        schedule,
        hotel,
        employee,
        week,
        avoid_days=None,
    ):
        """
    Escolhe a melhor folga isolada
    para uma determinada semana.
    """

        candidates = []

        if avoid_days is None:
            avoid_days = set()

        # -----------------------------
        # 1. Tenta cumprir todas as regras
        # -----------------------------

        for day in self._get_single_days(
            week,
        ):
            
            if self._is_vacation_day(
                hotel,
                employee,
                day,
            ):
                continue
            

            if self._is_valid_single_day(
                schedule,
                hotel,
                employee,
                day,
            ):
                candidates.append(day)

        preferred_days = []
        avoided_days = []

        for day in candidates:

            if day in avoid_days:
                avoided_days.append(day)
            else:
                preferred_days.append(day)

        days = preferred_days

        if not days:
            days = avoided_days

        # -----------------------------
        # 3. Escolhe o melhor candidato
        # -----------------------------

        best_day = None
        best_score = None

        for day in days:

            score = self.rest_scorer.score_single_day(
                schedule,
                hotel,
                employee,
                [day],
                self,
            )

            if (
                best_score is None
                or score < best_score
            ):
                best_score = score
                best_day = day

        return best_day

    
    def _needs_weekly_rest(     
        self,
        employee,
        hotel,
    ) -> bool:
        """
    Indica se o colaborador necessita
    de planeamento de folgas semanais.
    """

        if not employee.ativo:
            return False

        # Já tem fins de semana sempre livres
        if not employee.trabalha_fins_de_semana:
            return False

        # Já tem folgas fixas
        if self._has_fixed_days_off(
            employee,
            hotel,
        ):
            return False

        return True
    
    def _is_in_substitution_group(
        self,
        employee,
        hotel,
    ):
        """
    Indica se o colaborador pertence
    a algum grupo de substituição.
    """

        return any(
            substitution.employee_id == employee.id
            or substitution.substitute_id == employee.id
            for substitution in hotel.substitutions
        )
    
    def _substitution_partner(
        self,
        employee,
        hotel,
    ):
        """
    Devolve o colaborador que pertence
    ao mesmo grupo de substituição.
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
    
    def _unit_employees(
        self,
        hotel,
        unit_name,
    ):
        """
    Devolve os colaboradores ativos
    cuja unidade principal é a indicada.
    """

        return [
            employee
            for employee in hotel.employees.values()
            if (
                employee.ativo
                and employee.unidade_principal == unit_name
                and not self._can_rotate(
                    employee,
                    hotel,
                )
            )
        ]
    
    def _rotation_count(
        self,
        hotel,
    ):
        """
    Devolve todos os colaboradores
    que podem reforçar outras unidades.
    """

        return sum(
            1
            for employee in hotel.employees.values()
            if (
                employee.ativo
                and self._can_rotate(
                    employee,
                    hotel,
                )
            )
        )

    def _can_rotate(
        self,
        employee,
        hotel,
    ) -> bool:
        """
    Indica se o colaborador pode
    reforçar outra unidade.
    """

        return any(
            reinforcement.employee_id == employee.id
            for reinforcement in hotel.reinforcements
        )
    
    def _employees_in_priority_order(
        self,
        hotel,
    ):
        """
    Devolve os colaboradores pela ordem
    em que devem ser planeados.
    """

        ordered = []

        # -------------------------
        # 1. Grupos de substituição
        # -------------------------

        added = set()

        for substitution in hotel.substitutions:

            employee = hotel.employees[
                substitution.employee_id
            ]

            substitute = hotel.employees[
                substitution.substitute_id
            ]

            if employee.id not in added:
                ordered.append(employee)
                added.add(employee.id)

            if substitute.id not in added:
                ordered.append(substitute)
                added.add(substitute.id)

        # -------------------------
        # 2. Colaboradores fixos
        # -------------------------

        for unit in hotel.units.values():

            for employee in self._unit_employees(
                hotel,
                unit.nome,
            ):

                if employee.id in added:
                    continue

                if self._can_rotate(
                    employee,
                    hotel,
                ):
                    continue

                ordered.append(employee)
                added.add(employee.id)

        # -------------------------
        # 3. Rotativos
        # -------------------------

        for employee in hotel.employees.values():

            if employee.id in added:
                continue

            if not self._can_rotate(
                employee,
                hotel,
            ):
                continue

            ordered.append(employee)

        return ordered
    
    def _violates_substitution(
        self,
        schedule,
        hotel,
        employee,
        days,
    ) -> bool:
        """
    Verifica se o par de folgas coincide
    com as folgas do respetivo substituto.
    """

        partner = self._substitution_partner(
            employee,
            hotel,
        )
        if partner is None:
            return False

        partner_days_off = self._employee_day_offs(
            schedule,
            partner,
        )

        days = set(days)

        conflict = bool(days & partner_days_off)

        return bool(
            days & partner_days_off
        )
    
    def _violates_five_day_rule(
        self,
        schedule,
        hotel,
        employee,
        days,
    ):
        """
    Verifica se o novo par cria
    mais de cinco dias consecutivos
    de trabalho.
    """ 
        
        return (
            self._consecutive_work_days(
                schedule,
                hotel,
                employee,
                days,
            )
            > 5
        )
    
    def _has_weekend_off(
        self,
        schedule,
        employee,
        week,
    ) -> bool:
        """
    Verifica se o colaborador tem
    sábado e domingo de folga
    nesta semana.
    """

        saturday = next(
            (day for day in week if day.weekday() == 5),
            None,
        )

        sunday = next(
            (day for day in week if day.weekday() == 6),
            None,
     )

        if saturday is None or sunday is None:
            return False

        return (
            schedule.is_day_off(
            employee.id,
            saturday,
        )
        and
        schedule.is_day_off(
            employee.id,
            sunday,
        )
    )
    
    def _assign_rest_days(
        self,
        schedule,
        hotel,
        employee,
        days,
    ):
        """
    Atribui um ou mais dias de folga
    ao colaborador e atualiza o estado
    do planeamento.
    """
        # Regista no horário
        for day in days:

            schedule.add_day_off(
                employee.id,
                day,
            )

        # Guarda as folgas por colaborador
        self.employee_day_offs.setdefault(
            employee.id,
            set(),
        )

        self.employee_day_offs[
            employee.id
        ].update(days)

        # Atualiza o número total
        # de colaboradores de folga
        for day in days:

            self.total_day_offs[day] = (
                self.total_day_offs.get(day, 0)
                + 1
            )

        # Atualiza os restantes contadores
        self._update_unit_day_offs(
            employee,
            days,
        )

        self._update_rotation_day_offs(
            hotel,
            employee,
            days,
        )

        self._update_weekend_day_offs(
            days,
        )

    def _update_weekend_day_offs(
        self,
        days,
    ):
        """
    Atualiza o número de colaboradores
    de folga ao fim de semana.
    """

        for day in days:

            if day.weekday() not in (5, 6):
                continue

            self.weekend_day_offs[day] = (
                self.weekend_day_offs.get(
                    day,
                    0,
                )
                + 1
            )

    def _update_unit_day_offs(
        self,
        employee,
        days,
    ):
        """
    Atualiza o número de colaboradores
    de folga por unidade e por dia.
    """

        for day in days:

            key = (
                employee.unidade_principal,
                day,
            )

            self.unit_day_offs[key] = (
                self.unit_day_offs.get(
                    key,
                    0,
                )
                + 1
            )

    def _update_rotation_day_offs(
        self,
        hotel,
        employee,
        days,
    ):
        """
    Atualiza o número de colaboradores
    rotativos de folga por dia.
    """

        if not self._can_rotate(
            employee,
            hotel,
        ):
            return

        for day in days:

            self.rotation_day_offs[day] = (
                self.rotation_day_offs.get(
                    day,
                    0,
                )
                + 1
            )

    def _employee_day_offs(
        self,
        schedule,
        employee,
    ):
        """
    Devolve todas as folgas conhecidas
    do colaborador.
    """
        analysis_start = self.start_date - timedelta(days=7)
        analysis_end = self.end_date

        days_off = set()

        # Folgas do período anterior
        if self.previous_schedule is not None:

            for day_off in self.previous_schedule.day_offs:

                if day_off.employee_id == employee.id:

                    if day_off.day >= analysis_start:
                        days_off.add(day_off.day)

        # Folgas já atribuídas neste planeamento
        days_off.update(
                self.employee_day_offs.get(
                employee.id,
                set(),
            )   
        )

        # Fins de semana mensais
        for month_plan in schedule.weekend_plan.values():

            weekend = month_plan.get(
                employee.id,
            )

            if weekend is None:
                continue

            saturday, sunday = weekend

            if saturday >= analysis_start:
                days_off.add(saturday)

            if sunday >= analysis_start:
                days_off.add(sunday)

        return {
            day
            for day in days_off
            if analysis_start <= day <= analysis_end
        }
    
    def _consecutive_work_days(
        self,
        schedule,
        hotel,
        employee,
        simulated_days,
    ) -> int:
        """
    Devolve o número de dias consecutivos de trabalho
    entre a folga anterior e o novo bloco de folgas.
    """

        days_off = self._employee_day_offs(
            schedule,
            employee,
        )

        days_off.update(simulated_days)

        for vacation in hotel.vacations:

            if vacation.colaborador_id != employee.id:
                continue

            day = vacation.data_inicio

            while day <= vacation.data_fim:

                days_off.add(day)

                day += timedelta(days=1)

        block_start = min(simulated_days)

        previous_day_off = None

        for day in sorted(days_off):

            if day >= block_start:
                break

            previous_day_off = day

        # Não existe nenhuma folga anterior:
        # conta desde o início do período.
        if previous_day_off is None:

            return 0
        
        # Conta os dias de trabalho entre a
        # folga anterior e o novo bloco.
        return (
            block_start
            - previous_day_off
        ).days - 1
    
    def _planning_days(
        self,
        start_date,
        end_date,
    ):
        """
    Devolve todos os dias a analisar.

    Inclui os 14 dias anteriores ao início
    do período para validar a regra dos
    cinco dias consecutivos.
    """

        first_day = start_date - timedelta(days=7)

        days = []

        current_day = first_day

        while current_day <= end_date:

            days.append(
                current_day,
            )

            current_day += timedelta(days=1)

        return days


    def _rotation_day_offs_count(
        self,
        hotel,
        employee,
        days,
    ):
        """
    Devolve quantos colaboradores
    rotativos ficariam de folga.
    """

        if not self._can_rotate(
            employee,
            hotel,
        ):
            return 0

        total = 0

        for day in days:

            total += (
            self.total_day_offs.get(
                day,
                0,
            )
            + self.vacation_day_offs.get(
                day,
                0,
            )
            + self.fixed_day_offs.get(
                day,
                0,
            )
            + 1
        )

        return total
    
    def _unit_day_offs_count(
        self,
        hotel,
        employee,
        days,
    ):
        """
    Conta quantos colaboradores fixos
    da unidade ficariam de folga.
    """

        total = 0

        for day in days:

            key = (
                employee.unidade_principal,
                day,
            )

            total += (
            self.total_day_offs.get(
                day,
                0,
            )
            + self.vacation_day_offs.get(
                day,
                0,
            )
            + self.fixed_day_offs.get(
                day,
                0,
            )
            + 1
        )

        return total

    def _remove_week_rest(
        self,
        schedule,
        hotel,
        employee,
        week,
    ):
        """
    Remove as folgas semanais do colaborador
    nesta semana, preservando um eventual
    fim de semana atribuído pelo
    MonthlyWeekendPlanner.

    Atualiza igualmente todos os contadores
    utilizados pelo planeador.
    """

        week = set(week)

        #
        # Dias de folga existentes nesta semana
        #

        days = [
            day
            for day in self.employee_day_offs.get(
                employee.id,
                set(),
            )
            if day in week
        ]

        #
        # Preservar sábado e domingo caso
        # pertençam ao WeekendPlanner.
        #

        if self._has_weekend_off(
            schedule,
            employee,
            week,
        ):
            days = [
                day
                for day in days
                if day.weekday() < 5
            ]

        if not days:
            return []

        #
        # Remover do schedule
        #

        schedule.day_offs = [
            day_off
            for day_off in schedule.day_offs
            if not (
                day_off.employee_id == employee.id
                and day_off.day in days
            )
        ]

        #
        # Remover do employee_day_offs
        #

        self.employee_day_offs[
            employee.id
        ].difference_update(days)

        #
        # Atualizar unit_day_offs
        #

        for day in days:

            key = (
                employee.unidade_principal,
                day,
            )

            if key in self.unit_day_offs:

                self.unit_day_offs[key] -= 1

                if self.unit_day_offs[key] <= 0:
                    del self.unit_day_offs[key]

        #
        # Atualizar rotation_day_offs
        #

        if self._can_rotate(
            employee,
            hotel,
        ):

            for day in days:

                if day in self.rotation_day_offs:

                    self.rotation_day_offs[day] -= 1

                    if self.rotation_day_offs[day] <= 0:
                        del self.rotation_day_offs[day]

        #
        # Atualizar total_day_offs
        #

        for day in days:

            if day in self.total_day_offs:

                self.total_day_offs[day] -= 1

                if self.total_day_offs[day] <= 0:
                    del self.total_day_offs[day]

        self._remove_weekend_day_offs(
            days,
        )

        return days
    
    def _replan_week(
        self,
        schedule,
        hotel,
        employee,
        week,
        pattern,
        avoid_days=None,
    ) -> bool:
        """
    Replaneia as folgas de uma única semana
    para um colaborador.

    Tenta evitar os dias indicados em
    avoid_days, mas apenas como preferência.
    """

        if avoid_days is None:
            avoid_days = set()

        #
        # Par consecutivo
        #

        if pattern == RestPattern.CONSECUTIVE_PAIR:

            pair = self._best_pair(
                schedule,
                hotel,
                employee,
                week,
                avoid_days=avoid_days,
            )

            if pair is None:
                return False

            self._assign_rest_days(
                schedule,
                hotel,
                employee,
                pair,
            )

            return True

        #
        # Folga isolada
        #

        day = self._best_single_day(
            schedule,
            hotel,
            employee,
            week,
            avoid_days=avoid_days,
        )

        if day is None:
            return False

        self._assign_rest_days(
            schedule,
            hotel,
            employee,
            [day],
        )

        return True
    
    def _substitution_conflict_days(
        self,
        schedule,
        hotel,
        employee,
        week,
    ) -> set:
        """
    Devolve os dias da semana que apenas estão
    bloqueados pela substituição.

    Estes dias serão evitados quando forem
    replaneadas as folgas do colaborador
    relacionado.
    """

        avoid_days = set()

        for day in week:

            #
            # Não existe conflito de substituição.
            #

            if not self._violates_substitution(
                schedule,
                hotel,
                employee,
                [day],
            ):
                continue

            #
            # Mesmo sem substituição continuaria
            # a violar os 5 dias consecutivos.
            #

            if self._violates_five_day_rule(
                schedule,
                hotel,
                employee,
                [day],
            ):
                continue

            #
            # Este dia só está bloqueado
            # pela substituição.
            #

            avoid_days.add(day)

        return avoid_days
    
    def _repair_substitution_conflict(
        self,
        schedule,
        hotel,
        employee,
        week,
    ) -> bool:
        """
    Tenta resolver um conflito de substituição
    replaneando apenas a semana do colaborador
    relacionado.

    Devolve True se conseguir libertar pelo
    menos um dos dias bloqueados.
    """

        #
        # Dias que apenas estão bloqueados
        # pela substituição.
        #

        avoid_days = self._substitution_conflict_days(
            schedule,
            hotel,
            employee,
            week,
        )

        if not avoid_days:
            return False

        #
        # Procurar a substituição.
        #

        for substitution in hotel.substitutions:

            if substitution.employee_id == employee.id:

                other = hotel.employees[
                    substitution.substitute_id
                ]

            elif substitution.substitute_id == employee.id:

                other = hotel.employees[
                    substitution.employee_id
                ]


            else:
                continue

            #
            # Descobrir o padrão atual.
            #

            pattern = self.week_patterns[
                (
                    other.id,
                    week[0],
                )
            ]

            #
            # Guardar as folgas atuais.
            #

            old_days = self._remove_week_rest(
                schedule,
                hotel,
                other,
                week,
            )

            if not old_days:
                continue

            #
            # Tentar novo planeamento.
            #

            success = self._replan_week(
                schedule,
                hotel,
                other,
                week,
                pattern,
                avoid_days=avoid_days,
            )

            if success:

                day = self._best_single_day(
                    schedule,
                    hotel,
                    employee,
                    week,
                )

                if day is not None:
                    return True
            
            #
            # Rollback.
            #

            self._assign_rest_days(
                schedule,
                hotel,
                other,
                old_days,
            )

        return False
    
    def _remove_weekend_day_offs(
        self,
        days,
    ):
        """
    Atualiza o número de colaboradores
    de folga ao fim de semana após
    remover folgas.
    """

        for day in days:

            if day.weekday() not in (5, 6):
                continue

            if day in self.weekend_day_offs:

                self.weekend_day_offs[day] -= 1

                if self.weekend_day_offs[day] <= 0:
                    del self.weekend_day_offs[day]

    def _is_vacation_day(
        self,
        hotel,
        employee,
        day,
    ) -> bool:
        """
    Verifica se o colaborador está de férias
    nesse dia.
    """

        for vacation in hotel.vacations:

            if vacation.colaborador_id != employee.id:
                continue

            if vacation.data_inicio <= day <= vacation.data_fim:
                return True

        return False
    
    def _total_day_offs_count(
        self,
        days,
    ):
        """
    Conta quantos colaboradores
    ficariam de folga nesses dias.
    """

        total = 0

        for day in days:

            total += (
                self.total_day_offs.get(
                    day,
                    0,
                )
                + self.vacation_day_offs.get(
                    day,
                    0,
                )
                + self.fixed_day_offs.get(
                    day,
                    0,
                )
                + 1
            )

        return total
    
    def _creates_three_consecutive_days_off(
        self,
        schedule,
        hotel,
        employee,
        simulated_days,
    ):
        """
    Impede 3 dias consecutivos de folga.
    """

        days_off = self._employee_day_offs(
            schedule,
            employee,
        )

        days_off.update(simulated_days)

        ordered = sorted(days_off)

        consecutive = 1

        for previous, current in zip(ordered, ordered[1:]):

            if (current - previous).days == 1:

                consecutive += 1

                if consecutive >= 3:
                    return True

            else:
                consecutive = 1

        return False
    
    def _extends_vacation(
        self,
        hotel,
        employee,
        pair,
    ) -> bool:
        """
    Indica se o par de folgas prolonga
    um período de férias do colaborador.

    Considera que prolonga as férias se
    existir continuidade imediata entre
    as férias e o par de folgas.
    """

        pair_start = min(pair)
        pair_end = max(pair)

        for vacation in hotel.vacations:

            if vacation.colaborador_id != employee.id:
                continue

            #
            # Férias terminam imediatamente
            # antes do par.
            #

            if vacation.data_fim + timedelta(days=1) == pair_start:
                return True

            #
            # Férias começam imediatamente
            # depois do par.
            #

            if vacation.data_inicio - timedelta(days=1) == pair_end:
                return True

        return False
    
    def _extends_vacation_single_day(
        self,
        hotel,
        employee,
        day,
    ) -> bool:
        """
    Indica se a folga isolada prolonga
    um período de férias.
    """

        for vacation in hotel.vacations:

            if vacation.colaborador_id != employee.id:
                continue

            #
            # Férias terminam imediatamente
            # antes da folga.
            #

            if vacation.data_fim + timedelta(days=1) == day:
                return True

            #
            # Férias começam imediatamente
            # depois da folga.
            #

            if vacation.data_inicio - timedelta(days=1) == day:
                return True

        return False
    
    def _initialize_vacation_state(
        self,
        hotel,
    ):
        """
    Conta os colaboradores de férias
    por dia e por unidade.
    """

        for vacation in hotel.vacations:

            employee = hotel.employees[
                vacation.colaborador_id
            ]

            current = vacation.data_inicio

            while current <= vacation.data_fim:

                #
                # Total.
                #

                self.vacation_day_offs[current] = (
                    self.vacation_day_offs.get(
                        current,
                        0,
                    )
                    + 1
                )

                #
                # Unidade.
                #

                key = (
                    employee.unidade_principal,
                    current,
                )

                self.unit_vacation_day_offs[key] = (
                    self.unit_vacation_day_offs.get(
                        key,
                        0,
                    )
                    + 1
                )

                #
                # Rodar.
                #

                if self._can_rotate(
                    employee,
                    hotel,
                ):
                    self.rotation_vacation_day_offs[current] = (
                        self.rotation_vacation_day_offs.get(
                            current,
                            0,
                        )
                        + 1
                    )

                current += timedelta(days=1)
    
    def _initialize_fixed_days_off_state(
        self,
        hotel,
    ):
        """
    Conta os colaboradores com
    folgas fixas por dia, por unidade
    e por grupo de rotação.
    """

        for fixed_day in hotel.fixed_days_off:

            employee = hotel.employees[
                fixed_day.employee_id
            ]

            day = fixed_day.data

            #
            # Total.
            #

            self.fixed_day_offs[day] = (
                self.fixed_day_offs.get(day, 0)
                + 1
            )

            #
            # Unidade.
            #

            key = (
                employee.unidade_principal,
                day,
            )

            self.unit_fixed_day_offs[key] = (
                self.unit_fixed_day_offs.get(key, 0)
                + 1
            )

            #
            # Rodativos.
            #

            if self._can_rotate(
                employee,
                hotel,
            ):
                self.rotation_fixed_day_offs[day] = (
                    self.rotation_fixed_day_offs.get(
                        day,
                        0,
                    )
                    + 1
                )
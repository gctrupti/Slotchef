"""Google OR-Tools CP-SAT scheduling engine for SlotChef."""

from __future__ import annotations

import time

from ortools.sat.python import cp_model

from slotchef_optimizer.constraints.eligibility import filter_eligible_candidates
from slotchef_optimizer.explanations.reasons import ReasonCode, SolverStatus
from slotchef_optimizer.models.domain import (
    AssignmentProposal,
    BookingInput,
    ScheduleResult,
    SchedulingSnapshot,
    UnassignedProposal,
)


class ScheduleInvariantError(Exception):
    """Raised when proposed assignments violate mathematical or domain invariants."""


class SlotChefScheduler:
    """Core CP-SAT constraint programming scheduler."""

    def __init__(self, time_limit_seconds: float = 5.0) -> None:
        self.time_limit_seconds = max(0.5, float(time_limit_seconds))

    def solve(self, snapshot: SchedulingSnapshot) -> ScheduleResult:
        start_clock = time.perf_counter()

        # Step 1: Pre-solver eligibility filtering
        eligible_map, exclusions_map = filter_eligible_candidates(
            snapshot.cooks,
            snapshot.bookings,
            snapshot.service_date,
        )

        model = cp_model.CpModel()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_seconds

        # Decision variables
        start_vars: dict[str, cp_model.IntVar] = {}
        end_vars: dict[str, cp_model.IntVar] = {}
        unassigned_vars: dict[str, cp_model.BoolVar] = {}
        assign_vars: dict[tuple[str, str], cp_model.BoolVar] = {}

        # Objective tracking terms
        penalty_terms: list[cp_model.LinearExpr] = []
        lateness_vars: list[cp_model.IntVar] = []
        transition_terms: list[tuple[int, cp_model.BoolVar]] = []

        booking_dict: dict[str, BookingInput] = {b.id: b for b in snapshot.bookings}

        # Step 2: Create variables and window bounds per booking
        for b in snapshot.bookings:
            max_start = b.latest_finish_minute - b.duration_minutes
            s_var = model.new_int_var(b.earliest_start_minute, max_start, f"start_{b.id}")
            e_var = model.new_int_var(b.earliest_start_minute + b.duration_minutes, b.latest_finish_minute, f"end_{b.id}")
            model.add(e_var == s_var + b.duration_minutes)

            start_vars[b.id] = s_var
            end_vars[b.id] = e_var
            u_var = model.new_bool_var(f"unassigned_{b.id}")
            unassigned_vars[b.id] = u_var

            # Lateness penalty: deviation from preferred start
            pref_start = b.preferred_start_minute or b.earliest_start_minute
            dev = model.new_int_var(0, 1440, f"dev_{b.id}")
            diff = model.new_int_var(-1440, 1440, f"diff_{b.id}")
            model.add(diff == s_var - pref_start)
            model.add_abs_equality(dev, diff)
            lateness_vars.append(dev)

            # High penalty for leaving booking unassigned, weighted by priority
            penalty_unassigned = 50_000 * b.priority
            penalty_terms.append(penalty_unassigned * u_var)

            eligible_cooks = eligible_map.get(b.id, [])
            assign_for_b: list[cp_model.BoolVar] = []

            for c in eligible_cooks:
                a_var = model.new_bool_var(f"assign_{b.id}_{c.id}")
                assign_vars[(b.id, c.id)] = a_var
                assign_for_b.append(a_var)

                # Soft preference for requested cook
                if b.preferred_cook_id and b.preferred_cook_id == c.id:
                    penalty_terms.append(-1_000 * a_var)

                # Working windows containment
                if c.working_windows:
                    window_bools: list[cp_model.BoolVar] = []
                    for w_idx, win in enumerate(c.working_windows):
                        if (
                            win.end_minute - win.start_minute >= b.duration_minutes
                            and win.end_minute >= b.earliest_start_minute + b.duration_minutes
                            and win.start_minute <= max_start
                        ):
                            in_w = model.new_bool_var(f"win_{b.id}_{c.id}_{w_idx}")
                            model.add(s_var >= win.start_minute).only_enforce_if(in_w)
                            model.add(e_var <= win.end_minute).only_enforce_if(in_w)
                            window_bools.append(in_w)

                    if window_bools:
                        model.add(sum(window_bools) >= a_var)
                    else:
                        model.add(a_var == 0)

                # Protected breaks avoidance
                for brk_idx, brk in enumerate(c.breaks):
                    before_brk = model.new_bool_var(f"bbrk_{b.id}_{c.id}_{brk_idx}")
                    model.add(e_var <= brk.start_minute).only_enforce_if([a_var, before_brk])
                    model.add(s_var >= brk.end_minute).only_enforce_if([a_var, ~before_brk])

                # Existing committed assignments avoidance
                for comm_idx, (c_start, c_end) in enumerate(c.existing_commitments):
                    before_comm = model.new_bool_var(f"bcomm_{b.id}_{c.id}_{comm_idx}")
                    buf = c.default_buffer_minutes
                    model.add(e_var + buf <= c_start).only_enforce_if([a_var, before_comm])
                    model.add(s_var >= c_end + buf).only_enforce_if([a_var, ~before_comm])

            # Exact assignment constraint: assigned to at most 1 eligible cook, or unassigned
            model.add(sum(assign_for_b) + u_var == 1)

        # Step 3: Cook daily capacity constraints
        for c in snapshot.cooks:
            eligible_b_ids = [b.id for b in snapshot.bookings if (b.id, c.id) in assign_vars]
            if not eligible_b_ids:
                continue

            # Visit count limit
            existing_visits = len(c.existing_commitments)
            remaining_visits = max(0, c.max_daily_visits - existing_visits)
            model.add(sum(assign_vars[(b_id, c.id)] for b_id in eligible_b_ids) <= remaining_visits)

            # Daily minutes limit
            existing_mins = sum(end - start for start, end in c.existing_commitments)
            remaining_mins = max(0, c.max_daily_minutes - existing_mins)
            cooking_time_expr = sum(
                booking_dict[b_id].duration_minutes * assign_vars[(b_id, c.id)]
                for b_id in eligible_b_ids
            )
            model.add(cooking_time_expr <= remaining_mins)

        # Step 4: Pairwise non-overlap & transition constraint (Section 4.6)
        all_bookings = snapshot.bookings
        for c in snapshot.cooks:
            c_bookings = [b for b in all_bookings if (b.id, c.id) in assign_vars]
            for i_idx in range(len(c_bookings)):
                for j_idx in range(i_idx + 1, len(c_bookings)):
                    b_i = c_bookings[i_idx]
                    b_j = c_bookings[j_idx]

                    both_assigned = model.new_bool_var(f"both_{b_i.id}_{b_j.id}_{c.id}")
                    model.add_bool_and(
                        [assign_vars[(b_i.id, c.id)], assign_vars[(b_j.id, c.id)]]
                    ).only_enforce_if(both_assigned)
                    model.add_bool_or(
                        [~assign_vars[(b_i.id, c.id)], ~assign_vars[(b_j.id, c.id)]]
                    ).only_enforce_if(~both_assigned)

                    before_ij = model.new_bool_var(f"ord_{b_i.id}_{b_j.id}_{c.id}")
                    before_ji = model.new_bool_var(f"ord_{b_j.id}_{b_i.id}_{c.id}")

                    model.add(before_ij + before_ji == 1).only_enforce_if(both_assigned)
                    model.add(before_ij == 0).only_enforce_if(~both_assigned)
                    model.add(before_ji == 0).only_enforce_if(~both_assigned)

                    t_ij = snapshot.get_transition_minutes(b_i.location_id, b_j.location_id)
                    t_ji = snapshot.get_transition_minutes(b_j.location_id, b_i.location_id)

                    model.add(end_vars[b_i.id] + t_ij <= start_vars[b_j.id]).only_enforce_if(before_ij)
                    model.add(end_vars[b_j.id] + t_ji <= start_vars[b_i.id]).only_enforce_if(before_ji)

                    transition_terms.append((t_ij, before_ij))
                    transition_terms.append((t_ji, before_ji))

        # Step 5: Compose balanced objective function
        for dev in lateness_vars:
            penalty_terms.append(2 * dev)

        for t_min, bool_var in transition_terms:
            penalty_terms.append(10 * t_min * bool_var)

        model.minimize(sum(penalty_terms))

        # Step 6: Solve
        status_raw = solver.solve(model)
        elapsed_ms = int((time.perf_counter() - start_clock) * 1000)

        # Step 7: Parse solver status
        if status_raw == cp_model.OPTIMAL:
            status = SolverStatus.OPTIMAL
        elif status_raw == cp_model.FEASIBLE:
            status = SolverStatus.FEASIBLE
        elif status_raw == cp_model.INFEASIBLE:
            status = SolverStatus.INFEASIBLE
        elif status_raw == cp_model.MODEL_INVALID:
            status = SolverStatus.MODEL_INVALID
        else:
            status = SolverStatus.UNKNOWN

        # Step 8: Build result proposals
        assignments: list[AssignmentProposal] = []
        unassigned_proposals: list[UnassignedProposal] = []

        if status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            for b in snapshot.bookings:
                if solver.value(unassigned_vars[b.id]):
                    primary_code = self._determine_unassigned_primary_reason(
                        b,
                        exclusions_map.get(b.id, {}),
                        len(snapshot.cooks),
                    )
                    unassigned_proposals.append(
                        UnassignedProposal(
                            booking_id=b.id,
                            primary_reason=primary_code,
                            reason_details="No eligible cook could accommodate the requested time window and buffer.",
                            candidate_cook_exclusions=exclusions_map.get(b.id, {}),
                        )
                    )
                else:
                    assigned_cook_id = ""
                    for c in snapshot.cooks:
                        if (b.id, c.id) in assign_vars and solver.value(assign_vars[(b.id, c.id)]):
                            assigned_cook_id = c.id
                            break

                    start_m = int(solver.value(start_vars[b.id]))
                    end_m = int(solver.value(end_vars[b.id]))
                    assignments.append(
                        AssignmentProposal(
                            booking_id=b.id,
                            cook_id=assigned_cook_id,
                            start_minute=start_m,
                            end_minute=end_m,
                            duration_minutes=b.duration_minutes,
                        )
                    )

            # Step 9: Invariant verification
            self.validate_invariants(assignments, snapshot)

        else:
            # All bookings remain unassigned when infeasible or unknown
            for b in snapshot.bookings:
                primary_code = self._determine_unassigned_primary_reason(
                    b,
                    exclusions_map.get(b.id, {}),
                    len(snapshot.cooks),
                )
                unassigned_proposals.append(
                    UnassignedProposal(
                        booking_id=b.id,
                        primary_reason=primary_code,
                        reason_details="Solver could not satisfy constraints within the time limit."
                        if status == SolverStatus.UNKNOWN
                        else "No feasible schedule satisfies all hard constraints.",
                        candidate_cook_exclusions=exclusions_map.get(b.id, {}),
                    )
                )

        obj_val = float(solver.objective_value) if status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE) else 0.0

        return ScheduleResult(
            status=status,
            solve_duration_ms=elapsed_ms,
            assignments=assignments,
            unassigned=unassigned_proposals,
            candidate_cook_count=len(snapshot.cooks),
            objective_value=obj_val,
            objective_components={
                "unassigned_count": len(unassigned_proposals),
                "assigned_count": len(assignments),
                "total_penalty": obj_val,
            },
            reason_summary=f"Solved with status {status.value} in {elapsed_ms}ms.",
            metadata={
                "snapshot_version": snapshot.snapshot_version,
                "society_id": snapshot.society_id,
            },
        )

    def validate_invariants(
        self,
        assignments: list[AssignmentProposal],
        snapshot: SchedulingSnapshot,
    ) -> None:
        """Pure Python verification of all hard constraints against the proposed schedule."""
        booking_map = {b.id: b for b in snapshot.bookings}
        cook_map = {c.id: c for c in snapshot.cooks}
        assignments_by_cook: dict[str, list[AssignmentProposal]] = {}

        for a in assignments:
            b = booking_map.get(a.booking_id)
            c = cook_map.get(a.cook_id)
            if not b or not c:
                raise ScheduleInvariantError(f"Assignment references invalid booking/cook: {a}")

            # 1. Duration invariant
            if a.end_minute != a.start_minute + b.duration_minutes:
                raise ScheduleInvariantError(
                    f"Booking {b.id} duration mismatch: {a.end_minute - a.start_minute} != {b.duration_minutes}"
                )

            # 2. Time window validity
            if a.start_minute < b.earliest_start_minute or a.end_minute > b.latest_finish_minute:
                raise ScheduleInvariantError(
                    f"Booking {b.id} placed at [{a.start_minute}, {a.end_minute}], outside allowed window [{b.earliest_start_minute}, {b.latest_finish_minute}]"
                )

            # 3. Cook eligibility & skills
            if not b.required_skills.issubset(c.skills):
                raise ScheduleInvariantError(f"Cook {c.id} lacks skills required for booking {b.id}")

            # 4. Cook working windows containment
            if c.working_windows:
                contained = any(
                    w.start_minute <= a.start_minute and a.end_minute <= w.end_minute
                    for w in c.working_windows
                )
                if not contained:
                    raise ScheduleInvariantError(f"Booking {b.id} placed outside working windows of cook {c.id}")

            # 5. Protected breaks
            for brk in c.breaks:
                overlap = max(a.start_minute, brk.start_minute) < min(a.end_minute, brk.end_minute)
                if overlap:
                    raise ScheduleInvariantError(f"Booking {b.id} overlaps protected break {brk} of cook {c.id}")

            assignments_by_cook.setdefault(a.cook_id, []).append(a)

        # 6. Cook capacity & non-overlap with transitions
        for cook_id, cook_assignments in assignments_by_cook.items():
            cook = cook_map[cook_id]
            if len(cook_assignments) + len(cook.existing_commitments) > cook.max_daily_visits:
                raise ScheduleInvariantError(f"Cook {cook_id} daily visits exceed limit {cook.max_daily_visits}")

            total_mins = sum(a.duration_minutes for a in cook_assignments)
            existing_mins = sum(end - start for start, end in cook.existing_commitments)
            if total_mins + existing_mins > cook.max_daily_minutes:
                raise ScheduleInvariantError(f"Cook {cook_id} daily minutes exceed limit {cook.max_daily_minutes}")

            # Sort by start minute
            sorted_assignments = sorted(cook_assignments, key=lambda x: x.start_minute)
            for i in range(len(sorted_assignments) - 1):
                cur = sorted_assignments[i]
                nxt = sorted_assignments[i + 1]
                cur_b = booking_map[cur.booking_id]
                nxt_b = booking_map[nxt.booking_id]
                trans = snapshot.get_transition_minutes(cur_b.location_id, nxt_b.location_id)

                if cur.end_minute + trans > nxt.start_minute:
                    raise ScheduleInvariantError(
                        f"Overlap/transition violation on cook {cook_id}: "
                        f"Booking {cur.booking_id} ends at {cur.end_minute} + {trans}m buffer > start {nxt.start_minute} of booking {nxt.booking_id}"
                    )

    @staticmethod
    def _determine_unassigned_primary_reason(
        booking: BookingInput,
        cook_exclusions: dict[str, list[ReasonCode]],
        total_candidate_cooks: int,
    ) -> ReasonCode:
        if total_candidate_cooks == 0:
            return ReasonCode.NO_FEASIBLE_COOK

        if not cook_exclusions:
            # All candidate cooks were eligible, unassigned due to time window conflict
            return ReasonCode.TIME_WINDOW_CONFLICT

        if len(cook_exclusions) == total_candidate_cooks:
            all_reasons: list[ReasonCode] = []
            for codes in cook_exclusions.values():
                all_reasons.extend(codes)

            for priority_code in [
                ReasonCode.NO_SKILL_MATCH,
                ReasonCode.COOK_ON_LEAVE,
                ReasonCode.OUTSIDE_WORKING_HOURS,
                ReasonCode.DAILY_CAPACITY_REACHED,
                ReasonCode.SOCIETY_MISMATCH,
            ]:
                if all_reasons.count(priority_code) == len(cook_exclusions):
                    return priority_code

            return ReasonCode.NO_FEASIBLE_COOK

        return ReasonCode.TIME_WINDOW_CONFLICT

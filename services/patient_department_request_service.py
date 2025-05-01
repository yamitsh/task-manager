from collections import defaultdict
from models.patient_task import PatientTask
from models.patient_request import PatientRequest
from .abstract_patient_request_service import PatientRequestService
from typing import NewType
from tinydb import where
import db.db_tinydb as db

DepartmentToPatientTasks = NewType(
    'DepartmentToPatientTasks', dict[str, list[PatientTask]])

PatientToGroupedDepartmentTasks = dict[str, DepartmentToPatientTasks]


class DepartmentPatientRequestService(PatientRequestService):

    def get_task(self, task_id) -> PatientTask | None:
        # TODO: gather all db methods to db_utils.py, to control all DB accesses in one place
        result_dict = db.tasks.get(where('id') == task_id)
        if not result_dict:
            return None

        return PatientTask(**result_dict)

    def get_open_patient_requests(self, patient_id) -> list[dict] | None:
        return db.patient_requests.search(
            (where('patient_id') == patient_id) & (where('status') == 'Open'))

    def get_open_patient_department_request(self, patient_id, assigned_to) -> PatientRequest | None:
        result_dict = db.patient_requests.get(
            (where('patient_id') == patient_id) & (where('assigned_to') == assigned_to) & (where('status') == 'Open'))

        if not result_dict:
            return None

        return PatientRequest(**result_dict)

    def update_existing_open_requests(self, patient_ids: set[str]):
        # remove irrelevant tasks from open PatientRequests

        for patient_id in patient_ids:
            open_requests = self.get_open_patient_requests(patient_id)

            for open_req in open_requests:
                # get tasks objects
                req_tasks = [self.get_task(t_id) for t_id in open_req.get('task_ids')]
                # keep relevant tasks by department
                relevant_tasks = [t for t in req_tasks if t.assigned_to == open_req.get('assigned_to')]
                # change the status of existing PatientRequest
                open_tasks = [t for t in relevant_tasks if t.status == 'Open']
                open_req['status'] = 'Open' if len(open_tasks) > 0 else 'Closed'
                # save to DB
                db.patient_requests.update(
                    open_req, where('id') == open_req.get('id'))

    def update_requests(self, tasks: list[PatientTask]):
        # create a dictionary with patient id and department as key, and tasks list as value
        grouped_by_pat_dep: dict[tuple, list[PatientTask]] = defaultdict(list)

        for task in tasks:
            grouped_by_pat_dep[(task.patient_id, task.assigned_to)].append(task)

        # get or create patient request
        for (patient_id, assigned_to), patient_tasks in grouped_by_pat_dep.items():
            existing_req: PatientRequest = self.get_open_patient_department_request(patient_id, assigned_to)
            pat_req = self.to_patient_request(patient_id, patient_tasks, is_split_by_department=True)

            if not existing_req:
                db.patient_requests.insert(pat_req.model_dump())
            else:
                pat_req.id = existing_req.id
                db.patient_requests.update(
                    pat_req.model_dump(), where('id') == existing_req.id)

        patient_ids = set([task.patient_id for task in tasks])
        self.update_existing_open_requests(patient_ids)

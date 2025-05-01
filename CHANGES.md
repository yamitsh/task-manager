# CHANGES.md

## Enhancements

* **Implemented Grouping of Patient Requests by Department:** The system now supports grouping `PatientRequest` objects not only by `patient_id` (the existing functionality) but also by the `assigned_to` field present in the associated `PatientTask` objects.

## Implementation Details

* **No New Database Table Creation:** Initially, I considered creating a new database table to handle the department-based grouping. However, after analyzing the data structure, I determined that no new fields needed to be added or removed from the existing `PatientRequest` model. Therefore, the existing `patient_requests` table continues to be used.

* **'is\_split\_by\_department' Field:** To facilitate analysis and differentiate `PatientRequest` objects created after this enhancement, a new boolean field named `'is_split_by_department'` has been added to the `PatientRequest` model. This field will be set to `True` for requests created or updated as part of the new department grouping logic.

* **Modified 'services/patient\_department\_request\_service.py':** The code within this service has been updated to implement the dual grouping logic. It now creates or updates `PatientRequest` objects based on a combined key of `patient_id` and `assigned_to`. This mirrors the previous logic which grouped solely by `patient_id`. The value associated with this combined key is a list of relevant `PatientTask` objects.

* **Removal of Irrelevant Tasks:** A process has been implemented to ensure data consistency. After a `PatientTask`'s department is changed, the system iterates through all relevant open `PatientRequest` objects that might contain this task. Tasks that no longer belong to the request's grouping criteria (based on the request's `patient_id` and `assigned_to`) are removed from the request's `task_ids` set.

* **Performance Optimization for Task Removal:** To optimize the removal of irrelevant tasks, instead of retrieving the associated `PatientRequest` for each individual task whose department changed (which could lead to multiple database queries per request if a request had many tasks), a set of unique `patient_id`s of the affected tasks is created first. This set is then used to retrieve only the relevant `PatientRequest` objects, significantly reducing the number of database queries required for this cleanup process.
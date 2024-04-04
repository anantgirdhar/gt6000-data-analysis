import csv
import sys
from pathlib import Path


def clean_prepost(prepost_filename, cleaned_filename):
    RENAME_FIELDS = {
        "StartDate": "Submission Start",
        "EndDate": "Submission End",
        "Progress": "Progress",
        "Finished": "Finished",
        "RecipientLastName": "Last Name",
        "RecipientFirstName": "First Name",
        "RecipientEmail": "Email",
    }
    REMOVE_TEXT_FIELDS = True
    if (Path() / cleaned_filename).is_file():
        raise FileExistsError(
            f"{cleaned_filename} already exists. Back it up or delete it."
        )
    with (
        open(prepost_filename, "r") as prepost_file,
        open(cleaned_filename, "w") as cleaned_file,
    ):
        csvreader = csv.reader(prepost_file)
        csvwriter = csv.writer(cleaned_file)
        header = next(csvreader)
        cleaned_header = []
        field_indices_to_keep = []
        for i, field in enumerate(header):
            if field in RENAME_FIELDS:
                cleaned_header.append(RENAME_FIELDS[field])
                field_indices_to_keep.append(i)
            elif field.startswith("Q"):
                if field.endswith("_TEXT"):
                    continue
                cleaned_header.append(field)
                field_indices_to_keep.append(i)
            else:
                continue
        # Verify that all of RENAME_FIELDS have been found
        for field in RENAME_FIELDS.values():
            if field not in cleaned_header:
                raise KeyError(f"{field} not found in the cleaned header")
        csvwriter.writerow(cleaned_header)
        # Skip the next two rows containing prompts and qualtrics metadata
        next(csvreader)
        next(csvreader)
        for row in csvreader:
            extracted_values = [
                v for i, v in enumerate(row) if i in field_indices_to_keep
            ]
            csvwriter.writerow(extracted_values)


def _extract_gradebook_header_information(header_row):
    RENAME_STUDENT_INFO = {
        "Student": "Full Name",
        "SIS Login ID": "GT Account",
        "Section": "Section",
    }
    RENAME_DELIVERABLES = {
        "Deliverable 1": "D1",
        "Deliverable 2": "D2",
        "Deliverable 3": "D3",
        "Deliverable 4": "D4",
        "Deliverable 5": "D5",
    }
    RENAME_GROUP_MEETINGS = {
        "Group Meeting - Week 1 Attendance": "GM1",
        "Group Meeting - Week 2 Attendance": "GM2",
        "Group Meeting - Week 3 Attendance": "GM3",
        "Group Meeting - Week 4 Attendance": "GM4",
        "Group Meeting - Week 5 Attendance": "GM5",
        "Group Meeting - Week 6 Attendance": "GM6",
        "Group Meeting - Week 7 Attendance": "GM7",
        "Group Meeting - Week 8 Attendance": "GM8",
    }
    cleaned_header = []
    field_indices_to_keep = []
    # Since the modules and workshops have changed over the years, just
    # report the total for those two categories
    module_field_indices = {f"M{i}": [] for i in range(1, 9)}
    workshop_field_indices = []
    for i, field in enumerate(header_row):
        if field in RENAME_STUDENT_INFO:
            cleaned_header.append(RENAME_STUDENT_INFO[field])
            field_indices_to_keep.append(i)
        elif field.startswith("Deliverable"):
            for prefix, renamed_field in RENAME_DELIVERABLES.items():
                if field.startswith(prefix):
                    cleaned_header.append(renamed_field)
                    field_indices_to_keep.append(i)
        elif field.startswith("Group Meeting"):
            for prefix, renamed_field in RENAME_GROUP_MEETINGS.items():
                if field.startswith(prefix):
                    cleaned_header.append(renamed_field)
                    field_indices_to_keep.append(i)
        elif field.startswith("Extract Workshop"):
            workshop_field_indices.append(i)
            if "Workshops" not in cleaned_header:
                cleaned_header.append("Workshops")
        elif field[0] == "M" and field[1].isdigit():
            module_field_indices[f"M{field[1]}"].append(i)
        elif field.startswith("Pre-Course Assessment"):
            cleaned_header.append("PreSurvey")
            field_indices_to_keep.append(i)
        elif field.startswith("Post-Course Assessment"):
            cleaned_header.append("PostSurvey")
            field_indices_to_keep.append(i)
        else:
            continue
    # Tack on the headers for the combined fields
    cleaned_header.extend(sorted(module_field_indices.keys()))
    # Verify that all required fields have been found
    for field in RENAME_STUDENT_INFO.values():
        assert field in cleaned_header
    for field in RENAME_DELIVERABLES.values():
        assert field in cleaned_header
    for field in RENAME_GROUP_MEETINGS.values():
        assert field in cleaned_header
    for field in module_field_indices.keys():
        assert field in cleaned_header
    assert "Workshops" in cleaned_header
    return (
        cleaned_header,
        field_indices_to_keep,
        module_field_indices,
        workshop_field_indices,
    )


def _clean_gradebook_row(
    row,
    field_indices_to_keep,
    module_field_indices,
    workshop_field_indices,
):
    extracted_values = [
        v for i, v in enumerate(row) if i in field_indices_to_keep
    ]
    for module in sorted(module_field_indices.keys()):
        module_points = [
            float(row[i]) if row[i] else 0
            for i in module_field_indices[module]
        ]
        extracted_values.append(str(sum(module_points)))
    workshop_points = [
        float(row[i]) if row[i] else 0 for i in workshop_field_indices
    ]
    extracted_values.append(str(sum(workshop_points)))
    return extracted_values


def clean_gradebook(filename, cleaned_filename):
    # if (Path() / cleaned_filename).is_file():
    #     raise FileExistsError(
    #         f"{cleaned_filename} already exists. Back it up or delete it."
    #     )
    with (
        open(filename, "r") as gradebook,
        open(cleaned_filename, "w") as cleaned_file,
    ):
        csvreader = csv.reader(gradebook)
        csvwriter = csv.writer(cleaned_file)
        header = next(csvreader)
        (
            cleaned_header,
            field_indices_to_keep,
            module_field_indices,
            workshop_field_indices,
        ) = _extract_gradebook_header_information(header)
        csvwriter.writerow(cleaned_header)
        # Skip the next row containing points possible
        next(csvreader)
        for row in csvreader:
            csvwriter.writerow(
                _clean_gradebook_row(
                    row,
                    field_indices_to_keep,
                    module_field_indices,
                    workshop_field_indices,
                )
            )


if __name__ == "__main__":
    # clean_prepost(sys.argv[1], sys.argv[2])
    clean_gradebook(sys.argv[1], sys.argv[2])

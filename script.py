import json

json_file = "../product_management/fixtures/product_management.json"

with open(json_file, "r") as file:
    initiatives_to_update = json.load(file)

# ====================Challenge======================
updated_initiatives = []
for data in initiatives_to_update:
    fields = data["fields"]

    if data["model"] == "product_management.initiative":
        status = fields["status"]
        new_status3 = ""
        if status == 1:
            new_status3 = "Active"
        elif status == 2:
            new_status3 = "Completed"
        elif status == 3:
            new_status3 = "Draft"
        elif status == 4:
            new_status3 = "Cancelled"

        if new_status3:
            data["fields"]["status"] = new_status3
            updated_initiatives.append(data)

    elif data["model"] == "product_management.challenge":
        status = fields["status"]
        new_status1 = ""
        if status == 0:
            new_status1 = "Draft"
        elif status == 1:
            new_status1 = "Blocked"
        elif status == 2:
            new_status1 = "Active"
        elif status == 4:
            new_status1 = "Completed"

        if new_status1:
            data["fields"]["status"] = new_status1
            updated_initiatives.append(data)

    elif data["model"] == "product_management.bounty":
        status = fields["status"]
        new_status2 = ""
        if status == 2:
            new_status2 = "Available"
        elif status == 3:
            new_status2 = "Claimed"
        elif status == 4:
            new_status2 = "Completed"
        elif status == 5:
            new_status2 = "In Review"

        if new_status2:
            data["fields"]["status"] = new_status2
            updated_initiatives.append(data)

    else:
        updated_initiatives.append(data)


with open(json_file, "w") as file:
    json.dump(updated_initiatives, file, indent=4)

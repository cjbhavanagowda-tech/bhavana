
import json
import os
from datetime import datetime

DATA_FILE = "hospital.json"


class HospitalSystem:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.data = {"patients": {}, "doctors": {}, "appointments": [], "bills": []}
        self.load()

    
    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename) as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                print("Data file corrupted. Starting fresh.")

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.data, f, indent=4)

    
    def add_patient(self, pid, name, age, gender, disease):
        if pid in self.data["patients"]:
            print("Patient ID already exists.")
            return
        self.data["patients"][pid] = {"name": name, "age": age, "gender": gender,
                                      "disease": disease, "history": []}
        self.save()
        print("Patient registered.")

    def view_patients(self):
        if not self.data["patients"]:
            print("No patients.")
        for pid, p in self.data["patients"].items():
            print(f"{pid:<8}{p['name']:<18}{p['age']:<5}{p['gender']:<8}{p['disease']}")

    def patient_record(self, pid):
        p = self.data["patients"].get(pid)
        if not p:
            print("Patient not found.")
            return
        print(f"\n--- Record of {p['name']} ({pid}) ---")
        print(f"Age: {p['age']}  Gender: {p['gender']}  Condition: {p['disease']}")
        print("History:")
        for h in p["history"] or ["(none)"]:
            print("  -", h)
        bills = [b for b in self.data["bills"] if b["patient_id"] == pid]
        print("Bills:", ", ".join(f"#{b['bill_id']} Rs.{b['total']} ({b['status']})" for b in bills) or "(none)")

    
    def add_doctor(self, did, name, speciality, fee):
        if did in self.data["doctors"]:
            print("Doctor ID already exists.")
            return
        self.data["doctors"][did] = {"name": name, "speciality": speciality, "fee": fee}
        self.save()
        print("Doctor added.")

    def view_doctors(self):
        if not self.data["doctors"]:
            print("No doctors.")
        for did, d in self.data["doctors"].items():
            print(f"{did:<8}Dr. {d['name']:<16}{d['speciality']:<16}Fee: Rs.{d['fee']}")

    
    def book_appointment(self, pid, did, date, time):
        if pid not in self.data["patients"] or did not in self.data["doctors"]:
            print("Invalid patient or doctor ID.")
            return
        for a in self.data["appointments"]:
            if a["doctor_id"] == did and a["date"] == date and a["time"] == time and a["status"] == "Booked":
                print("Doctor already booked at that slot.")
                return
        appt_id = len(self.data["appointments"]) + 1
        self.data["appointments"].append({"id": appt_id, "patient_id": pid, "doctor_id": did,
                                          "date": date, "time": time, "status": "Booked"})
        self.save()
        print(f"Appointment #{appt_id} booked.")

    def view_appointments(self):
        if not self.data["appointments"]:
            print("No appointments.")
        for a in self.data["appointments"]:
            p = self.data["patients"].get(a["patient_id"], {}).get("name", "?")
            d = self.data["doctors"].get(a["doctor_id"], {}).get("name", "?")
            print(f"#{a['id']} {a['date']} {a['time']}  {p} -> Dr. {d}  [{a['status']}]")

    def complete_appointment(self, appt_id, notes):
        for a in self.data["appointments"]:
            if a["id"] == appt_id and a["status"] == "Booked":
                a["status"] = "Completed"
                self.data["patients"][a["patient_id"]]["history"].append(
                    f"{a['date']}: seen by Dr. {self.data['doctors'][a['doctor_id']]['name']} - {notes}")
                self.save()
                print("Appointment completed and added to patient history.")
                return a
        print("Booked appointment not found.")

    
    def generate_bill(self, appt_id, medicine_cost=0.0):
        appt = next((a for a in self.data["appointments"] if a["id"] == appt_id), None)
        if not appt or appt["status"] != "Completed":
            print("Complete the appointment before billing.")
            return
        fee = self.data["doctors"][appt["doctor_id"]]["fee"]
        total = fee + medicine_cost
        bill = {"bill_id": len(self.data["bills"]) + 1, "patient_id": appt["patient_id"],
                "appointment_id": appt_id, "consultation": fee, "medicine": medicine_cost,
                "total": total, "status": "Unpaid",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")}
        self.data["bills"].append(bill)
        self.save()
        p = self.data["patients"][appt["patient_id"]]["name"]
        print(f"\n===== BILL #{bill['bill_id']} =====\nPatient      : {p}")
        print(f"Consultation : Rs.{fee}\nMedicines    : Rs.{medicine_cost}\nTOTAL        : Rs.{total}\n")

    def pay_bill(self, bill_id):
        for b in self.data["bills"]:
            if b["bill_id"] == bill_id:
                b["status"] = "Paid"
                self.save()
                print("Payment recorded.")
                return
        print("Bill not found.")


def num(prompt, cast=float):
    while True:
        try:
            v = cast(input(prompt))
            if v >= 0:
                return v
        except ValueError:
            pass
        print("Enter a valid non-negative number.")


def main():
    h = HospitalSystem()
    menu = """
===== HOSPITAL MANAGEMENT SYSTEM =====
1. Register patient     2. View patients      3. Patient record
4. Add doctor           5. View doctors
6. Book appointment     7. View appointments  8. Complete appointment
9. Generate bill       10. Pay bill          11. Exit"""
    while True:
        print(menu)
        c = input("Choice: ").strip()
        if c == "1":
            h.add_patient(input("Patient ID: ").strip(), input("Name: ").strip(),
                          num("Age: ", int), input("Gender: ").strip(), input("Condition: ").strip())
        elif c == "2": h.view_patients()
        elif c == "3": h.patient_record(input("Patient ID: ").strip())
        elif c == "4":
            h.add_doctor(input("Doctor ID: ").strip(), input("Name: ").strip(),
                         input("Speciality: ").strip(), num("Consultation fee: "))
        elif c == "5": h.view_doctors()
        elif c == "6":
            h.book_appointment(input("Patient ID: ").strip(), input("Doctor ID: ").strip(),
                               input("Date (YYYY-MM-DD): ").strip(), input("Time (HH:MM): ").strip())
        elif c == "7": h.view_appointments()
        elif c == "8": h.complete_appointment(num("Appointment ID: ", int), input("Notes: ").strip())
        elif c == "9": h.generate_bill(num("Appointment ID: ", int), num("Medicine cost: "))
        elif c == "10": h.pay_bill(num("Bill ID: ", int))
        elif c == "11":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()

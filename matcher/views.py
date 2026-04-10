from django.shortcuts import render
from .forms import UploadCSVForm
from django.shortcuts import redirect
import csv

def home(request):
    return render(request, 'matcher/home.html', {
        "studentFileName": request.session.get("studentFileName", ""),
        "employerFileName": request.session.get("employerFileName", "")
    })
    
def upload_student_csv(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]

            if not file.name.endswith(".csv"):
                return render(request, 'matcher/home.html', {
                    "form": form,
                    "error": "The file must be a .csv file.",
                    "studentFileName": request.session.get("studentFileName", ""),
                    "employerFileName": request.session.get("employerFileName", "")
                })
            request.session["studentData"] = parse_csv_file(file)
            request.session["studentFileName"] = file.name
            return redirect("home")
    return redirect("home")
        
def upload_employer_csv(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES["file"]

            if not file.name.endswith(".csv"):
                return render(request, 'matcher/home.html', {
                    "form": form,
                    "error": "The files must be .csv files.",
                    "studentFileName": request.session.get("studentFileName", ""),
                    "employerFileName": request.session.get("employerFileName", "")
                })
            request.session["employerData"] = parse_csv_file(file)
            request.session["employerFileName"] = file.name
            return redirect("home")
    return redirect("home")


def make_matches(students, employers):

    matches = {}

    matchedStudents = []
    unmatchedStudents = []
    tryAgainStudents = []

    # Make an initial placement for all students a single time.
    for student in students:
        matchedStudents.append(student)
        for employer in students[student]:
            if employer not in matches:
                matches[employer] = []

            # See if the student is on the employer’s list.
            if student in employers[employer]:
                
            # Case where there is still room to add the student, regardless of ranking.
                if len(matches[employer]) < int(employers[employer][0]):
                    matches[employer].append(student)
                    break
                
                # Case where the company is already at max capacity
                else:
                    lowestStudent = 0
                    for matchedStudent in matches[employer]:
                        currStudent = employers[employer].index(matchedStudent)
    
                        if currStudent > lowestStudent:
                            lowestStudent = currStudent
                    
                    # Case where current student is preferred over another student.
                    if employers[employer].index(student) < lowestStudent:
                        tryAgainStudents.append(employers[employer][lowestStudent])
                        matches[employer].remove(employers[employer][lowestStudent])
                        matches[employer].append(student)
                        break
                
    # Try to place all displaced students, otherwise move them to the unmatched students list.
    while len(tryAgainStudents) > 0:
        currStudent = tryAgainStudents[0]
        for employer in students[currStudent]:

            # See if the student is on the employer’s list.
            if currStudent in employers[employer]:
                
                # Case where there is still room to add the student, regardless of ranking.
                if len(matches[employer]) < int(employers[employer][0]):
                    matches[employer].append(currStudent)
                    tryAgainStudents.pop(0)
                    break
                
                # Case where the company is already at max capacity
                else:
                    lowestStudent = 0
                    for matchedStudent in matches[employer]:
                        iCurrStudent = employers[employer].index(matchedStudent)
                        if iCurrStudent > lowestStudent:
                            lowestStudent = iCurrStudent

                    # Case where current student is preferred over another student.
                    if employers[employer].index(currStudent) < lowestStudent:
                        tryAgainStudents.append(employers[employer][lowestStudent])
                        tryAgainStudents.pop(0)
                        matches[employer].remove(employers[employer][lowestStudent])
                        matches[employer].append(currStudent)
                        break
        
        # If the try again student wasn't placed by this point, then there is no match for them.
        if currStudent in tryAgainStudents:
            matchedStudents.remove(currStudent)
            tryAgainStudents.pop(tryAgainStudents.index(currStudent))

    all_students = set(students.keys())
    matched_students = set()

    for employer in matches:
        for student in matches[employer]:
            matched_students.add(student)

    unmatchedStudents = list(all_students - matched_students)

    matches = {
    employer: students
    for employer, students in matches.items()
    if students
}

    return matches, unmatchedStudents

def make_potential_matches(matches, employer_dict, unmatched_students):
    potential_matches = {}
    unmatched_set = set(unmatched_students)
    unmatched_companies = []

    for employer in employer_dict:
        capacity = int(employer_dict[employer][0])
        current_matches = matches.get(employer, [])

        if capacity > len(current_matches):
            valid_students = [
                student for student in employer_dict[employer][1:]
                if student in unmatched_set
            ]

            if valid_students:
                potential_matches[employer] = valid_students
        if not matches.get(employer):
            unmatched_companies.append(employer)

    for students in potential_matches.values():
        for student in students:
            unmatched_set.discard(student)

    for company in potential_matches:
        capacity = int(employer_dict[company][0])
        current = len(matches.get(company, []))
        potential_matches[company] = {
            "students": potential_matches[company],
            "open_spots": capacity - current
        }
    

    return potential_matches, unmatched_set, unmatched_companies

def parse_csv_file(file):
    decoded = file.read().decode('utf-8').splitlines()
    reader = csv.reader(decoded)
    next(reader)

    parsedData = {}
    for row in reader:
        parsedData[row[1]] = row[2:]

    return parsedData

def generate_report(request):
    employer_file = request.session.get("employerData")
    student_file = request.session.get("studentData")

    if not employer_file or not student_file:
        return render(request, "matcher/home.html", {
            "error": "Please upload both files.",
            "studentFileName": request.session.get("studentFileName", ""),
            "employerFileName": request.session.get("employerFileName", "")
        })
    
    matches, unmatched_students = make_matches(student_file, employer_file)

    potential_matches, unmatched_students_potential, unmatched_companies = make_potential_matches(matches, employer_file, unmatched_students)

    return render(request, "matcher/report.html", {
        "matches": matches,
        "potential_matches": potential_matches,
        "unmatched_students": unmatched_students_potential,
        "unmatched_companies": unmatched_companies,
        "employers": employer_file
    })

def clear_student_file(request):
    del request.session["studentFileName"]
    del request.session["studentData"]
    return redirect("home")

def clear_employer_file(request):
    del request.session["employerFileName"]
    del request.session["employerData"]
    return redirect("home")